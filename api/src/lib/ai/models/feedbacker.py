from dataclasses import dataclass
from typing import Annotated, Literal
from pocketbase.models.dtos import Record
from pydantic import BaseModel, Field

from lib.clients import HTTPAsyncClient


@dataclass
class FeedbackerDeps:
    quiz: Record
    quiz_items: list[Record]
    quiz_attempt: Record
    http: HTTPAsyncClient


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
    mode: Literal["feedback"]
    feedback: Feedback
    additional: Additional
