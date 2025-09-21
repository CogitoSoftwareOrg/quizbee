from dataclasses import dataclass
import logging
from pydantic_ai import (
    Agent,
    RunContext,
    StructuredDict,
)
from pocketbase import PocketBase
from typing import Annotated, Any
from pydantic import BaseModel, Field, create_model

from src.lib.clients import langfuse_client
from src.lib.settings import settings


@dataclass
class QuizerDeps:
    admin_pb: PocketBase
    quiz_id: str


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
        Field(title="Quiz Items", description="An array of exactly 2 quiz items."),
    ]


def make_quiz_patch_model(n_items: int):
    QuizItemsField = Annotated[
        list[QuizItem],
        Field(
            title="Quiz Items",
            description=f"An array of exactly {n_items} quiz items.",
            min_length=n_items,
            max_length=n_items,
        ),
    ]
    return create_model(
        f"QuizPatch_{n_items}",
        quiz_items=(QuizItemsField, ...),
        __base__=QuizPatch,
    )


QUIZER_LLM = "gemini-2.5-flash-lite"


quizer_agent = Agent(
    model=QUIZER_LLM,
    deps_type=QuizerDeps,
    instrument=True,
    system_prompt="",
    history_processors=[],
    output_type=QuizPatch,
    retries=3,
)


@quizer_agent.system_prompt
async def system_prompt(ctx: RunContext[QuizerDeps]):
    logging.info(
        f"System prompt for {ctx.deps.quiz_id} env: {settings.env} langfuse: {settings.langfuse_public_key}"
    )
    return langfuse_client.get_prompt("create_quiz", label=settings.env).compile()
