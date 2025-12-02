import logging
import redis.asyncio as redis
import asyncio
import re
from dataclasses import dataclass

from src.apps.material_owner.domain._in import MaterialApp, SearchCmd
from src.apps.material_owner.domain.models import MaterialChunk, SearchType
from src.apps.user_owner.domain._in import Principal
from src.lib.distributed_lock import DistributedLock

from ..domain._in import GenMode, GenerateCmd, QuizGenerator
from ..domain.errors import NotQuizOwnerError
from ..domain.out import PatchGenerator, PatchGeneratorDto, QuizIndexer, QuizRepository
from ..domain.models import Quiz, QuizItem, QuizItemVariant
from ..domain.constants import DEFAULT_CHUNKS_PER_QUESTION, HOLDOUT, PATCH_LIMIT

from .errors import NoItemsReadyForGenerationError

logger = logging.getLogger(__name__)

PAGE_MARKER_PATTERN = re.compile(r"\{quizbee_page_number_(\d+)\}")


@dataclass
class SubChunk:
    chunk_id: str
    page: int
    content: str
    material_id: str
    title: str


def split_chunk_by_pages(
    chunk_id: str,
    content: str,
    pages: list[int],
    material_id: str,
    title: str,
) -> list[SubChunk]:
    if not pages or len(pages) <= 1:
        page = pages[0] if pages else 0
        clean_content = PAGE_MARKER_PATTERN.sub("", content).strip()
        return [
            SubChunk(
                chunk_id=chunk_id,
                page=page,
                content=clean_content,
                material_id=material_id,
                title=title,
            )
        ]

    sub_chunks: list[SubChunk] = []
    parts = PAGE_MARKER_PATTERN.split(content)

    current_page = pages[0]
    for i, part in enumerate(parts):
        if i % 2 == 1:
            current_page = int(part)
        else:
            clean_part = part.strip()
            if clean_part:
                sub_chunks.append(
                    SubChunk(
                        chunk_id=chunk_id,
                        page=current_page,
                        content=clean_part,
                        material_id=material_id,
                        title=title,
                    )
                )

    return (
        sub_chunks
        if sub_chunks
        else [
            SubChunk(
                chunk_id=chunk_id,
                page=pages[0],
                content=PAGE_MARKER_PATTERN.sub("", content).strip(),
                material_id=material_id,
                title=title,
            )
        ]
    )


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
        chunks: list[MaterialChunk] = []
        sub_chunks: list[SubChunk] = []

        if len(quiz.materials) > 0:
            chunks = await self._relevant_chunks(quiz, item, user)
            for chunk in chunks:
                sub_chunks.extend(
                    split_chunk_by_pages(
                        chunk_id=chunk.id,
                        content=chunk.content,
                        pages=chunk.pages,
                        material_id=chunk.material_id,
                        title=chunk.title,
                    )
                )

        sub_chunk_contents = [sc.content for sc in sub_chunks]

        dto = PatchGeneratorDto(
            quiz=quiz,
            cache_key=cache_key,
            chunks=sub_chunk_contents if sub_chunk_contents else None,
            item_order=item.order,
        )

        await self._patch_generator.generate(dto)

        # Now `item` (which is `items_to_generate[i]`) should be updated.
        generated_data = None
        if item.status == "generated":
            generated_data = (item.question, item.variants, item.hint)

        used_chunks_data = None
        if len(sub_chunks) > 0 and dto.used_chunk_indices is not None:
            logger.info(f"Number of used sub-chunks: {len(dto.used_chunk_indices)}")
            used_sub_chunks = [
                sub_chunks[i] for i in dto.used_chunk_indices if i < len(sub_chunks)
            ]

            if len(used_sub_chunks) > 0:
                used_chunk_to_pages: dict[str, set[int]] = {}
                for sc in used_sub_chunks:
                    if sc.chunk_id not in used_chunk_to_pages:
                        used_chunk_to_pages[sc.chunk_id] = set()
                    used_chunk_to_pages[sc.chunk_id].add(sc.page)

                used_chunk_ids = list(used_chunk_to_pages.keys())

                chunks_info = await self._material_app.get_chunks_info(used_chunk_ids)

                for info in chunks_info:
                    chunk_id = info.get("id", "")
                    if chunk_id in used_chunk_to_pages:
                        info["pages"] = sorted(used_chunk_to_pages[chunk_id])

                await self._material_app.mark_chunks_as_used(used_chunk_ids)
                used_chunks_data = (chunks_info, used_chunk_ids)
                logger.info(
                    f"Marked {len(used_chunk_ids)} chunks as used "
                    f"(LLM selected {len(used_sub_chunks)} sub-chunks from {len(sub_chunks)} total). "
                    f"Chunks info: {chunks_info}"
                )
            else:
                logger.warning(
                    f"LLM returned used_chunk_indices {dto.used_chunk_indices} but no valid sub-chunks found"
                )
        elif len(sub_chunks) > 0:
            chunk_to_pages: dict[str, set[int]] = {}
            for sc in sub_chunks:
                if sc.chunk_id not in chunk_to_pages:
                    chunk_to_pages[sc.chunk_id] = set()
                chunk_to_pages[sc.chunk_id].add(sc.page)

            all_chunk_ids = list(chunk_to_pages.keys())
            chunks_info = await self._material_app.get_chunks_info(all_chunk_ids)

            for info in chunks_info:
                chunk_id = info.get("id", "")
                if chunk_id in chunk_to_pages:
                    info["pages"] = sorted(chunk_to_pages[chunk_id])

            await self._material_app.mark_chunks_as_used(all_chunk_ids)
            used_chunks_data = (chunks_info, all_chunk_ids)
            logger.warning(
                f"LLM did not return used_chunk_indices, marking all {len(all_chunk_ids)} chunks as used. "
                f"Chunks info: {chunks_info}"
            )

        return generated_data, used_chunks_data

    async def _relevant_chunks(
        self, quiz: Quiz, item: QuizItem, user: Principal
    ) -> list[MaterialChunk]:
        num_clusters = len(quiz.cluster_vectors)
        cluster_idx = item.order % num_clusters
        vector = quiz.cluster_vectors[cluster_idx]
        threshold = (
            quiz.cluster_thresholds[cluster_idx]
            if cluster_idx < len(quiz.cluster_thresholds)
            else None
        )

        logger.info(
            f"Searching for item {item.order} with vector cluster {cluster_idx}, threshold: {threshold}"
        )

        limit_chunks = quiz.chunks_per_question or DEFAULT_CHUNKS_PER_QUESTION

        chunks = await self._material_app.search(
            SearchCmd(
                user=user,
                material_ids=[m.id for m in quiz.materials],
                limit_chunks=limit_chunks,
                vectors=[vector],
                vector_thresholds=[threshold] if threshold else None,
                search_type=SearchType.GENERATOR,
            )
        )

        logger.info(f"Found {len(chunks)} chunks for item {item.order}")
        return chunks
