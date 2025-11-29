from langfuse import Langfuse
from pocketbase import PocketBase
import httpx

from src.apps.material_owner.domain._in import MaterialApp
from src.apps.message_owner.domain._in import MessageOwnerApp
from src.apps.llm_tools.domain._in import LLMToolsApp

from .adapters.out import (
    PBAttemptRepository,
    AIGrokExplainer,
    AIAttemptFinalizer,
)
from .domain.out import AttemptRepository, Explainer, AttemptFinalizer
from .app.usecases import QuizAttempterAppImpl


def init_quiz_attempter_deps(
    lf: Langfuse,
    admin_pb: PocketBase,
    http: httpx.AsyncClient,
    material_app: MaterialApp,
    llm_tools: LLMToolsApp,
) -> tuple[AttemptRepository, Explainer, AttemptFinalizer]:
    attempt_repository = PBAttemptRepository(admin_pb, http=http)
    explainer = AIGrokExplainer(lf=lf, material_app=material_app, llm_tools=llm_tools)
    finalizer = AIAttemptFinalizer(lf=lf, attempt_repository=attempt_repository)
    return attempt_repository, explainer, finalizer


def init_quiz_attempter_app(
    message_owner: MessageOwnerApp,
    llm_tools: LLMToolsApp,
    attempt_repository: AttemptRepository,
    explainer: Explainer,
    finalizer: AttemptFinalizer,
    material_app: MaterialApp,
) -> QuizAttempterAppImpl:
    """Factory for QuizAttempterApp - all dependencies explicit"""
    return QuizAttempterAppImpl(
        attempt_repository=attempt_repository,
        explainer=explainer,
        message_owner=message_owner,
        llm_tools=llm_tools,
        finalizer=finalizer,
        material_app=material_app,
    )
