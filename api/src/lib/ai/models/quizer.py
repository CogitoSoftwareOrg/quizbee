from dataclasses import dataclass, field
from typing import Annotated, Literal
from pydantic import BaseModel, Field
from pocketbase.models.dtos import Record

from lib.clients import HTTPAsyncClient


class DynamicConfig(BaseModel):
    negativeQuestions: list[str] = Field(default_factory=list)
    adds: list[str] = Field(default_factory=list)
    moreOnTopic: list[str] = Field(default_factory=list)
    lessOnTopic: list[str] = Field(default_factory=list)
    extraBeginner: list[str] = Field(default_factory=list)
    extraExpert: list[str] = Field(default_factory=list)


@dataclass
class QuizerDeps:
    http: HTTPAsyncClient
    quiz: Record
    prev_quiz_items: list[Record]
    materials: list[Record]


class Answer(BaseModel):
    answer: Annotated[str, Field(title="Answer", description="The answer text.")]
    explanation: Annotated[
        str, Field(title="Answer Explanation", description="The explanation text.")
    ]
    correct: Annotated[
        bool, Field(title="Correct", description="Whether the answer is correct.")
    ]


class QuizItem(BaseModel):
    question: Annotated[
        str, Field(title="Question", description="The quiz question text.")
    ]
    answers: Annotated[
        list[Answer],
        Field(
            title="Answers",
            description="The answers to the question. 4 in total with ONLY one correct answer.",
            min_length=4,
            max_length=4,
        ),
    ]


class QuizerOutput(BaseModel):
    mode: Literal["quiz"]
    quiz_items: Annotated[
        list[QuizItem],
        Field(
            title="Quiz Items",
            description="An array of exactly 5 quiz items.",
            # min_length=5,
            max_length=6,
        ),
    ]
