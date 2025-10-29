from typing import Annotated


from fastapi import Depends, Request

from ....app.contracts import QuizAttempterApp


def get_quiz_attempter_app(request: Request) -> QuizAttempterApp:
    return request.app.state.quiz_attempter_app


QuizAttempterAppDeps = Annotated[QuizAttempterApp, Depends(get_quiz_attempter_app)]
