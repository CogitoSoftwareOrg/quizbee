import os
from langfuse import Langfuse
from pydantic_ai import Agent

lf = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST"),
    environment=os.getenv("PUBLIC_ENV"),
)

Agent.instrument_all()
