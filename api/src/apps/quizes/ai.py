from dataclasses import dataclass
import logging
import httpx
from langfuse.api import Model
from pocketbase.models.dtos import Record
from pydantic_ai import (
    Agent,
    RunContext,
    StructuredDict,
)
from pocketbase import PocketBase
from typing import Annotated, Any
from pydantic import BaseModel, Field, create_model
from pydantic_ai.messages import (
    ModelMessage,
    SystemPromptPart,
    UserPromptPart,
    ModelRequest,
)

from src.lib.clients import langfuse_client
from src.lib.settings import settings


@dataclass
class QuizerDeps:
    http: httpx.AsyncClient
    admin_pb: PocketBase
    quiz: Record
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


QUIZER_LLM = "gemini-2.5-flash-lite"


async def build_langfuse_messages(
    ctx: RunContext[QuizerDeps],
    messages: list[ModelMessage],
) -> list[ModelMessage]:
    materials = await load_materials_from_records(ctx.deps.http, ctx.deps.materials)
    materials = materials or "<no materials>"
    chat = langfuse_client.get_prompt(
        "create_quiz_patch", label=settings.env, type="chat"
    ).compile(
        materials=materials,
    )
    parts = []
    for chat_msg in chat:
        if chat_msg["role"] == "system":  # pyright: ignore[reportGeneralTypeIssues]
            parts.append(
                SystemPromptPart(
                    content=chat_msg[
                        "content"
                    ]  # pyright: ignore[reportGeneralTypeIssues]
                )
            )
        else:
            parts.append(
                UserPromptPart(
                    content=chat_msg[
                        "content"
                    ]  # pyright: ignore[reportGeneralTypeIssues]
                )
            )

    return [ModelRequest(parts=parts)] + messages


quizer_agent = Agent(
    model=QUIZER_LLM,
    deps_type=QuizerDeps,
    instrument=True,
    history_processors=[build_langfuse_messages],
    output_type=QuizPatch,
    retries=3,
)


async def load_materials_from_records(
    http: httpx.AsyncClient, records: list[Record]
) -> str:
    contents = []
    for m in records:
        mid = m.get("id")
        col = m.get("collectionName")
        fname = m.get("file")
        url = f"{settings.pb_url}/api/files/{col}/{mid}/{fname}"
        resp = await http.get(url)
        resp.raise_for_status()
        contents.append(resp.text)
    materials = "\n\n".join(contents)
    return materials
