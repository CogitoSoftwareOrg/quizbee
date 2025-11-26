from src.apps.quiz_owner.domain._in import (
    QuizApp,
    GenerateCmd,
    FinalizeQuizCmd,
    GenMode,
)
from src.apps.quiz_attempter.domain._in import (
    QuizAttempterApp,
    FinalizeAttemptCmd,
    AskExplainerCmd,
)
from src.apps.material_owner.domain._in import (
    AddMaterialCmd,
    MaterialApp,
    Material,
    RemoveMaterialCmd,
)
from src.apps.user_owner.domain._in import AuthUserApp
from src.apps.user_owner.domain.models import Tariff
from src.apps.quiz_owner.domain.constants import PATCH_LIMIT

from ..domain.errors import NotEnoughQuizItemsError

from ..domain._in import (
    EdgeAPIApp,
    PublicRemoveMaterialCmd,
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
        quiz_app: QuizApp,
        quiz_attempter: QuizAttempterApp,
        material: MaterialApp,
    ):
        self.user_auth = user_auth
        self.quiz_app = quiz_app
        self.quiz_attempter = quiz_attempter
        self.material = material

    async def start_quiz(self, cmd: PublicStartQuizCmd) -> None:
        user = await self.user_auth.validate(cmd.token)
        cost = PATCH_LIMIT * 2
        if user.remaining < cost:
            raise NotEnoughQuizItemsError(
                quiz_id=cmd.quiz_id, user_id=user.id, cost=cost, stored=user.remaining
            )

        await self.quiz_app.start(
            GenerateCmd(
                user=user,
                quiz_id=cmd.quiz_id,
                cache_key=cmd.cache_key,
                mode=GenMode.Start,
            )
        )

        await self.user_auth.charge(user.id, cost)

    async def generate_quiz_items(self, cmd: PublicGenerateQuizItemsCmd) -> None:
        user = await self.user_auth.validate(cmd.token)
        cost = PATCH_LIMIT if cmd.mode != GenMode.Regenerate else 0
        if user.remaining <= cost:
            raise NotEnoughQuizItemsError(
                quiz_id=cmd.quiz_id, user_id=user.id, cost=cost, stored=user.remaining
            )

        await self.quiz_app.generate(
            GenerateCmd(
                user=user,
                quiz_id=cmd.quiz_id,
                mode=cmd.mode,
                cache_key=cmd.cache_key,
            )
        )

        if cost > 0:
            await self.user_auth.charge(user.id, cost)

    async def finalize_quiz(self, cmd: PublicFinalizeQuizCmd) -> None:
        user = await self.user_auth.validate(cmd.token)
        await self.quiz_app.finalize(
            FinalizeQuizCmd(
                user=user,
                quiz_id=cmd.quiz_id,
                cache_key=cmd.cache_key,
            )
        )

    async def finalize_attempt(self, cmd: PublicFinalizeAttemptCmd) -> None:
        user = await self.user_auth.validate(cmd.token)
        if user.tariff == Tariff.FREE:
            raise ValueError("Free tier does not support finalizing attempts")

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

        # Check storage limit
        file_size = len(cmd.file.file_bytes)
        if user.storage_usage + file_size > user.storage_limit:
            raise ValueError(
                f"Storage limit exceeded. Used: {user.storage_usage}, Limit: {user.storage_limit}, File: {file_size}"
            )

        material = await self.material.add_material(
            AddMaterialCmd(
                quiz_id=cmd.quiz_id or "",
                user=user,
                file=cmd.file,
                title=cmd.title,
                material_id=cmd.material_id,
                hash=cmd.hash,
            )
        )

        await self.user_auth.update_storage(user.id, file_size)

        return material

    async def remove_material(self, cmd: PublicRemoveMaterialCmd) -> None:
        user = await self.user_auth.validate(cmd.token)

        # Get material to know its size
        material = await self.material.get_material(cmd.material_id)
        size_to_free = material.size_bytes if material else 0

        await self.material.remove_material(
            RemoveMaterialCmd(
                user=user,
                material_id=cmd.material_id,
            )
        )

        if size_to_free > 0:
            await self.user_auth.update_storage(user.id, -size_to_free)

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
