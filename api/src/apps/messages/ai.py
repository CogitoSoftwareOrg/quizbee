from pydantic_ai import (
    Agent,
    NativeOutput,
    PromptedOutput,
    RunContext,
)

from pydantic_ai.messages import ModelMessage, ModelRequest, SystemPromptPart

from lib.ai import ExplainerDeps, build_pre_prompt, ExplainerOutput, AgentEnvelope
from lib.clients import langfuse_client
from lib.config import LLMS
from lib.settings import settings

EXPLAINER_LLM = LLMS.GPT_5_MINI


async def inject_system_prompt(
    ctx: RunContext[ExplainerDeps], messages: list[ModelMessage]
) -> list[ModelMessage]:
    quiz = ctx.deps.quiz
    current_item = ctx.deps.current_item
    decision = ctx.deps.current_decision
    question = current_item.get("question", "")
    answers = current_item.get("answers", "")

    pre_parts = await build_pre_prompt(ctx.deps.http, quiz)

    pre_parts.append(
        SystemPromptPart(
            content=langfuse_client.get_prompt(
                "explainer/base", label=settings.env
            ).compile(question=question, answers=answers, decision=decision)
        )
    )

    return [ModelRequest(parts=pre_parts)] + messages


explainer_agent = Agent(
    model=EXPLAINER_LLM,
    deps_type=ExplainerDeps,
    instrument=True,
    history_processors=[inject_system_prompt],
    output_type=AgentEnvelope,
)
