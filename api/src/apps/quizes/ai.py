import json
from dataclasses import dataclass
import logging
import httpx
from pocketbase.models.dtos import Record
from pydantic_ai import Agent, RunContext
from pocketbase import PocketBase
from typing import Annotated
from pydantic import BaseModel, Field, create_model
from pydantic_ai.messages import (
    DocumentUrl,
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


QUIZER_LLM = LLMS.GROK_4_FAST

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


async def materials_to_ai_docs(
    http: httpx.AsyncClient, records: list[Record], force_download: bool = False
) -> list[DocumentUrl]:
    urls = []
    for m in records:
        mid = m.get("id")
        col = m.get("collectionName")
        fname = m.get("file")
        url = f"{settings.pb_url}/api/files/{col}/{mid}/{fname}"
        urls.append(url)
        # resp = await http.get(url)
        # resp.raise_for_status()
        # contents.append(resp.text)

    return [DocumentUrl(url=url, force_download=force_download) for url in urls]
