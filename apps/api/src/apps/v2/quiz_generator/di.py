from typing import Annotated
from fastapi import Depends, FastAPI, Request
import httpx
from meilisearch_python_sdk import AsyncClient
from pocketbase import PocketBase

from src.apps.v2.material_search.app.contracts import MaterialSearchApp
from src.apps.v2.llm_tools.app.contracts import LLMToolsApp


from .domain.ports import QuizRepository, AttemptRepository, QuizIndexer
from .app.contracts import QuizGeneratorApp
from .app.usecases import QuizGeneratorAppImpl


def set_quiz_generator_app(
    app: FastAPI,
    llm_tools: LLMToolsApp,
    material_search: MaterialSearchApp,
    quiz_repository: QuizRepository,
    attempt_repository: AttemptRepository,
    quiz_indexer: QuizIndexer,
):
    app.state.quiz_generator_app = QuizGeneratorAppImpl(
        quiz_repository,
        attempt_repository,
        quiz_indexer,
        llm_tools,
        material_search,
    )


def get_quiz_generator_app(request: Request) -> QuizGeneratorApp:
    return request.app.state.quiz_generator_app


QuizGeneratorAppDeps = Annotated[QuizGeneratorApp, Depends(get_quiz_generator_app)]
