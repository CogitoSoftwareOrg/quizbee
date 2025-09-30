import logging
from collections.abc import AsyncIterable
from pydantic_ai import Agent, RunContext
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
from lib.config import LLMS

from .models import QuizerDeps, QuizPatch
from .prompts import inject_request_prompt

QUIZER_LLM = LLMS.GPT_5_MINI

quizer_agent = Agent(
    model=QUIZER_LLM,
    deps_type=QuizerDeps,
    instrument=True,
    output_type=QuizPatch,
    history_processors=[inject_request_prompt],
    retries=3,
)


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
