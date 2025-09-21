from dataclasses import dataclass
import logging
from pydantic_ai import (
    Agent,
    RunContext,
    StructuredDict,
)
from pocketbase import PocketBase
from typing import Annotated, Any
from pydantic import BaseModel, Field

from src.lib.clients import langfuse_client
from src.lib.settings import settings


@dataclass
class QuizerDeps:
    admin_pb: PocketBase


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
        Field(
            title="Quiz Items",
            description="An array of exactly 2 quiz items.",
            # min_length=5,
            # max_length=5,
        ),
    ]


def quiz_patch_output_schema(n_items: int):
    """
    Берём схему из Pydantic-модели Quiz, патчим ТОЛЬКО quiz_items,
    и делаем StructuredDict для output_type.
    """
    schema = QuizPatch.model_json_schema()

    qi = schema.get("properties", {}).get("quiz_items", {})
    qi["minItems"] = n_items
    qi["maxItems"] = n_items
    qi["description"] = f"An array of exactly {n_items} quiz items."

    return StructuredDict(
        schema, name="QuizPatch", description=f"QuizPatch with exactly {n_items} items"
    )


QUIZER_LLM = "gemini-2.5-flash-lite"

quizer_agent = Agent(
    model=QUIZER_LLM,
    deps_type=QuizerDeps,
    instrument=True,
    system_prompt="",
    history_processors=[],
    # output_type=QuizPatch,
)


@quizer_agent.system_prompt
async def system_prompt():
    return langfuse_client.get_prompt("create_quiz", label=settings.env).compile()
