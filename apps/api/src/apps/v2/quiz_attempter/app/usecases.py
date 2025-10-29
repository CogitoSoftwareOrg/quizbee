from src.apps.v2.user_auth.app.contracts import AuthUserApp

from ..domain.models import Attempt
from ..domain.ports import AttemptRepository

from .contracts import QuizAttempterApp, FinalizeCmd


class QuizAttempterAppImpl(QuizAttempterApp):
    def __init__(self, attempt_repository: AttemptRepository, user_auth: AuthUserApp):
        self.attempt_repository = attempt_repository
        self.user_auth = user_auth

    async def finalize(self, cmd: FinalizeCmd) -> None:
        pass
