from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import ModelMessage, ModelRequest, SystemPromptPart, UserPromptPart
from langfuse import Langfuse

from .models import TrimmerDeps, TrimmerOutput
from src.lib.config import LLMS
from src.lib.settings import settings

TRIMMER_LLM = LLMS.GPT_5_NANO


def create_trimmer_agent(lf: Langfuse) -> Agent:
    """Create a trimmer agent with the given Langfuse client."""

    async def inject_request_prompt(
        ctx: RunContext[TrimmerDeps], messages: list[ModelMessage]
    ) -> list[ModelMessage]:
        """Inject the table of contents and user query into the prompt."""

        contents = ctx.deps.contents
        query = ctx.deps.query

        post_parts = []

        post_parts.append(
            SystemPromptPart(
                content=lf.get_prompt("trimmer/base", label=settings.env).compile()
            )
        )

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

    return Agent(
        model=TRIMMER_LLM,
        deps_type=TrimmerDeps,
        output_type=TrimmerOutput,
        instrument=True,
        retries=3,
        history_processors=[inject_request_prompt],
    )
