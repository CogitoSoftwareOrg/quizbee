from typing import Annotated
from fastapi import Depends, FastAPI, Request

from src.apps.v2.user_auth.app.contracts import AuthUserApp

from .domain.ports import AttemptRepository

from .app.contracts import QuizAttempterApp
from .app.usecases import QuizAttempterAppImpl


def set_quiz_attempter_app(
    app: FastAPI,
    attempt_repository: AttemptRepository,
    user_auth: AuthUserApp,
):
    app.state.quiz_attempter_app = QuizAttempterAppImpl(
        attempt_repository=attempt_repository,
        user_auth=user_auth,
    )


def get_quiz_attempter_app(request: Request) -> QuizAttempterApp:
    return request.app.state.quiz_attempter_app


QuizAttempterAppDeps = Annotated[QuizAttempterApp, Depends(get_quiz_attempter_app)]
