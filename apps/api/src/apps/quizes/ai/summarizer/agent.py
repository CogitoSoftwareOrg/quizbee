from typing import Annotated
from fastapi import Depends, FastAPI, Request
from pydantic_ai import Agent, NativeOutput, RunContext
from pydantic_ai.messages import ModelMessage, ModelRequest, SystemPromptPart

from src.lib.config import LLMS, LLMSCosts
from src.lib.clients import langfuse_client
from src.lib.ai import build_pre_prompt, SummarizerDeps, AgentEnvelope
from src.lib.settings import settings


SUMMARIZER_LLM = LLMS.GPT_5_MINI
SUMMARIZER_COSTS = LLMSCosts.GPT_5_MINI
# SUMMARIZER_LLM = LLMS.GROK_4_FAST
# SUMMARIZER_COSTS = LLMSCosts.GROK_4_FAST


async def inject_request_prompt(
    ctx: RunContext[SummarizerDeps], messages: list[ModelMessage]
) -> list[ModelMessage]:
    pre_parts = await build_pre_prompt(
        ctx.deps.http, ctx.deps.quiz, ctx.deps.materials_context
    )

    post_parts = []
    post_parts.append(
        SystemPromptPart(
            content=langfuse_client.get_prompt(
                "summarizer/base", label=settings.env
            ).compile(quiz=ctx.deps.quiz_contents)
        )
    )
    return [ModelRequest(parts=pre_parts)] + messages + [ModelRequest(parts=post_parts)]


def init_summarizer(app: FastAPI):
    app.state.summarizer_agent = Agent(
        # instrument=True,
        model=SUMMARIZER_LLM,
        deps_type=SummarizerDeps,
        output_type=AgentEnvelope,
        retries=3,
        history_processors=[inject_request_prompt],
    )


def get_summarizer(request: Request) -> Agent:
    return request.app.state.summarizer_agent


Summarizer = Annotated[Agent[SummarizerDeps, AgentEnvelope], Depends(get_summarizer)]
