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
        list[str], Field(title="Quiz Tags", description="The topic tags of the quiz.")
    ]


class SummarizerOutput(BaseModel):
    mode: Literal["summary"]
    summary: str
    additional: Additional
