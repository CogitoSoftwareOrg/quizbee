from src.apps.v2.user_auth.app.contracts import AuthUserApp

from ..domain.models import Attempt
from ..domain.ports import AttemptRepository
from ..domain.errors import NotAttemptOwnerError, AttemptAlreadyFinalizedError

from .contracts import QuizAttempterApp, FinalizeCmd


class QuizAttempterAppImpl(QuizAttempterApp):
    def __init__(self, attempt_repository: AttemptRepository, user_auth: AuthUserApp):
        self.attempt_repository = attempt_repository
        self.user_auth = user_auth

    async def finalize(self, cmd: FinalizeCmd) -> None:
        user = await self.user_auth.validate(cmd.token)
        attempt = await self.attempt_repository.get(cmd.attempt_id)

        if attempt.user_id != user.id:
            raise NotAttemptOwnerError(
                attempt_id=cmd.attempt_id, user_id=user.id, quiz_id=cmd.quiz_id
            )
        if attempt.feedback is not None:
            raise AttemptAlreadyFinalizedError(
                attempt_id=cmd.attempt_id, user_id=user.id, quiz_id=cmd.quiz_id
            )
