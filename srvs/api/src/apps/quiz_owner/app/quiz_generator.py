import logging
import redis.asyncio as redis
import asyncio

from src.apps.material_owner.domain._in import MaterialApp, SearchCmd
from src.apps.user_owner.domain._in import Principal
from src.lib.distributed_lock import DistributedLock

from ..domain._in import GenMode, GenerateCmd, QuizGenerator
from ..domain.errors import NotQuizOwnerError
from ..domain.out import PatchGenerator, PatchGeneratorDto, QuizIndexer, QuizRepository
from ..domain.models import Quiz, QuizItem
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

        async with self._lock.lock(lock_key, wait_timeout=60.0):
            logger.info(f"Acquired lock for quiz generation: {cmd.quiz_id}")

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
            await self._quiz_repository.update(quiz)

            # Generate for each specific item by order to avoid race conditions
            generation_tasks = []
            for idx, item in enumerate(items_to_generate):
                generation_tasks.append(
                    self._run_generation_task(quiz, item, cmd.user, cmd.cache_key)
                )

            await asyncio.gather(*generation_tasks)

            await self._quiz_repository.update(quiz, fresh_generated=True)

            logger.info(f"Generation completed for quiz {cmd.quiz_id}")

    async def _run_generation_task(
        self, quiz: Quiz, item: QuizItem, user: Principal, cache_key: str
    ) -> None:
        item_chunks = []
        chunk_ids = []

        if len(quiz.materials) > 0:
            result = await self._relevant_chunks(quiz, [item], user)
            item_chunks = [contents for contents, _ in result][0]
            chunk_ids = [ids for _, ids in result][0]

        await self._patch_generator.generate(
            dto=PatchGeneratorDto(
                quiz=quiz,
                cache_key=cache_key,
                chunks=item_chunks,
                item_order=item.order,
            )
        )

        if len(chunk_ids) > 0:
            await self._material_app.mark_chunks_as_used(chunk_ids)

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
