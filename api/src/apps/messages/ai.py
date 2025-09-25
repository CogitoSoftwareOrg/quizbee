from dataclasses import dataclass
import logging
import json
from collections.abc import AsyncIterable
from typing import Any
from pydantic import BaseModel
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
from pocketbase.models.options import CommonOptions
from pocketbase import PocketBase

from src.lib.clients import langfuse_client
from src.lib.config import LLMS
from src.lib.settings import settings
from src.apps.billing import UsageCollector


@dataclass
class ExplainerDeps:
    admin_pb: PocketBase
    quiz_attempt: Record
    quiz: Record
    quiz_items: list[Record]
    current_item: Record
    current_decision: Any


EXPLAINER_LLM = LLMS.GROK_4_FAST


def inject_system_prompt(
    ctx: RunContext[ExplainerDeps], messages: list[ModelMessage]
) -> list[ModelMessage]:
    current_item = ctx.deps.current_item
    decision = ctx.deps.current_decision
    question = current_item.get("question", "")
    answers = current_item.get("answers", "")

    sys_part = SystemPromptPart(
        content=langfuse_client.get_prompt("explain_quiz", label=settings.env).compile(
            question=question, answers=answers, decision=decision
        )
    )

    for msg in messages:
        if isinstance(msg, ModelRequest):
            msg.parts = [p for p in msg.parts if not isinstance(p, SystemPromptPart)]
            msg.parts.insert(0, sys_part)  # pyright: ignore[reportArgumentType]
            return messages

    return [ModelRequest(parts=[sys_part])] + messages


explainer_agent = Agent(
    model=EXPLAINER_LLM,
    deps_type=ExplainerDeps,
    instrument=True,
    history_processors=[inject_system_prompt],
)
