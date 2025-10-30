from typing import Any
from fastapi import FastAPI

from src.apps..user_auth.app.contracts import AuthUserApp
from src.apps..quiz_generator.app.contracts import QuizGeneratorApp
from src.apps..quiz_attempter.app.contracts import QuizAttempterApp
from src.apps..material_search.app.contracts import MaterialSearchApp

from .app.usecases import EdgeAPIAppImpl


def init_edge_api_app(
    auth_user_app: AuthUserApp,
    quiz_generator_app: QuizGeneratorApp,
    quiz_attempter_app: QuizAttempterApp,
    material_search_app: MaterialSearchApp,
):
    return EdgeAPIAppImpl(
        user_auth=auth_user_app,
        quiz_generator=quiz_generator_app,
        quiz_attempter=quiz_attempter_app,
        material_search=material_search_app,
    )
