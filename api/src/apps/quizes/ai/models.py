from dataclasses import dataclass, field
from typing import Annotated
from pydantic import BaseModel, Field
from pocketbase.models.dtos import Record
from pydantic import create_model


@dataclass
class DynamicConfig:
    adds: list[str] = field(default_factory=list)
    moreOnTopic: list[str] = field(default_factory=list)
    lessOnTopic: list[str] = field(default_factory=list)
    extraBeginner: list[str] = field(default_factory=list)
    extraExpert: list[str] = field(default_factory=list)


@dataclass
class QuizerDeps:
    quiz: Record
    dynamic_config: DynamicConfig
    prev_quiz_items: list[Record]
    materials: list[Record]
    materials_context: str


class WrongAnswer(BaseModel):
    answer: Annotated[
        str, Field(title="Wrong Answer", description="A wrong answer option.")
    ]
    explanation: Annotated[
        str,
        Field(
            title="Wrong Answer Explanation",
            description="Why this answer is wrong.",
            min_length=10,
        ),
    ]


class RightAnswer(BaseModel):
    answer: Annotated[
        str, Field(title="Right Answer", description="The correct answer.")
    ]
    explanation: Annotated[
        str,
        Field(
            title="Right Answer Explanation",
            description="Why this answer is correct.",
            min_length=10,
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
        Field(title="Quiz Items", description="An array of quiz items."),
    ]


def make_quiz_patch_model(n_items: int):
    QuizItemsField = Annotated[
        list[QuizItem],
        Field(
            title="Quiz Items",
            description=f"An array of exactly {n_items} quiz items.",
            # min_length=n_items,
            max_length=n_items + 10,
        ),
    ]
    return create_model(
        f"QuizPatch_{n_items}",
        quiz_items=(QuizItemsField, []),
        __base__=QuizPatch,
    )
