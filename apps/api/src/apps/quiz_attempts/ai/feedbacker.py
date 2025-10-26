from typing import Annotated
from fastapi import Depends, FastAPI
from fastapi.requests import Request
from pydantic_ai import Agent, NativeOutput, PromptedOutput, RunContext
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    SystemPromptPart,
)


from src.lib.ai import FeedbackerDeps, build_pre_prompt, FeedbackerOutput, AgentEnvelope
from src.lib.settings import settings
from src.lib.clients import langfuse_client
from src.lib.config import LLMS, LLMSCosts


async def inject_request_prompt(
    ctx: RunContext[FeedbackerDeps], messages: list[ModelMessage]
) -> list[ModelMessage]:
    quiz = ctx.deps.quiz
    quiz_attempt = ctx.deps.quiz_attempt
    quiz_items = ctx.deps.quiz_items

    pre_parts = await build_pre_prompt(ctx.deps.http, ctx.deps.quiz)

    quiz_content = "\n".join(
        [
            f"{i+1}. {qi.get('question')}: {qi.get('answers')}"
            for i, qi in enumerate(quiz_items)
        ]
    )
    choices = quiz_attempt.get("choices", [])
    wrong_item_ids = set(
        [c.get("itemId") for c in choices if c.get("correct") is False]
    )
    correct_item_ids = set(
        [c.get("itemId") for c in choices if c.get("correct") is True]
    )

    wrong_items_content = "\n".join(
        [f"{qi.get('question')}" for qi in quiz_items if qi.get("id") in wrong_item_ids]
    )
    correct_items_content = "\n".join(
        [
            f"{qi.get('question')}"
            for qi in quiz_items
            if qi.get("id") in correct_item_ids
        ]
    )

    parts = []

    # SYSTEM PARTS
    parts.append(
        SystemPromptPart(
            content=langfuse_client.get_prompt(
                "feedbacker/base", label=settings.env
            ).compile(
                quiz_content=quiz_content,
                correct_answers=correct_items_content,
                wrong_answers=wrong_items_content,
            )
        )
    )

    return [ModelRequest(parts=pre_parts)] + messages + [ModelRequest(parts=parts)]


FEEDBACKER_LLM = LLMS.GPT_5_MINI
FEEDBACKER_COSTS = LLMSCosts.GPT_5_MINI
# FEEDBACKER_LLM = LLMS.GROK_4_FAST
# FEEDBACKER_COSTS = LLMSCosts.GROK_4_FAST


def init_feedbacker(app: FastAPI):
    app.state.feedbacker_agent = Agent(
        # instrument=True,
        model=FEEDBACKER_LLM,
        deps_type=FeedbackerDeps,
        output_type=AgentEnvelope,
        history_processors=[inject_request_prompt],
        retries=3,
    )


def get_feedbacker(request: Request) -> Agent:
    return request.app.state.feedbacker_agent


Feedbacker = Annotated[Agent[FeedbackerDeps, AgentEnvelope], Depends(get_feedbacker)]
