from typing import Annotated
from fastapi import Depends, FastAPI, Request
import httpx
from pocketbase import PocketBase

from .adapters.out.pb_quiz_repository import PBQuizRepository

from .app.contracts import QuizGeneratorApp
from .app.usecases import QuizGeneratorAppImpl


def set_quiz_generator_app(app: FastAPI, admin_pb: PocketBase, http: httpx.AsyncClient):
    quiz_repository = PBQuizRepository(admin_pb, http)
    app.state.quiz_generator_app = QuizGeneratorAppImpl(quiz_repository)


def get_quiz_generator_app(request: Request) -> QuizGeneratorApp:
    return request.app.state.quiz_generator_app


QuizGeneratorAppDeps = Annotated[QuizGeneratorApp, Depends(get_quiz_generator_app)]
