import logging
from typing import Annotated
from fastapi import Depends, FastAPI, Request
from collections.abc import AsyncIterable
from pydantic_ai import Agent, ModelRetry, NativeOutput, PromptedOutput, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.messages import (
    AgentStreamEvent,
    FinalResultEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    TextPartDelta,
    ThinkingPartDelta,
    ToolCallPartDelta,
    PartStartEvent,
)
from src.lib.ai import QuizerDeps, QuizerOutput, AgentEnvelope
from src.lib.config import LLMS, LLMSCosts

from .prompts import inject_request_prompt

QUIZER_LLM = LLMS.GPT_5_MINI
QUIZER_COSTS = LLMSCosts.GPT_5_MINI
QUIZER_PRIORITY_COSTS = LLMSCosts.GPT_5_MINI_PRIORITY
# QUIZER_LLM = LLMS.GROK_4_FAST
# QUIZER_COSTS = LLMSCosts.GROK_4_FAST


def init_quizer(app: FastAPI):
    app.state.quizer_agent = Agent(
        # instrument=True,
        model=QUIZER_LLM,
        deps_type=QuizerDeps,
        output_type=AgentEnvelope,
        history_processors=[inject_request_prompt],
        retries=3,
    )


def get_quizer(request: Request) -> Agent:
    return request.app.state.quizer_agent


Quizer = Annotated[Agent[QuizerDeps, AgentEnvelope], Depends(get_quizer)]

# @quizer_agent.output_validator
# async def validate_out(ctx: RunContext[QuizerDeps], out: AgentEnvelope):
#     # если список outputs:
#     if out.data.mode == "quiz":
#         # if len(out.data.quiz_items) < 5:
#         #     raise ModelRetry("Нужно минимум 5 вопросов.")
#         for i, qi in enumerate(out.data.quiz_items):
#             if len(qi.answers) != 4:
#                 raise ModelRetry(f"Вопрос {i}: должно быть 4 ответа.")
#             if sum(a.correct for a in qi.answers) != 1:
#                 raise ModelRetry(f"Вопрос {i}: ровно один correct=True.")
#     return out


async def event_stream_handler(
    ctx: RunContext[QuizerDeps],
    event_stream: AsyncIterable[AgentStreamEvent],
):
    async for event in event_stream:
        if isinstance(event, PartStartEvent):
            logging.info(f"[Request] Starting part {event.index}: {event.part!r}")

        elif isinstance(event, PartDeltaEvent):
            if isinstance(event.delta, TextPartDelta):
                logging.info(
                    f"[Request] Part {event.index} text delta: {event.delta.content_delta!r}"
                )
            elif isinstance(event.delta, ThinkingPartDelta):
                logging.info(
                    f"[Request] Part {event.index} thinking delta: {event.delta.content_delta!r}"
                )
            elif isinstance(event.delta, ToolCallPartDelta):
                logging.info(
                    f"[Request] Part {event.index} args delta: {event.delta.args_delta}"
                )

        elif isinstance(event, FunctionToolCallEvent):
            logging.info(
                f"[Tools] LLM calls tool={event.part.tool_name!r} "
                f"args={event.part.args} (tool_call_id={event.part.tool_call_id!r})"
            )

        elif isinstance(event, FunctionToolResultEvent):
            logging.info(
                f"[Tools] Tool call {event.tool_call_id!r} returned => {event.result.content}"
            )

        elif isinstance(event, FinalResultEvent):
            logging.info(
                f"[Result] Model starts producing a final result (tool_name={event.tool_name})"
            )
