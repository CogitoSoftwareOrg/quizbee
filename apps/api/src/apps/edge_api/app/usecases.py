from src.apps.quiz_generator.app.contracts import QuizGeneratorApp
from src.apps.quiz_attempter.app.contracts import QuizAttempterApp
from src.apps.material_search.app.contracts import MaterialSearchApp
from src.apps.user_auth.app.contracts import AuthUserApp

from ..domain._in import (
    EdgeAPIApp,
    PublicStartQuizCmd,
    PublicGenerateQuizItemsCmd,
    PublicFinalizeQuizCmd,
    PublicFinalizeAttemptCmd,
    PublicAskExplainerCmd,
    PublicAddMaterialCmd,
    PublicRemoveMaterialCmd,
)
from .quiz_usecases import QuizAPIAppImpl
from .attempt_usecases import AttemptAPIAppImpl
from .material_usecases import MaterialAPIAppImpl


class EdgeAPIAppImpl(EdgeAPIApp):
    def __init__(
        self,
        user_auth: AuthUserApp,
        quiz_generator: QuizGeneratorApp,
        quiz_attempter: QuizAttempterApp,
        material_search: MaterialSearchApp,
    ):
        self._quiz_api = QuizAPIAppImpl(
            quiz_generator=quiz_generator,
            user_auth=user_auth,
        )
        self._attempt_api = AttemptAPIAppImpl(
            quiz_attempter=quiz_attempter,
            user_auth=user_auth,
        )
        self._material_api = MaterialAPIAppImpl(
            material_search=material_search,
            user_auth=user_auth,
        )

    async def start_quiz(self, cmd: PublicStartQuizCmd) -> None:
        return await self._quiz_api.start_quiz(cmd)

    async def generate_quiz_items(self, cmd: PublicGenerateQuizItemsCmd) -> None:
        return await self._quiz_api.generate_quiz_items(cmd)

    async def finalize_quiz(self, cmd: PublicFinalizeQuizCmd) -> None:
        return await self._quiz_api.finalize_quiz(cmd)

    async def finalize_attempt(self, cmd: PublicFinalizeAttemptCmd) -> None:
        return await self._attempt_api.finalize_attempt(cmd)

    async def ask_explainer(self, cmd: PublicAskExplainerCmd):
        async for result in self._attempt_api.ask_explainer(cmd):
            yield result

    async def add_material(self, cmd: PublicAddMaterialCmd):
        return await self._material_api.add_material(cmd)

    async def remove_material(self, cmd: PublicRemoveMaterialCmd) -> None:
        return await self._material_api.remove_material(cmd)
