from fastapi import FastAPI

from src.apps.v2.user_auth.app.contracts import AuthUserApp
from src.apps.v2.quiz_generator.app.contracts import QuizGeneratorApp
from src.apps.v2.quiz_attempter.app.contracts import QuizAttempterApp
from src.apps.v2.material_search.app.contracts import MaterialSearchApp

from .app.usecases import EdgeAPIAppImpl


def set_edge_api_app(
    app: FastAPI,
    auth_user_app: AuthUserApp,
    quiz_generator_app: QuizGeneratorApp,
    quiz_attempter_app: QuizAttempterApp,
    material_search_app: MaterialSearchApp,
):
    app.state.edge_api_app = EdgeAPIAppImpl(
        user_auth=auth_user_app,
        quiz_generator=quiz_generator_app,
        quiz_attempter=quiz_attempter_app,
        material_search=material_search_app,
    )
