from ..domain.ports import QuizRepository
from ..domain.models import Quiz

from .contracts import GenerateCmd, FinilizeCmd, GenMode, QuizFinilizer, QuizGenerator


class QuizGeneratorApp(QuizFinilizer, QuizGenerator):
    def __init__(self, quiz_repository: QuizRepository):
        self.quiz_repository = quiz_repository

    async def generate(self, cmd: GenerateCmd) -> None:
        pass

    async def finilize(self, cmd: FinilizeCmd) -> None:
        pass
