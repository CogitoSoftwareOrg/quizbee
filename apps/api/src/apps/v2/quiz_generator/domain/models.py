from dataclasses import dataclass, field
from enum import StrEnum

from src.lib.utils import genID


class QuizItemStatus(StrEnum):
    GENERATED = "generated"
    GENERATING = "generating"
    FINAL = "final"
    BLANK = "blank"
    FAILED = "failed"


class QuizDifficulty(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"


class QuizStatus(StrEnum):
    DRAFT = "draft"
    CREATING = "creating"
    FINAL = "final"
    PREPARING = "preparing"
    ANSWERED = "answered"


class QuizVisibility(StrEnum):
    LINK = "link"
    PUBLIC = "public"


class QuizCategory(StrEnum):
    GENERAL = "general"
    MATH = "math"
    HISTORY = "history"
    LAW = "law"
    LANGUAGE = "language"
    ART = "art"
    PSYCHOLOGY = "psychology"
    POP_CULTURE = "pop_culture"
    STEM = "stem"


@dataclass(slots=True, kw_only=True)
class QuizGenConfig:
    negative_questions: list[str] = field(default_factory=list)
    additional_instructions: list[str] = field(default_factory=list)
    more_on_topic: list[str] = field(default_factory=list)
    less_on_topic: list[str] = field(default_factory=list)
    extra_beginner: list[str] = field(default_factory=list)
    extra_expert: list[str] = field(default_factory=list)


@dataclass(slots=True, kw_only=True)
class QuizItemVariant:
    content: str
    is_correct: bool
    explanation: str


@dataclass(slots=True, kw_only=True)
class QuizItem:
    id: str
    question: str
    variants: list[QuizItemVariant]
    order: int
    status: QuizItemStatus


@dataclass(slots=True, kw_only=True)
class Choice:
    idx: int
    correct: bool
    item_id: str


@dataclass(slots=True, kw_only=True)
class Attempt:
    id: str = field(default_factory=genID)
    choices: list[Choice] = field(default_factory=list)
    quiz_id: str
    user_id: str

    @classmethod
    def create(cls, quiz_id: str, user_id: str):
        return cls(
            quiz_id=quiz_id,
            user_id=user_id,
        )


@dataclass(slots=True, kw_only=True)
class Quiz:
    author_id: str
    title: str
    query: str
    id: str = field(default_factory=genID)
    material_ids: list[str] = field(default_factory=list)
    length: int = 0
    difficulty: QuizDifficulty
    visibility: QuizVisibility = QuizVisibility.PUBLIC
    status: QuizStatus = QuizStatus.DRAFT
    material_content: str = ""
    avoid_repeat: bool = False
    items: list[QuizItem] = field(default_factory=list)

    gen_config: QuizGenConfig = field(default_factory=QuizGenConfig)

    summary: str | None = None
    tags: list[str] | None = None
    category: QuizCategory | None = None

    @classmethod
    def create(
        cls, author_id: str, title: str, query: str, difficulty: QuizDifficulty
    ) -> "Quiz":
        return cls(
            author_id=author_id,
            title=title,
            query=query,
            difficulty=difficulty,
        )
