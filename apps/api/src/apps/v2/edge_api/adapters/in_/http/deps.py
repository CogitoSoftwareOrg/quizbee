from typing import Annotated


from fastapi import Depends, Request

from src.apps.v2.quiz_attempter.app.contracts import QuizAttempterApp
from src.apps.v2.quiz_generator.app.contracts import QuizGeneratorApp
from src.apps.v2.material_search.app.contracts import MaterialSearchApp


def get_quiz_attempter_app(request: Request) -> QuizAttempterApp:
    return request.app.state.quiz_attempter_app


QuizAttempterAppDeps = Annotated[QuizAttempterApp, Depends(get_quiz_attempter_app)]


def get_quiz_generator_app(request: Request) -> QuizGeneratorApp:
    return request.app.state.quiz_generator_app


QuizGeneratorAppDeps = Annotated[QuizGeneratorApp, Depends(get_quiz_generator_app)]


def get_material_search_app(request: Request) -> MaterialSearchApp:
    return request.app.state.material_search_app


MaterialSearchAppDeps = Annotated[MaterialSearchApp, Depends(get_material_search_app)]
