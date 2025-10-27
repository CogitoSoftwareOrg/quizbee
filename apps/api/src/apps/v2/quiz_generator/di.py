from typing import Annotated
from fastapi import Depends, FastAPI, Request
from pocketbase import PocketBase

from .adapters.out.pb_repository import PBQAttemptRepository, PBQuizRepository

from .app.contracts import QuizGeneratorApp
from .app.usecases import QuizGeneratorAppImpl


def set_quiz_generator_app(app: FastAPI, admin_pb: PocketBase):
    quiz_repository = PBQuizRepository(admin_pb)
    app.state.quiz_generator_app = QuizGeneratorAppImpl(quiz_repository)


def get_quiz_generator_app(request: Request) -> QuizGeneratorApp:
    return request.app.state.quiz_generator_app


QuizGeneratorAppDeps = Annotated[QuizGeneratorApp, Depends(get_quiz_generator_app)]
