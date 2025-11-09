from langfuse import Langfuse
from pocketbase import PocketBase
import httpx

from src.apps.message_owner.domain._in import MessageOwnerApp
from src.apps.llm_tools.domain._in import LLMToolsApp
from src.lib.di import AgentEnvelope, init_global_deps

from .adapters.out import (
    PBAttemptRepository,
    AIExplainer,
    AIAttemptFinalizer,
)
from .domain.ports import AttemptRepository, Explainer, AttemptFinalizer
from .app.usecases import QuizAttempterAppImpl


def init_quiz_attempter_deps(
    lf: Langfuse, admin_pb: PocketBase, http: httpx.AsyncClient
) -> tuple[AttemptRepository, Explainer, AttemptFinalizer]:
    attempt_repository = PBAttemptRepository(admin_pb, http=http)
    explainer = AIExplainer(
        lf=lf,
        output_type=AgentEnvelope,
    )
    finalizer = AIAttemptFinalizer(
        lf=lf,
        attempt_repository=attempt_repository,
        output_type=AgentEnvelope,
    )
    return attempt_repository, explainer, finalizer


def init_quiz_attempter_app(
    message_owner: MessageOwnerApp,
    llm_tools: LLMToolsApp,
    attempt_repository: AttemptRepository,
    explainer: Explainer,
    finalizer: AttemptFinalizer,
) -> QuizAttempterAppImpl:
    """Factory for QuizAttempterApp - all dependencies explicit"""
    return QuizAttempterAppImpl(
        attempt_repository=attempt_repository,
        explainer=explainer,
        message_owner=message_owner,
        llm_tools=llm_tools,
        finalizer=finalizer,
    )
