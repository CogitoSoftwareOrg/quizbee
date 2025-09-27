import json
from dataclasses import dataclass
import logging
import httpx
from pocketbase.models.dtos import Record
from pydantic_ai import Agent, RunContext
from pocketbase import PocketBase
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
class QuizerDeps:
    http: httpx.AsyncClient
    admin_pb: PocketBase
    quiz: Record
    prev_quiz_items: list[Record]
    materials: list[Record]


class WrongAnswer(BaseModel):
    answer: Annotated[
        str, Field(title="Wrong Answer", description="A wrong answer option.")
    ]
    explanation: Annotated[
        str,
        Field(
            title="Wrong Answer Explanation", description="Why this answer is wrong."
        ),
    ]


class RightAnswer(BaseModel):
    answer: Annotated[
        str, Field(title="Right Answer", description="The correct answer.")
    ]
    explanation: Annotated[
        str,
        Field(
            title="Right Answer Explanation", description="Why this answer is correct."
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
async def system_prompt(ctx: RunContext[QuizerDeps]) -> str:
    prev_quiz_items = ctx.deps.prev_quiz_items
    prev_questions = [qi.get("question") for qi in prev_quiz_items]
    prompt = langfuse_client.get_prompt("create_quiz", label=settings.env).compile(
        prev_quiz_items=json.dumps(prev_questions)
    )
    return prompt


async def event_stream_handler(
    ctx: RunContext[QuizerDeps],
    event_stream: AsyncIterable[AgentStreamEvent],
):
    pb = ctx.deps.admin_pb

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
