from typing import Any
from fastapi import FastAPI

from src.apps.user_owner.domain._in import AuthUserApp
from src.apps.quiz_owner.domain._in import QuizGeneratorApp
from src.apps.quiz_attempter.domain._in import QuizAttempterApp
from src.apps.material_owner.domain._in import MaterialApp

from .app.usecases import EdgeAPIAppImpl


def init_edge_api_app(
    auth_user_app: AuthUserApp,
    quiz_generator_app: QuizGeneratorApp,
    quiz_attempter_app: QuizAttempterApp,
    material_app: MaterialApp,
):
    return EdgeAPIAppImpl(
        user_auth=auth_user_app,
        quiz_generator=quiz_generator_app,
        quiz_attempter=quiz_attempter_app,
        material=material_app,
    )
