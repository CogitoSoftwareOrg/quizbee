from dataclasses import dataclass
import logging
from collections.abc import AsyncIterable
from pydantic_ai import (
    Agent,
    RunContext,
)
from pydantic_ai.messages import (
    AgentStreamEvent,
    FinalResultEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartStartEvent,
    TextPartDelta,
    ThinkingPartDelta,
    ToolCallPartDelta,
)
from pydantic_ai.messages import ModelMessage, ModelRequest, SystemPromptPart
from pocketbase.models.dtos import Record
from pocketbase import PocketBase

from src.lib.clients import langfuse_client
from src.lib.settings import settings


@dataclass
class QuizerDeps:
    admin_pb: PocketBase


QUIZER_LLM = "gemini-2.5-flash-lite"


def inject_system_prompt(
    ctx: RunContext[QuizerDeps], messages: list[ModelMessage]
) -> list[ModelMessage]:
    sys_part = langfuse_client.get_prompt("create_quiz", label=settings.env).compile()

    for msg in messages:
        if isinstance(msg, ModelRequest):
            msg.parts = [p for p in msg.parts if not isinstance(p, SystemPromptPart)]
            msg.parts.insert(0, sys_part)  # type: ignore
            return messages

    return [ModelRequest(parts=[sys_part])] + messages  # type: ignore


quizer_agent = Agent(
    model=QUIZER_LLM,
    deps_type=QuizerDeps,
    instrument=True,
    system_prompt="",
    history_processors=[inject_system_prompt],
    output_type=str,
)
