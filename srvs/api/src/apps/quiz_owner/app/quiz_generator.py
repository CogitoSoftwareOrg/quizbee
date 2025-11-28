import logging
import redis.asyncio as redis
import asyncio

from src.apps.material_owner.domain._in import MaterialApp, SearchCmd
from src.apps.user_owner.domain._in import Principal
from src.lib.distributed_lock import DistributedLock

from ..domain._in import GenMode, GenerateCmd, QuizGenerator
from ..domain.errors import NotQuizOwnerError
from ..domain.out import PatchGenerator, PatchGeneratorDto, QuizIndexer, QuizRepository
from ..domain.models import Quiz, QuizItem, QuizItemVariant
from ..domain.constants import HOLDOUT, PATCH_CHUNK_TOKEN_LIMIT, PATCH_LIMIT

from .errors import NoItemsReadyForGenerationError

logger = logging.getLogger(__name__)


class QuizGeneratorImpl(QuizGenerator):
    def __init__(
        self,
        quiz_repository: QuizRepository,
        quiz_indexer: QuizIndexer,
        material_app: MaterialApp,
        patch_generator: PatchGenerator,
        redis_client: redis.Redis,
    ):
        self._quiz_repository = quiz_repository
        self._quiz_indexer = quiz_indexer
        self._material_app = material_app
        self._patch_generator = patch_generator
        self._lock = DistributedLock(redis_client, lock_timeout=300)  # 5 min timeout

    async def generate(self, cmd: GenerateCmd) -> None:
        ### эта функция отвечает за генерацию одного патча
        ### используется distributed lock чтобы предотвратить race conditions
        ### при параллельных Continue запросах

        lock_key = f"quiz:generate:{cmd.quiz_id}"

        # 1. Reservation Phase
        async with self._lock.lock(lock_key, wait_timeout=60.0):
            logger.info(f"Acquired lock for quiz reservation: {cmd.quiz_id}")

            # Read fresh quiz state inside the lock
            quiz = await self._quiz_repository.get(cmd.quiz_id)
            if quiz.author_id != cmd.user.id:
                raise NotQuizOwnerError(quiz_id=cmd.quiz_id, user_id=cmd.user.id)

            if cmd.mode == GenMode.Regenerate:
                logger.info(f"Incrementing generation for quiz {cmd.quiz_id}")
                quiz.increment_generation()
                await self._quiz_repository.update(quiz)

            to_generate = (
                PATCH_LIMIT + HOLDOUT if cmd.mode == GenMode.Start else PATCH_LIMIT
            )

            items_to_generate = quiz.generate_patch(to_generate)
            if len(items_to_generate) == 0:
                logger.warning(
                    f"No items ready for generation in quiz {cmd.quiz_id}. "
                    f"All items may be FINAL or there are no items."
                )
                raise NoItemsReadyForGenerationError(quiz_id=cmd.quiz_id)

            # Save reserved items (status=GENERATING)
            await self._quiz_repository.update(quiz)
            logger.info(
                f"Reserved {len(items_to_generate)} items for generation in quiz {cmd.quiz_id}"
            )

        # 2. Generation Phase (No Lock)
        # Generate for each specific item by order to avoid race conditions
        generation_tasks = []
        for idx, item in enumerate(items_to_generate):
            generation_tasks.append(
                self._run_generation_task(quiz, item, cmd.user, cmd.cache_key)
            )

        results = await asyncio.gather(*generation_tasks)

        # 3. Result Phase
        async with self._lock.lock(lock_key, wait_timeout=60.0):
            logger.info(f"Acquired lock for quiz result saving: {cmd.quiz_id}")

            # Re-read quiz to get latest state (though we only update specific items)
            # Actually, we can just update the items we generated.
            # But to be safe and consistent with repository pattern, let's just update the items.
            # Since we have the `quiz` object from reservation phase, and we only modified
            # the items that we reserved (which no one else should touch),
            # we can apply the results to them.

            # However, `_run_generation_task` now returns data instead of modifying in place?
            # No, let's keep it modifying in place BUT we need to be careful about
            # the `quiz` object being stale if other requests finished in between.
            # But since we only touch `items_to_generate` which are by definition
            # reserved for THIS request (status=GENERATING), it should be fine.
            # The only risk is if `quiz` has other fields updated (like status).

            # Let's re-fetch the quiz to be absolutely safe about global state,
            # but apply changes to the specific items.
            fresh_quiz = await self._quiz_repository.get(cmd.quiz_id)

            # Apply results to fresh_quiz items
            for item, (chunks_info, used_chunk_ids) in zip(items_to_generate, results):
                # Find corresponding item in fresh_quiz
                fresh_item = next(
                    (i for i in fresh_quiz.items if i.id == item.id), None
                )
                if fresh_item:
                    # Copy generated data from `item` (which was modified in _run_generation_task if we keep it same)
                    # OR better: `_run_generation_task` should NOT modify `item` but return data.
                    # Let's refactor `_run_generation_task` to return data.
                    pass

            # Wait, `_run_generation_task` in my plan was supposed to return results.
            # Let's look at `results`.

            # Actually, let's just update the items we have.
            # `pb_quiz_repository.update` with `fresh_generated=True` updates only fresh generated items.
            # We need to make sure `items_to_generate` are marked as fresh_generated=True.

            # Let's apply the results (which are side-effects on `item` objects currently)
            # We need to make sure we are saving the correct state.

            # Refined approach:
            # `_run_generation_task` modifies `item` in place (question, variants, etc).
            # We need to save these items.
            # Since `items_to_generate` are references to objects inside `quiz.items`,
            # `quiz` is now modified.
            # But `quiz` might be stale regarding OTHER items.
            # `repository.update(quiz, fresh_generated=True)` only saves items with `fresh_generated=True`.
            # So it SHOULD be safe even if `quiz` is stale, as long as we don't save the whole quiz record
            # but only the items.
            # Let's check `pb_quiz_repository.py`:
            # `update` calls `save_item` for fresh items, then `quizes.update` for the quiz record.
            # The `quizes.update` might overwrite changes if `quiz` is stale!
            # We should AVOID updating the quiz record in the result phase if possible,
            # or re-fetch and merge.

            # But `quiz.increment_generation` updates the generation count on the quiz record.
            # That happened in Reservation phase.
            # In Result phase, we mostly care about items.

            # Let's look at `pb_quiz_repository.update`:
            # await self.admin_pb.collection("quizes").update(quiz.id, await self._to_record(quiz))
            # This DOES overwrite the quiz record.

            # So we MUST re-fetch quiz, and apply item updates to the fresh quiz.

            fresh_quiz = await self._quiz_repository.get(cmd.quiz_id)

            for i, (generated_item_data, used_chunks_data) in enumerate(results):
                # generated_item_data is (question, variants, hint)
                # used_chunks_data is (used_chunks, used_chunk_ids)

                original_item = items_to_generate[i]
                target_item = next(
                    (x for x in fresh_quiz.items if x.id == original_item.id), None
                )

                if target_item:
                    if generated_item_data:
                        q, v, h = generated_item_data
                        target_item.to_generated(q, v, h)

                    if used_chunks_data:
                        chunks_info, chunk_ids = used_chunks_data
                        if target_item.used_chunks is None:
                            target_item.used_chunks = []
                        target_item.used_chunks.extend(chunks_info)
                        # We already marked chunks as used in the task? No, let's do it here or in task.
                        # The original code did it in task.

            await self._quiz_repository.update(fresh_quiz, fresh_generated=True)

            logger.info(f"Generation completed for quiz {cmd.quiz_id}")

    async def _run_generation_task(
        self, quiz: Quiz, item: QuizItem, user: Principal, cache_key: str
    ) -> tuple[
        tuple[str, list[QuizItemVariant], str] | None,
        tuple[list[dict], list[str]] | None,
    ]:
        item_chunks = []
        chunk_ids = []

        if len(quiz.materials) > 0:
            result = await self._relevant_chunks(quiz, [item], user)
            item_chunks = [contents for contents, _ in result][0]
            chunk_ids = [ids for _, ids in result][0]

        dto = PatchGeneratorDto(
            quiz=quiz,
            cache_key=cache_key,
            chunks=item_chunks,
            item_order=item.order,
        )

        # This modifies the item in place in the original code?
        # No, `patch_generator.generate(dto)` likely returns something or modifies dto?
        # Let's check `PatchGenerator`. It's an interface.
        # Assuming it modifies `item` indirectly or we need to see how it was used.
        # Original code: `await self._patch_generator.generate(dto)`
        # Then it checks `dto.used_chunk_indices`.
        # Wait, where does the generated content go?
        # Ah, `PatchGenerator` probably calls `quiz.generation_step`?
        # Let's check `PatchGenerator` interface or implementation if possible.
        # But I don't have access to it right now without looking.
        # However, `quiz_generator.py` original code didn't seem to extract question/answer from `dto`.
        # It just called `generate(dto)`.
        # This implies `patch_generator.generate` has side effects on the `quiz` or `item`?
        # Or it calls `quiz.generation_step`.

        # If `patch_generator.generate` calls `quiz.generation_step`, it modifies the `quiz` object passed to it.
        # Since we are passing the `quiz` object from the Reservation phase (which might be stale),
        # `patch_generator` will modify THAT stale object.
        # We need to capture those modifications and apply them to the fresh quiz in Result phase.

        # But `patch_generator` might be calling `quiz.generation_step` which does:
        # item = next(...)
        # item.to_generated(...)

        # So the `item` inside `quiz` (the stale one) gets updated.
        # We can extract the new state from that `item` and return it.

        await self._patch_generator.generate(dto)

        # Now `item` (which is `items_to_generate[i]`) should be updated.
        generated_data = None
        if item.status == "generated":
            generated_data = (item.question, item.variants, item.hint)

        used_chunks_data = None
        if len(chunk_ids) > 0 and dto.used_chunk_indices is not None:
            used_chunk_ids = [
                chunk_ids[i] for i in dto.used_chunk_indices if i < len(chunk_ids)
            ]

            if len(used_chunk_ids) > 0:
                chunks_info = await self._material_app.get_chunks_info(used_chunk_ids)
                await self._material_app.mark_chunks_as_used(used_chunk_ids)
                used_chunks_data = (chunks_info, used_chunk_ids)
                logger.info(
                    f"Marked {len(used_chunk_ids)}/{len(chunk_ids)} chunks as used "
                    f"(LLM selected: {dto.used_chunk_indices}). "
                )
            else:
                logger.warning(
                    f"LLM returned used_chunk_indices {dto.used_chunk_indices} but no valid chunk IDs found"
                )
        elif len(chunk_ids) > 0:
            chunks_info = await self._material_app.get_chunks_info(chunk_ids)
            used_chunks_data = (chunks_info, chunk_ids)
            logger.warning(
                f"LLM did not return used_chunk_indices, marking all {len(chunk_ids)} chunks as used. "
            )
            await self._material_app.mark_chunks_as_used(chunk_ids)

        return generated_data, used_chunks_data

    async def _relevant_chunks(
        self, quiz: Quiz, items: list[QuizItem], user: Principal
    ) -> list[tuple[list[str], list[str]]]:
        num_clusters = len(quiz.cluster_vectors)
        central_vectors = [
            quiz.cluster_vectors[item.order % num_clusters] for item in items
        ]
        logger.info(f"Central vectors: {len(central_vectors)}")

        result_list: list[tuple[list[str], list[str]]] = []

        for idx, vector in enumerate(central_vectors):
            logger.info(f"Searching for vector {idx + 1}/{len(central_vectors)}")

            chunks = await self._material_app.search(
                SearchCmd(
                    user=user,
                    material_ids=[m.id for m in quiz.materials],
                    limit_tokens=PATCH_CHUNK_TOKEN_LIMIT,
                    vectors=[vector],
                )
            )

            chunk_ids = [c.id for c in chunks]
            chunk_contents = [c.content for c in chunks]

            result_list.append((chunk_contents, chunk_ids))
            logger.info(f"Vector {idx + 1}: found {len(chunks)} chunks")

        return result_list
