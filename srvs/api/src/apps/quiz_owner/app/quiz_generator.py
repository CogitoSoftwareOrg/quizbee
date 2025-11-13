import logging
import redis.asyncio as redis

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

            to_generate = (
                PATCH_LIMIT if cmd.mode == GenMode.Continue else PATCH_LIMIT + HOLDOUT
            )

            if cmd.mode == GenMode.Continue:
                generated_items = quiz.generated_items()
                for item in generated_items[:HOLDOUT]:
                    item.to_final()
                await self._quiz_repository.update(quiz)

            if cmd.mode == GenMode.Regenerate:
                logger.info(f"Incrementing generation for quiz {cmd.quiz_id}")
                quiz.increment_generation()
                await self._quiz_repository.update(quiz)

            items_to_generate = quiz.generate_patch(to_generate)
            if len(items_to_generate) == 0:
                logging.error(
                    f"No items ready for generation in quiz {cmd.quiz_id}. "
                    f"All items may be FINAL or there are no items."
                )
                raise NoItemsReadyForGenerationError(quiz_id=cmd.quiz_id)
            await self._quiz_repository.update(quiz)

            chunk_contents = []
            chunk_ids = []
            if len(quiz.materials) > 0:
                chunk_contents, chunk_ids = await self._relevant_chunks(
                    quiz, items_to_generate, cmd.user
                )

            # Generate for each specific item by order to avoid race conditions
            for item in items_to_generate:
                await self._patch_generator.generate(
                    dto=(
                        PatchGeneratorDto(
                            quiz=quiz,
                            cache_key=cmd.cache_key,
                            chunks=chunk_contents,
                            item_order=item.order,
                        )
                    )
                )

            await self._material_app.mark_chunks_as_used(chunk_ids)
            logger.info(f"Marked {len(chunk_ids)} chunks as used for quiz {quiz.id}")

            await self._quiz_repository.update(quiz, fresh_generated=True)

            logger.info(f"Generation completed for quiz {cmd.quiz_id}")

    async def _relevant_chunks(
        self, quiz: Quiz, items: list[QuizItem], user: Principal
    ) -> tuple[list[str], list[str]]:
        num_clusters = len(quiz.cluster_vectors)
        central_vectors = [
            quiz.cluster_vectors[item.order % num_clusters] for item in items
        ]
        logger.info(f"Central vectors: {len(central_vectors)}")

        chunks = await self._material_app.search(
            SearchCmd(
                user=user,
                material_ids=[m.id for m in quiz.materials],
                limit_tokens=PATCH_CHUNK_TOKEN_LIMIT,
                vectors=central_vectors,
            )
        )

        chunk_ids = [c.id for c in chunks]
        chunk_contents = [c.content for c in chunks]

        return chunk_contents, chunk_ids
