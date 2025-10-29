from src.apps.v2.user_auth.app.contracts import AuthUserApp

from ..domain.models import Attempt
from ..domain.ports import AttemptRepository

from .contracts import QuizAttempterApp, CreateCmd, FinalizeCmd


class QuizAttempterAppImpl(QuizAttempterApp):
    def __init__(self, attempt_repository: AttemptRepository, user_auth: AuthUserApp):
        self.attempt_repository = attempt_repository
        self.user_auth = user_auth

    async def create(self, cmd: CreateCmd) -> Attempt:
        user = await self.user_auth.validate(cmd.token)
        attempt = Attempt.create(cmd.quiz_id, user.id)
        await self.attempt_repository.save(attempt)
        return attempt

    async def finalize(self, cmd: FinalizeCmd) -> None:
        pass
