from dataclasses import dataclass
from typing import Annotated
from pocketbase.models.dtos import Record
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from lib.settings import settings
from lib.clients.langfuse import langfuse_client
from lib.config import LLMS


@dataclass
class FeedbackerDeps:
    quiz: Record
    quiz_items: list[Record]
    quiz_attempt: Record


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
        ),
    ]
    uncovered_topics: Annotated[
        list[str],
        Field(
            title="Uncovered Topics",
            description="A list of topics that are presented in materials but not covered in the quiz.",
        ),
    ]


class FeedbackerOutput(BaseModel):
    feedback: Feedback
    additional: Additional


FEEDBACKER_LLM = LLMS.GROK_4_FAST

feedbacker_agent = Agent(
    model=FEEDBACKER_LLM,
    deps_type=FeedbackerDeps,
    instrument=True,
    output_type=FeedbackerOutput,
    retries=3,
)


@feedbacker_agent.system_prompt()
async def system_prompt(ctx: RunContext[FeedbackerDeps]) -> str:
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

    prompt = langfuse_client.get_prompt("create_feedback", label=settings.env).compile(
        quiz_content=quiz_content,
        correct_answers=correct_items_content,
        wrong_answers=wrong_items_content,
    )
    return prompt
