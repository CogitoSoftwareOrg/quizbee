from typing import Union, Annotated
from pocketbase import PocketBase
from langfuse import Langfuse
from meilisearch_python_sdk import AsyncClient
import httpx
from pydantic import BaseModel, Field

from src.apps.quiz_attempter.adapters.out import (
    AttemptFinalizerOutput,
    ExplainerOutput,
)
from src.apps.quiz_owner.adapters.out import (
    AIQuizInstantGeneratorOutput,
    QuizFinalizerOutput,
)
from src.lib.settings import settings

AgentPayload = Annotated[
    Union[
        AIQuizInstantGeneratorOutput,
        QuizFinalizerOutput,
        ExplainerOutput,
        AttemptFinalizerOutput,
    ],
    Field(discriminator="mode"),
]


class AgentEnvelope(BaseModel):
    data: AgentPayload


def init_global_deps() -> tuple[PocketBase, Langfuse, AsyncClient, httpx.AsyncClient]:
    admin_pb = PocketBase(settings.pb_url)
    lf = Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
        environment=settings.env,
    )
    meili = AsyncClient(settings.meili_url, settings.meili_master_key)
    http = httpx.AsyncClient()
    return admin_pb, lf, meili, http
