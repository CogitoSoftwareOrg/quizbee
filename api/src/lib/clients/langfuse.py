from langfuse import Langfuse
from pydantic_ai.agent import Agent

from lib.settings import settings

langfuse_client = Langfuse(
    public_key=settings.langfuse_public_key,
    secret_key=settings.langfuse_secret_key,
    host=settings.langfuse_host,
    environment=settings.env,
)

Agent.instrument_all()
