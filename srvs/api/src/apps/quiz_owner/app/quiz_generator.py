import logging
from typing import cast

from src.apps.material_owner.domain._in import MaterialApp, SearchCmd
from src.apps.material_owner.domain.models import MaterialChunk
from src.apps.user_owner.domain._in import Principal

from ..domain._in import GenMode, GenerateCmd, QuizGenerator
from ..domain.errors import NotQuizOwnerError
from ..domain.out import PatchGenerator, PatchGeneratorDto, QuizIndexer, QuizRepository
from ..domain.models import Quiz, QuizItem
from ..domain.constants import PATCH_CHUNK_TOKEN_LIMIT

from .errors import NoItemsReadyForGenerationError

logger = logging.getLogger(__name__)


class QuizGeneratorImpl(QuizGenerator):
    def __init__(
        self,
        quiz_repository: QuizRepository,
        quiz_indexer: QuizIndexer,
        material_app: MaterialApp,
        patch_generator: PatchGenerator,
    ):
        self._quiz_repository = quiz_repository
        self._quiz_indexer = quiz_indexer
        self._material_app = material_app
        self._patch_generator = patch_generator

    async def generate(self, cmd: GenerateCmd) -> None:
        ### эта функция отвечает за генерацию одного патча

        quiz = await self._quiz_repository.get(cmd.quiz_id)
        if quiz.author_id != cmd.user.id:
            raise NotQuizOwnerError(quiz_id=cmd.quiz_id, user_id=cmd.user.id)

        if cmd.mode == GenMode.Regenerate:
            logger.info(f"Incrementing generation for quiz {cmd.quiz_id}")
            quiz.increment_generation()
            await self._quiz_repository.update(quiz)

        items_to_generate = quiz.generate_patch()
        if len(items_to_generate) == 0:
            logging.error(
                f"No items ready for generation in quiz {cmd.quiz_id}. "
                f"All items may be FINAL or there are no items."
            )
            raise NoItemsReadyForGenerationError(quiz_id=cmd.quiz_id)
        await self._quiz_repository.update(quiz)

        if len(quiz.materials) > 0:
            result = await self._relevant_chunks(
                quiz, items_to_generate, cmd.user
            )
            
            chunk_contents_list = [contents for contents, _ in result]
            chunk_ids = [chunk_id for _, ids in result for chunk_id in ids]
        else:
            chunk_contents_list = []
            chunk_ids = []

        await self._patch_generator.generate(
            dto=(
                PatchGeneratorDto(
                    quiz=quiz,
                    cache_key=cmd.cache_key,
                    chunks=chunk_contents_list,
                )
            )
        )

        await self._material_app.mark_chunks_as_used(chunk_ids)
        logger.info(f"Marked {len(chunk_ids)} chunks as used for quiz {quiz.id}")

        await self._quiz_repository.update(quiz, fresh_generated=True)

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
