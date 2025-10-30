from src.apps.quiz_generator.app.contracts import (
    QuizGeneratorApp,
    GenerateCmd,
    FinalizeQuizCmd,
    GenMode,
)
from src.apps.quiz_attempter.app.contracts import (
    QuizAttempterApp,
    FinalizeAttemptCmd,
    AskExplainerCmd,
)
from src.apps.material_search.app.contracts import (
    AddMaterialCmd,
    MaterialSearchApp,
    Material,
)
from src.apps.user_auth.app.contracts import AuthUserApp

from ..domain.errors import NotEnoughQuizItemsError
from ..domain.constants import PATCH_LIMIT

from .contracts import (
    EdgeAPIApp,
    PublicStartQuizCmd,
    PublicGenerateQuizItemsCmd,
    PublicFinalizeQuizCmd,
    PublicFinalizeAttemptCmd,
    PublicAskExplainerCmd,
    PublicAddMaterialCmd,
)


class EdgeAPIAppImpl(EdgeAPIApp):
    def __init__(
        self,
        user_auth: AuthUserApp,
        quiz_generator: QuizGeneratorApp,
        quiz_attempter: QuizAttempterApp,
        material_search: MaterialSearchApp,
    ):
        self.user_auth = user_auth
        self.quiz_generator = quiz_generator
        self.quiz_attempter = quiz_attempter
        self.material_search = material_search

    async def start_quiz(self, cmd: PublicStartQuizCmd) -> None:
        user = await self.user_auth.validate(cmd.token)
        cost = PATCH_LIMIT
        if user.remaining < cost:
            raise NotEnoughQuizItemsError(
                quiz_id=cmd.quiz_id, user_id=user.id, cost=cost, stored=user.remaining
            )

        await self.quiz_generator.start(
            GenerateCmd(
                user=user,
                quiz_id=cmd.quiz_id,
                cache_key=cmd.cache_key,
                mode=GenMode.Continue,
            )
        )

        await self.user_auth.charge(user.id, cost)

    async def generate_quiz_items(self, cmd: PublicGenerateQuizItemsCmd) -> None:
        user = await self.user_auth.validate(cmd.token)
        cost = PATCH_LIMIT
        if user.remaining < cost:
            raise NotEnoughQuizItemsError(
                quiz_id=cmd.quiz_id, user_id=user.id, cost=cost, stored=user.remaining
            )

        await self.quiz_generator.generate(
            GenerateCmd(
                user=user,
                quiz_id=cmd.quiz_id,
                mode=cmd.mode,
                cache_key=cmd.cache_key,
            )
        )

        await self.user_auth.charge(user.id, cost)

    async def finalize_quiz(self, cmd: PublicFinalizeQuizCmd) -> None:
        user = await self.user_auth.validate(cmd.token)
        await self.quiz_generator.finalize(
            FinalizeQuizCmd(
                user=user,
                quiz_id=cmd.quiz_id,
                cache_key=cmd.cache_key,
            )
        )

    async def finalize_attempt(self, cmd: PublicFinalizeAttemptCmd) -> None:
        user = await self.user_auth.validate(cmd.token)
        await self.quiz_attempter.finalize(
            FinalizeAttemptCmd(
                user=user,
                quiz_id=cmd.quiz_id,
                cache_key=cmd.cache_key,
                attempt_id=cmd.attempt_id,
            )
        )

    async def add_material(self, cmd: PublicAddMaterialCmd) -> Material:
        user = await self.user_auth.validate(cmd.token)
        material = await self.material_search.add_material(
            AddMaterialCmd(
                user=user,
                file=cmd.file,
                title=cmd.title,
                material_id=cmd.material_id,
            )
        )
        return material

    async def ask_explainer(self, cmd: PublicAskExplainerCmd):
        user = await self.user_auth.validate(cmd.token)
        cost = 1
        if user.remaining < cost:
            raise NotEnoughQuizItemsError(
                quiz_id=cmd.quiz_id, user_id=user.id, cost=1, stored=user.remaining
            )

        async for result in self.quiz_attempter.ask_explainer(
            AskExplainerCmd(
                user=user,
                cache_key=cmd.cache_key,
                attempt_id=cmd.attempt_id,
                query=cmd.query,
                item_id=cmd.item_id,
            )
        ):
            if result.status == "done":
                await self.user_auth.charge(user.id, cost)
            yield result
