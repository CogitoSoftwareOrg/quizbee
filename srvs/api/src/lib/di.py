from openai import AsyncOpenAI
from pydantic_ai import Agent
from pocketbase import PocketBase
from langfuse import Langfuse
from meilisearch_python_sdk import AsyncClient
import httpx
from pydantic_ai.providers.openai import OpenAIProvider

from src.lib.settings import settings


def init_global_deps() -> (
    tuple[PocketBase, Langfuse, AsyncClient, httpx.AsyncClient, OpenAIProvider]
):
    # Agent.instrument_all(settings.env == "local")

    admin_pb = PocketBase(settings.pb_url)
    lf = Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
        environment=settings.env,
    )
    meili = AsyncClient(settings.meili_url, settings.meili_master_key)
    http = httpx.AsyncClient()

    grok_provider = OpenAIProvider(
        openai_client=AsyncOpenAI(
            api_key=settings.grok_api_key,
            base_url="https://api.x.ai/v1",
        )
    )
    return admin_pb, lf, meili, http, grok_provider
