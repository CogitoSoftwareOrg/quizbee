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
    # SCIENCE = "science"
    # GEOGRAPHY = "geography"
    # LITERATURE = "literature"
    # MUSIC = "music"


@dataclass
class QuizGenConfig:
    negative_questions: list[str]
    additional_instructions: list[str]
    more_on_topic: list[str]
    less_on_topic: list[str]
    extra_beginner: list[str]
    extra_expert: list[str]


@dataclass
class QuizItemVariant:
    content: str
    is_correct: bool
    explanation: str


@dataclass
class QuizItem:
    id: str
    question: str
    variants: list[QuizItemVariant]
    order: int
    status: QuizItemStatus


@dataclass
class Choice:
    idx: int
    correct: bool
    item_id: str


@dataclass
class Attempt:
    id: str
    choices: list[Choice] = field(default_factory=list)


@dataclass(slots=True, kw_only=True)
class Quiz:
    id: str
    author_id: str
    material_ids: list[str]
    title: str
    length: int
    query: str
    difficulty: QuizDifficulty
    status: QuizStatus
    visibility: QuizVisibility
    total_materials: str
    avoid_repeat: bool
    items: list[QuizItem]

    gen_config: QuizGenConfig

    summary: str | None = None
    tags: list[str] | None = None
    category: QuizCategory | None = None

    @classmethod
    def create(cls, author_id: str) -> "Quiz":
        return cls(
            id=genID(),
            author_id=author_id,
            material_ids=[],
            title="",
            length=0,
            query="",
            difficulty=QuizDifficulty.INTERMEDIATE,
            gen_config=QuizGenConfig(
                negative_questions=[],
                additional_instructions=[],
                more_on_topic=[],
                less_on_topic=[],
                extra_beginner=[],
                extra_expert=[],
            ),
            total_materials="",
            avoid_repeat=False,
            items=[],
            visibility=QuizVisibility.PUBLIC,
            status=QuizStatus.DRAFT,
        )
