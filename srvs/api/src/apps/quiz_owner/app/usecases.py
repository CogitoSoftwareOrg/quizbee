import logging

from src.apps.llm_tools.domain._in import LLMToolsApp
from src.apps.material_owner.domain._in import MaterialApp, SearchCmd
from src.apps.user_owner.domain._in import Principal

from ..domain.out import (
    QuizFinalizer,
    PatchGenerator,
    QuizIndexer,
    QuizRepository,
)
from ..domain.models import Quiz, QuizStatus
from ..domain.constants import PATCH_LIMIT
from ..domain.errors import (
    NotQuizOwnerError,
    NotEnoughQuizItemsError,
    QuizNotAnsweredError,
)

from ..domain._in import (
    GenerateCmd,
    FinalizeQuizCmd,
    GenMode,
    QuizApp,
)

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
    ):
        self.quiz_repository = quiz_repository
        self.quiz_indexer = quiz_indexer
        self.material = material
        self.llm_tools = llm_tools
        self.patch_generator = patch_generator
        self.finalizer = finalizer

        self.quiz_generator = QuizGeneratorImpl(
            quiz_repository=quiz_repository,
            quiz_indexer=quiz_indexer,
            material_app=material,
            patch_generator=patch_generator,
        )
        self.quiz_starter = QuizStarterImpl(
            quiz_repository=quiz_repository,
            material_app=material,
            quiz_indexer=quiz_indexer,
        )

    async def start(self, cmd: GenerateCmd) -> None:
        await self.quiz_starter.start(cmd)
        await self.quiz_generator.generate(cmd)

    async def generate(self, cmd: GenerateCmd) -> None:
        await self.quiz_generator.generate(cmd)

    async def finalize(self, cmd: FinalizeQuizCmd) -> None:
        quiz = await self.quiz_repository.get(cmd.quiz_id)
        if quiz.author_id != cmd.user.id:
            raise NotQuizOwnerError(quiz_id=cmd.quiz_id, user_id=cmd.user.id)

        quiz.to_answered()
        await self.quiz_repository.update(quiz)
        await self.finalizer.finalize(quiz, cmd.cache_key)

        await self.quiz_indexer.index(quiz)
