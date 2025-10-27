from fastapi import Depends, FastAPI, Request
from meilisearch_python_sdk import AsyncClient
from typing import Annotated

from src.lib.settings import settings


def set_meili_client(app: FastAPI):
    app.state.meili_client = AsyncClient(settings.meili_url, settings.meili_master_key)


def get_meiliclient(request: Request) -> AsyncClient:
    return request.app.state.meili_client


MeiliDeps = Annotated[AsyncClient, Depends(get_meiliclient)]
