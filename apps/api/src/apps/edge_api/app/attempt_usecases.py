from src.apps.quiz_attempter.app.contracts import (
    AskExplainerCmd,
    FinalizeAttemptCmd,
    QuizAttempterApp,
)
from src.apps.user_auth.app.contracts import AuthUserApp
from src.apps.user_auth.domain.models import Tariff

from ..domain.errors import NotEnoughQuizItemsError
from ..domain._in import AttemptAPIApp, PublicAskExplainerCmd, PublicFinalizeAttemptCmd


class AttemptAPIAppImpl(AttemptAPIApp):
    def __init__(self, quiz_attempter: QuizAttempterApp, user_auth: AuthUserApp):
        self._quiz_attempter = quiz_attempter
        self._user_auth = user_auth

    async def finalize_attempt(self, cmd: PublicFinalizeAttemptCmd) -> None:
        user = await self._user_auth.validate(cmd.token)
        if user.tariff == Tariff.FREE:
            raise ValueError("Free tier does not support finalizing attempts")

        await self._quiz_attempter.finalize(
            FinalizeAttemptCmd(
                user=user,
                quiz_id=cmd.quiz_id,
                cache_key=cmd.cache_key,
                attempt_id=cmd.attempt_id,
            )
        )

    async def ask_explainer(self, cmd: PublicAskExplainerCmd):
        user = await self._user_auth.validate(cmd.token)
        cost = 1
        if user.remaining < cost:
            raise NotEnoughQuizItemsError(
                quiz_id=cmd.quiz_id, user_id=user.id, cost=1, stored=user.remaining
            )

        async for result in self._quiz_attempter.ask_explainer(
            AskExplainerCmd(
                user=user,
                cache_key=cmd.cache_key,
                attempt_id=cmd.attempt_id,
                query=cmd.query,
                item_id=cmd.item_id,
            )
        ):
            if result.status == "done":
                await self._user_auth.charge(user.id, cost)
            yield result
