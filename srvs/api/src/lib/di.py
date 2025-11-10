from pocketbase import PocketBase
from langfuse import Langfuse
from meilisearch_python_sdk import AsyncClient
import httpx

from src.lib.settings import settings


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
