import json
from dataclasses import dataclass, field
import logging
from pocketbase.models.dtos import Record
from pydantic_ai import Agent, RunContext
from typing import Annotated, AsyncIterable
from pydantic import BaseModel, Field, create_model
from pydantic_ai.messages import (
    AgentStreamEvent,
    FinalResultEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    ModelMessage,
    ModelRequest,
    PartDeltaEvent,
    PartStartEvent,
    SystemPromptPart,
    TextPartDelta,
    ThinkingPartDelta,
    ToolCallPartDelta,
    UserPromptPart,
)

from src.lib.clients import langfuse_client
from src.lib.config import LLMS
from src.lib.settings import settings


@dataclass
class DynamicConfig:
    adds: list[str] = field(default_factory=list)
    moreOnTopic: list[str] = field(default_factory=list)
    lessOnTopic: list[str] = field(default_factory=list)
    extraBeginner: list[str] = field(default_factory=list)
    extraExpert: list[str] = field(default_factory=list)


@dataclass
class QuizerDeps:
    quiz: Record
    dynamic_config: DynamicConfig
    prev_quiz_items: list[Record]
    materials: list[Record]
    materials_context: str


class WrongAnswer(BaseModel):
    answer: Annotated[
        str, Field(title="Wrong Answer", description="A wrong answer option.")
    ]
    explanation: Annotated[
        str,
        Field(
            title="Wrong Answer Explanation",
            description="Why this answer is wrong.",
            min_length=10,
        ),
    ]


class RightAnswer(BaseModel):
    answer: Annotated[
        str, Field(title="Right Answer", description="The correct answer.")
    ]
    explanation: Annotated[
        str,
        Field(
            title="Right Answer Explanation",
            description="Why this answer is correct.",
            min_length=10,
        ),
    ]


class QuizItem(BaseModel):
    question: Annotated[
        str, Field(title="Question", description="The quiz question text.")
    ]
    right_answer: Annotated[
        RightAnswer,
        Field(title="Right Answer", description="Correct answer with explanation."),
    ]
    wrong_answers: Annotated[
        list[WrongAnswer],
        Field(
            title="Wrong Answers",
            description="Exactly 3 wrong answers with explanations.",
            min_length=3,
            max_length=3,
        ),
    ]


class QuizPatch(BaseModel):
    quiz_items: Annotated[
        list[QuizItem],
        Field(title="Quiz Items", description="An array of quiz items."),
    ]


def make_quiz_patch_model(n_items: int):
    QuizItemsField = Annotated[
        list[QuizItem],
        Field(
            title="Quiz Items",
            description=f"An array of exactly {n_items} quiz items.",
            # min_length=n_items,
            max_length=n_items,
        ),
    ]
    return create_model(
        f"QuizPatch_{n_items}",
        quiz_items=(QuizItemsField, []),
        __base__=QuizPatch,
    )


def inject_request_prompt(
    ctx: RunContext[QuizerDeps], messages: list[ModelMessage]
) -> list[ModelMessage]:
    prev_quiz_items = ctx.deps.prev_quiz_items
    difficulty = ctx.deps.quiz.get("difficulty")
    materials_context = ctx.deps.materials_context
    adds = "\n".join(ctx.deps.dynamic_config.adds)
    extra_beginner = "\n".join(ctx.deps.dynamic_config.extraBeginner)
    extra_expert = "\n".join(ctx.deps.dynamic_config.extraExpert)
    more_on_topic = "\n".join(ctx.deps.dynamic_config.moreOnTopic)
    less_on_topic = "\n".join(ctx.deps.dynamic_config.lessOnTopic)

    parts = []

    # SYSTEM PARTS
    parts.append(
        SystemPromptPart(
            content=langfuse_client.get_prompt(
                "quizer/base", label=settings.env
            ).compile(
                prev_quiz_items=json.dumps(prev_quiz_items),
            )
        )
    )

    parts.append(
        SystemPromptPart(
            content=langfuse_client.get_prompt(
                f"quizer/{difficulty}", label=settings.env
            ).compile()
        )
    )

    if len(extra_beginner) > 0:
        parts.append(
            SystemPromptPart(
                content=langfuse_client.get_prompt(
                    "quizer/extra_beginner", label=settings.env
                ).compile(questions=extra_beginner)
            )
        )
    if len(extra_expert) > 0:
        parts.append(
            SystemPromptPart(
                content=langfuse_client.get_prompt(
                    "quizer/extra_expert", label=settings.env
                ).compile(questions=extra_expert)
            )
        )
    if len(more_on_topic) > 0:
        parts.append(
            SystemPromptPart(
                content=langfuse_client.get_prompt(
                    "quizer/more_on_topic", label=settings.env
                ).compile(questions=more_on_topic)
            )
        )
    if len(less_on_topic) > 0:
        parts.append(
            SystemPromptPart(
                content=langfuse_client.get_prompt(
                    "quizer/less_on_topic", label=settings.env
                ).compile(questions=less_on_topic)
            )
        )

    # USER PARTS
    if materials_context:
        parts.append(
            UserPromptPart(
                content=langfuse_client.get_prompt(
                    "quizer/materials", label=settings.env
                ).compile(
                    materials=materials_context,
                )
            )
        )
    if len(adds) > 0:
        parts.append(
            UserPromptPart(
                content=langfuse_client.get_prompt(
                    "quizer/adds", label=settings.env
                ).compile(
                    adds=adds,
                )
            )
        )

    return [ModelRequest(parts=parts)] + messages


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
