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
    PartDeltaEvent,
    PartStartEvent,
    TextPartDelta,
    ThinkingPartDelta,
    ToolCallPartDelta,
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


QUIZER_LLM = LLMS.GPT_5_MINI

quizer_agent = Agent(
    model=QUIZER_LLM,
    deps_type=QuizerDeps,
    instrument=True,
    output_type=QuizPatch,
    retries=3,
)


@quizer_agent.system_prompt()
async def create_base(ctx: RunContext[QuizerDeps]) -> str:
    prev_quiz_items = ctx.deps.prev_quiz_items
    prev_questions = [qi.get("question") for qi in prev_quiz_items]

    adds = "\n".join(ctx.deps.dynamic_config.adds)

    prompt = langfuse_client.get_prompt(
        "quizer/create_base", label=settings.env
    ).compile(
        prev_quiz_items=json.dumps(prev_questions),
        adds=adds,
    )
    return prompt


@quizer_agent.system_prompt()
async def difficulty(ctx: RunContext[QuizerDeps]) -> str:
    difficulty = ctx.deps.quiz.get("difficulty")  # beginner, intermediate, expert
    prompt = langfuse_client.get_prompt(
        f"quizer/{difficulty}", label=settings.env
    ).compile()

    extra_beginner = "\n".join(ctx.deps.dynamic_config.extraBeginner)
    if len(extra_beginner) > 0:
        extra_beginner_prompt = langfuse_client.get_prompt(
            f"quizer/extra_beginner", label=settings.env
        ).compile(questions=extra_beginner)
        prompt += extra_beginner_prompt

    extra_expert = "\n".join(ctx.deps.dynamic_config.extraExpert)
    if len(extra_expert) > 0:
        extra_expert_prompt = langfuse_client.get_prompt(
            f"quizer/extra_expert", label=settings.env
        ).compile(questions=extra_expert)
        prompt += extra_expert_prompt

    return prompt


@quizer_agent.system_prompt()
async def topic(ctx: RunContext[QuizerDeps]) -> str:
    prompt = ""

    more_on_topic = "\n".join(ctx.deps.dynamic_config.moreOnTopic)
    if len(more_on_topic) > 0:
        more_on_topic_prompt = langfuse_client.get_prompt(
            f"quizer/more_on_topic", label=settings.env
        ).compile(questions=more_on_topic)
        prompt += more_on_topic_prompt

    less_on_topic = "\n".join(ctx.deps.dynamic_config.lessOnTopic)
    if len(less_on_topic) > 0:
        less_on_topic_prompt = langfuse_client.get_prompt(
            f"quizer/less_on_topic", label=settings.env
        ).compile(questions=less_on_topic)
        prompt += less_on_topic_prompt

    return prompt


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
