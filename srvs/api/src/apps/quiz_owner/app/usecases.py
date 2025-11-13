import redis.asyncio as redis

from src.apps.llm_tools.domain._in import LLMToolsApp
from src.apps.material_owner.domain._in import MaterialApp

from ..domain.out import (
    QuizFinalizer,
    PatchGenerator,
    QuizIndexer,
    QuizRepository,
)
from ..domain.errors import (
    NotQuizOwnerError,
)

from ..domain._in import GenMode, GenerateCmd, FinalizeQuizCmd, QuizApp

from .quiz_starter import QuizStarterImpl
from .quiz_generator import QuizGeneratorImpl


class QuizAppImpl(QuizApp):
    def __init__(
        self,
        quiz_repository: QuizRepository,
        quiz_indexer: QuizIndexer,
        llm_tools: LLMToolsApp,
        material: MaterialApp,
        patch_generator: PatchGenerator,
        finalizer: QuizFinalizer,
        redis_client: redis.Redis,
    ):
        self._quiz_repository = quiz_repository
        self._quiz_indexer = quiz_indexer
        self._finalizer = finalizer
        self._material = material

        self._quiz_generator = QuizGeneratorImpl(
            quiz_repository=quiz_repository,
            quiz_indexer=quiz_indexer,
            material_app=material,
            patch_generator=patch_generator,
            redis_client=redis_client,
        )
        self._quiz_starter = QuizStarterImpl(
            quiz_repository=quiz_repository,
            material_app=material,
            quiz_indexer=quiz_indexer,
        )

    async def start(self, cmd: GenerateCmd) -> None:
        await self._quiz_starter.start(cmd)
        await self._quiz_generator.generate(cmd)

    async def generate(self, cmd: GenerateCmd) -> None:
        await self._quiz_generator.generate(cmd)

    async def finalize(self, cmd: FinalizeQuizCmd) -> None:
        quiz = await self._quiz_repository.get(cmd.quiz_id)
        if quiz.author_id != cmd.user.id:
            raise NotQuizOwnerError(quiz_id=cmd.quiz_id, user_id=cmd.user.id)

        quiz.to_answered()
        await self._quiz_repository.update(quiz)
        await self._finalizer.finalize(quiz, cmd.cache_key)

        await self._quiz_indexer.index(quiz)

    async def mark_chunks_as_used(self, chunk_ids: list[str]) -> None:
        """
        Отмечает чанки материалов как использованные.

        Args:
            chunk_ids: Список ID чанков для пометки
        """
        await self._material.mark_chunks_as_used(chunk_ids)
