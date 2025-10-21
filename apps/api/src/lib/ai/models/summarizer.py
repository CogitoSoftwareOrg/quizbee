from enum import StrEnum
from typing import Annotated, Literal
from pydantic import BaseModel, Field
from dataclasses import dataclass
from pocketbase.models.dtos import Record

from lib.clients import HTTPAsyncClient


@dataclass
class SummarizerDeps:
    materials_context: str
    quiz_contents: str
    http: HTTPAsyncClient
    quiz: Record


class QuizCategory(StrEnum):
    stem = "stem"
    general = "general"
    math = "math"
    history = "history"
    law = "law"
    language = "language"
    art = "art"
    popCulture = "popCulture"
    psychology = "psychology"


class Additional(BaseModel):
    quiz_title: Annotated[
        str, Field(title="Quiz Title", description="The title of the quiz.")
    ]
    quiz_slug: Annotated[
        str,
        Field(
            title="Quiz Slug",
            description="The slug of the quiz. 3 or 4 words. Formatting example: 'linear-algebra-basics'",
        ),
    ]
    quiz_tags: Annotated[
        list[str],
        Field(
            title="Quiz Tags",
            description="The topic tags of the quiz. More than 3 tags and less than 10 tags.",
            # min_length=3,
            # max_length=10,
        ),
    ]
    quiz_category: Annotated[
        QuizCategory,
        Field(
            title="Quiz Category",
            description="The category of the quiz.",
            default=QuizCategory.general,
        ),
    ]


class SummarizerOutput(BaseModel):
    mode: Literal["summary"]
    summary: str
    additional: Additional
