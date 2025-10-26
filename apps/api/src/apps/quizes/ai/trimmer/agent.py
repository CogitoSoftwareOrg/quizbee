from typing import Annotated
from fastapi import Depends, FastAPI
from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    SystemPromptPart,
    UserPromptPart,
)

from src.lib.ai import TrimmerDeps, TrimmerOutput, AgentEnvelope
from src.lib.config import LLMS
from src.lib.clients import langfuse_client
from src.lib.settings import settings

TRIMMER_LLM = LLMS.GPT_5_NANO


async def inject_request_prompt(
    ctx: RunContext[TrimmerDeps], messages: list[ModelMessage]
) -> list[ModelMessage]:
    """Inject the table of contents and user query into the prompt."""

    contents = ctx.deps.contents
    query = ctx.deps.query

    post_parts = []

    # Add system prompt from Langfuse
    post_parts.append(
        SystemPromptPart(
            content=langfuse_client.get_prompt(
                "trimmer/base", label=settings.env
            ).compile()
        )
    )

    # Add user content with table of contents and query
    post_parts.append(
        UserPromptPart(
            content=f"""Table of Contents (JSON):
{contents}

User Query:
{query}

Based on the table of contents above and the user's query, determine which page ranges should be included. Return the page ranges as a list of start-end pairs."""
        )
    )

    return messages + [ModelRequest(parts=post_parts)]


def init_trimmer(app: FastAPI):
    app.state.trimmer_agent = Agent(
        model=TRIMMER_LLM,
        deps_type=TrimmerDeps,
        output_type=TrimmerOutput,
        instrument=True,
        retries=3,
        history_processors=[inject_request_prompt],
    )


def get_trimmer(app: FastAPI) -> Agent:
    return app.state.trimmer_agent


Trimmer = Annotated[Agent[TrimmerDeps, TrimmerOutput], Depends(get_trimmer)]
