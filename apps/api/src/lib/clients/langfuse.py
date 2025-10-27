from typing import Annotated
from langfuse import Langfuse
from fastapi import Depends, FastAPI, Request
from pydantic_ai.agent import Agent

from src.lib.settings import settings


def set_langfuse(app: FastAPI):
    app.state.langfuse_client = Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
        environment=settings.env,
    )


def get_langfuse(request: Request) -> Langfuse:
    return request.app.state.langfuse_client


LangfuseDeps = Annotated[Langfuse, Depends(get_langfuse)]


# if settings.env != "production":
#     Agent.instrument_all()
