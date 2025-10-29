from typing import Annotated
from fastapi import Depends, FastAPI, Request

from src.apps.v2.user_auth.app.contracts import AuthUserApp
from src.apps.v2.material_search.app.contracts import MaterialSearchApp
from src.apps.v2.llm_tools.app.contracts import LLMToolsApp


from .domain.ports import (
    Finalizer,
    QuizRepository,
    AttemptRepository,
    QuizIndexer,
    PatchGenerator,
)
from .app.contracts import QuizGeneratorApp
from .app.usecases import QuizGeneratorAppImpl


def set_quiz_generator_app(
    app: FastAPI,
    user_auth: AuthUserApp,
    llm_tools: LLMToolsApp,
    material_search: MaterialSearchApp,
    quiz_repository: QuizRepository,
    attempt_repository: AttemptRepository,
    quiz_indexer: QuizIndexer,
    patch_generator: PatchGenerator,
    finalizer: Finalizer,
):
    app.state.quiz_generator_app = QuizGeneratorAppImpl(
        user_auth=user_auth,
        quiz_repository=quiz_repository,
        attempt_repository=attempt_repository,
        quiz_indexer=quiz_indexer,
        llm_tools=llm_tools,
        material_search=material_search,
        patch_generator=patch_generator,
        finalizer=finalizer,
    )


def get_quiz_generator_app(request: Request) -> QuizGeneratorApp:
    return request.app.state.quiz_generator_app


QuizGeneratorAppDeps = Annotated[QuizGeneratorApp, Depends(get_quiz_generator_app)]
