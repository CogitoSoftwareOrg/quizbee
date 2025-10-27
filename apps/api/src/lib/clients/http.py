from typing import Annotated
import httpx
from fastapi import Depends, FastAPI, Request


def set_http_client(app: FastAPI):
    app.state.http_client = httpx.AsyncClient()


def get_http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http_client


HTTPAsyncClient = Annotated[httpx.AsyncClient, Depends(get_http_client)]
