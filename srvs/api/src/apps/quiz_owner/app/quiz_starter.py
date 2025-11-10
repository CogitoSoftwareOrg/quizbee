import logging

from ..domain._in import QuizStarter, GenerateCmd
from ..domain.out import QuizRepository, QuizPreparator

logger = logging.getLogger(__name__)


class QuizStarterImpl(QuizStarter):
    def __init__(
        self, quiz_repository: QuizRepository, quiz_preparator: QuizPreparator
    ):
        self._quiz_repository = quiz_repository
        self._quiz_preparator = quiz_preparator

    async def start(self, cmd: GenerateCmd) -> None:
        quiz = await self._quiz_repository.get(cmd.quiz_id)
        quiz.to_preparing()
        await self._quiz_repository.update(quiz)

        await self._quiz_preparator.prepare(quiz)
        quiz.to_creating()
        quiz.increment_generation()
        await self._quiz_repository.update(quiz)
