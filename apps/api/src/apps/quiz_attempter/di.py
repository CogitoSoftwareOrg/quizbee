from langfuse import Langfuse
from pocketbase import PocketBase
import httpx

from src.apps.message_owner.app.contracts import MessageOwnerApp
from src.apps.llm_tools.app.contracts import LLMToolsApp
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
    attempt_repository: AttemptRepository | None = None,
    explainer: Explainer | None = None,
    finalizer: AttemptFinalizer | None = None,
):
    if attempt_repository is None or explainer is None or finalizer is None:
        admin_pb, lf, _, http = init_global_deps()
        default_attempt_repository, default_explainer, default_finalizer = (
            init_quiz_attempter_deps(lf=lf, admin_pb=admin_pb, http=http)
        )
        attempt_repository = attempt_repository or default_attempt_repository
        explainer = explainer or default_explainer
        finalizer = finalizer or default_finalizer

    return QuizAttempterAppImpl(
        attempt_repository=attempt_repository,
        explainer=explainer,
        message_owner=message_owner,
        llm_tools=llm_tools,
        finalizer=finalizer,
    )
