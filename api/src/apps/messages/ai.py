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
    UserPromptPart,
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
    materials_context: str
    current_item: Record
    current_decision: Any


EXPLAINER_LLM = LLMS.GPT_5_MINI


def inject_system_prompt(
    ctx: RunContext[ExplainerDeps], messages: list[ModelMessage]
) -> list[ModelMessage]:
    materials_context = ctx.deps.materials_context
    current_item = ctx.deps.current_item
    decision = ctx.deps.current_decision
    question = current_item.get("question", "")
    answers = current_item.get("answers", "")

    parts = []

    parts.append(
        SystemPromptPart(
            content=langfuse_client.get_prompt(
                "explainer/base", label=settings.env
            ).compile(question=question, answers=answers, decision=decision)
        )
    )

    if len(materials_context) > 0:
        parts.append(
            UserPromptPart(
                content=langfuse_client.get_prompt(
                    "explainer/materials", label=settings.env
                ).compile(materials=materials_context)
            )
        )

    return [ModelRequest(parts=parts)] + messages


explainer_agent = Agent(
    model=EXPLAINER_LLM,
    deps_type=ExplainerDeps,
    instrument=True,
    history_processors=[inject_system_prompt],
)
