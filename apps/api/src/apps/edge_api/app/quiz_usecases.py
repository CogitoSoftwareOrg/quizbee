from src.apps.quiz_generator.app.contracts import (
    FinalizeQuizCmd,
    GenMode,
    GenerateCmd,
    QuizGeneratorApp,
)
from src.apps.user_auth.app.contracts import AuthUserApp

from ..domain._in import (
    PublicFinalizeQuizCmd,
    QuizAPIApp,
    PublicStartQuizCmd,
    PublicGenerateQuizItemsCmd,
)
from ..domain.constants import PATCH_LIMIT
from ..domain.errors import NotEnoughQuizItemsError


class QuizAPIAppImpl(QuizAPIApp):
    def __init__(self, quiz_generator: QuizGeneratorApp, user_auth: AuthUserApp):
        self._quiz_generator = quiz_generator
        self._user_auth = user_auth

    async def start_quiz(self, cmd: PublicStartQuizCmd) -> None:
        user = await self._user_auth.validate(cmd.token)
        cost = PATCH_LIMIT
        if user.remaining < cost:
            raise NotEnoughQuizItemsError(
                quiz_id=cmd.quiz_id, user_id=user.id, cost=cost, stored=user.remaining
            )

        await self._quiz_generator.start(
            GenerateCmd(
                user=user,
                quiz_id=cmd.quiz_id,
                cache_key=cmd.cache_key,
                mode=GenMode.Continue,
            )
        )

        await self._user_auth.charge(user.id, cost)

    async def generate_quiz_items(self, cmd: PublicGenerateQuizItemsCmd) -> None:
        user = await self._user_auth.validate(cmd.token)
        cost = PATCH_LIMIT
        if user.remaining < cost:
            raise NotEnoughQuizItemsError(
                quiz_id=cmd.quiz_id, user_id=user.id, cost=cost, stored=user.remaining
            )

        await self._quiz_generator.generate(
            GenerateCmd(
                user=user,
                quiz_id=cmd.quiz_id,
                mode=cmd.mode,
                cache_key=cmd.cache_key,
            )
        )

        await self._user_auth.charge(user.id, cost)

    async def finalize_quiz(self, cmd: PublicFinalizeQuizCmd) -> None:
        user = await self._user_auth.validate(cmd.token)
        await self._quiz_generator.finalize(
            FinalizeQuizCmd(
                user=user,
                quiz_id=cmd.quiz_id,
                cache_key=cmd.cache_key,
            )
        )
