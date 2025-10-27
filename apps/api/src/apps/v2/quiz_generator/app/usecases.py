from ..domain.ports import QuizRepository
from ..domain.models import Quiz

from .contracts import GenerateCmd, FinilizeCmd, GenMode, QuizGeneratorApp


class QuizGeneratorAppImpl(QuizGeneratorApp):
    def __init__(self, quiz_repository: QuizRepository):
        self.quiz_repository = quiz_repository

    async def generate(self, cmd: GenerateCmd) -> None:
        pass

    async def finilize(self, cmd: FinilizeCmd) -> None:
        pass

    async def start(self, cmd: GenerateCmd) -> None:
        attempt = await self.quiz_repository.create_attempt(cmd.quiz_id, cmd.user_id)
