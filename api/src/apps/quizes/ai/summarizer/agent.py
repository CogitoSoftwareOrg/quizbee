from pydantic_ai import Agent, NativeOutput, RunContext
from pydantic_ai.messages import ModelMessage, ModelRequest, SystemPromptPart

from lib.config import LLMS
from lib.clients import langfuse_client
from lib.ai import build_pre_prompt, SummarizerDeps, AgentEnvelope
from lib.settings import settings


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


summarizer_agent = Agent(
    model=LLMS.GPT_5_MINI,
    deps_type=SummarizerDeps,
    output_type=AgentEnvelope,
    instrument=True,
    retries=3,
    history_processors=[inject_request_prompt],
)
