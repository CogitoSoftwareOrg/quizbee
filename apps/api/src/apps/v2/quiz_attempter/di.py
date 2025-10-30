from typing import Annotated
from fastapi import Depends, FastAPI, Request

from src.apps.v2.message_owner.app.contracts import MessageOwnerApp
from src.apps.v2.llm_tools.app.contracts import LLMToolsApp

from .domain.ports import AttemptRepository, Explainer, AttemptFinalizer
from .app.contracts import QuizAttempterApp
from .app.usecases import QuizAttempterAppImpl


def init_quiz_attempter_app(
    attempt_repository: AttemptRepository,
    explainer: Explainer,
    message_owner: MessageOwnerApp,
    llm_tools: LLMToolsApp,
    finalizer: AttemptFinalizer,
):

    return QuizAttempterAppImpl(
        attempt_repository=attempt_repository,
        explainer=explainer,
        message_owner=message_owner,
        llm_tools=llm_tools,
        finalizer=finalizer,
    )
