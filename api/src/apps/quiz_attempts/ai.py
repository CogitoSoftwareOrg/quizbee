from dataclasses import dataclass
from typing import Annotated
from pocketbase.models.dtos import Record
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    SystemPromptPart,
    UserPromptPart,
)

from lib.settings import settings
from lib.clients.langfuse import langfuse_client
from lib.config import LLMS


@dataclass
class FeedbackerDeps:
    quiz: Record
    quiz_items: list[Record]
    quiz_attempt: Record
    materials_context: str


class Additional(BaseModel):
    quiz_title: Annotated[
        str,
        Field(
            title="Quiz Title",
            description="The title of the quiz.",
        ),
    ]
    quiz_slug: Annotated[
        str,
        Field(
            title="Quiz Slug",
            description="The slug of the quiz.",
        ),
    ]
    quiz_tags: Annotated[
        list[str],
        Field(
            title="Quiz Tags",
            description="The topic tags of the quiz.",
            min_length=2,
            max_length=5,
        ),
    ]


class Feedback(BaseModel):
    overview: Annotated[
        str,
        Field(
            title="Small Overview",
            description="A brief overview of the quiz attempt and user results.",
        ),
    ]
    problem_topics: Annotated[
        list[str],
        Field(
            title="Problem Topics",
            description="A list of problem topics that the user struggled with.",
            max_length=3,
        ),
    ]
    uncovered_topics: Annotated[
        list[str],
        Field(
            title="Uncovered Topics",
            description="A list of topics that are presented in materials but not covered in the quiz.",
            max_length=3,
        ),
    ]


class FeedbackerOutput(BaseModel):
    feedback: Feedback
    additional: Additional


def inject_request_prompt(
    ctx: RunContext[FeedbackerDeps], messages: list[ModelMessage]
) -> list[ModelMessage]:
    quiz = ctx.deps.quiz
    quiz_attempt = ctx.deps.quiz_attempt
    quiz_items = ctx.deps.quiz_items

    quiz_content = "\n".join(
        [
            f"{i+1}. {qi.get('question')}: {qi.get('answers')}"
            for i, qi in enumerate(quiz_items)
        ]
    )
    choices = quiz_attempt.get("choices", [])
    wrong_item_ids = set(
        [c.get("itemId") for c in choices if c.get("correct") is False]
    )
    correct_item_ids = set(
        [c.get("itemId") for c in choices if c.get("correct") is True]
    )

    wrong_items_content = "\n".join(
        [f"{qi.get('question')}" for qi in quiz_items if qi.get("id") in wrong_item_ids]
    )
    correct_items_content = "\n".join(
        [
            f"{qi.get('question')}"
            for qi in quiz_items
            if qi.get("id") in correct_item_ids
        ]
    )
    materials_context = ctx.deps.materials_context

    parts = []

    # SYSTEM PARTS
    parts.append(
        SystemPromptPart(
            content=langfuse_client.get_prompt(
                "feedbacker/base", label=settings.env
            ).compile(
                quiz_content=quiz_content,
                correct_answers=correct_items_content,
                wrong_answers=wrong_items_content,
            )
        )
    )
    # USER PARTS
    if materials_context:
        parts.append(
            UserPromptPart(
                content=langfuse_client.get_prompt(
                    "feedbacker/materials", label=settings.env
                ).compile(
                    materials=materials_context,
                )
            )
        )

    return [ModelRequest(parts=parts)] + messages


FEEDBACKER_LLM = LLMS.GPT_5_MINI

feedbacker_agent = Agent(
    model=FEEDBACKER_LLM,
    deps_type=FeedbackerDeps,
    instrument=True,
    output_type=FeedbackerOutput,
    history_processors=[inject_request_prompt],
    retries=3,
)
