from dataclasses import dataclass, field
from enum import StrEnum

from src.lib.utils import genID

from .constants import PATCH_LIMIT
from .refs import MaterialRef


class QuizItemStatus(StrEnum):
    BLANK = "blank"
    GENERATED = "generated"
    GENERATING = "generating"
    FAILED = "failed"
    FINAL = "final"


class QuizDifficulty(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"


class QuizStatus(StrEnum):
    DRAFT = "draft"
    PREPARING = "preparing"
    CREATING = "creating"
    ANSWERED = "answered"
    FINAL = "final"


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
    POP_CULTURE = "popCulture"
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

    fresh_generated: bool = False

    def to_generating(self) -> None:
        if self.status not in {QuizItemStatus.BLANK}:
            raise ValueError("Item is not in blank status for generating")
        self.status = QuizItemStatus.GENERATING

    def regenerate(self) -> None:
        # Reset all non-FINAL items to BLANK for regeneration
        # This handles GENERATING, FAILED, GENERATED, and BLANK items
        if self.status not in {QuizItemStatus.FINAL}:
            self.status = QuizItemStatus.BLANK
            self.fresh_generated = False

    def to_failed(self) -> None:
        if self.status not in {QuizItemStatus.GENERATING}:
            raise ValueError("Item is not in generating status for failing")
        self.status = QuizItemStatus.FAILED

    def to_generated(self, question: str, variants: list[QuizItemVariant]) -> None:
        if self.status not in {QuizItemStatus.GENERATING}:
            raise ValueError("Item is not in generating status for generating")

        self.fresh_generated = True
        self.status = QuizItemStatus.GENERATED
        self.question = question
        self.variants = variants


@dataclass(slots=True, kw_only=True)
class Quiz:
    generation: int = 0
    author_id: str
    title: str
    query: str
    id: str = field(default_factory=genID)
    materials: list[MaterialRef] = field(default_factory=list)
    length: int = 0
    difficulty: QuizDifficulty
    visibility: QuizVisibility = QuizVisibility.PUBLIC
    status: QuizStatus = QuizStatus.DRAFT
    material_content: str = ""
    avoid_repeat: bool = False
    items: list[QuizItem] = field(default_factory=list)
    cluster_vectors: list[list[float]] = field(default_factory=list)

    gen_config: QuizGenConfig = field(default_factory=QuizGenConfig)

    summary: str | None = None
    tags: list[str] | None = None
    category: QuizCategory | None = None
    slug: str | None = None

    need_build_material_content: bool = False

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

    def to_preparing(self) -> None:
        if self.status != QuizStatus.DRAFT:
            raise ValueError("Quiz is not in draft status for preparing")
        self.status = QuizStatus.PREPARING
        if len(self.materials) > 0:
            self.request_build_material_content()

    def to_creating(self) -> None:
        if self.status != QuizStatus.PREPARING:
            raise ValueError("Quiz is not in preparing status for creating")
        self.status = QuizStatus.CREATING

    def to_answered(self) -> None:
        if self.status not in {QuizStatus.CREATING, QuizStatus.ANSWERED}:
            raise ValueError("Quiz is not in creating status for answered")
        for item in self.items:
            if item.status not in {QuizItemStatus.FINAL}:
                raise ValueError("Quiz can't be answered if some items are not final")
        self.status = QuizStatus.ANSWERED

    def to_final(self) -> None:
        if self.status != QuizStatus.ANSWERED:
            raise ValueError("Quiz is not in answered status for final")
        self.status = QuizStatus.FINAL

    def set_material_content(self, content: str):
        self.material_content = content
        self.need_build_material_content = False

    def set_cluster_vectors(self, vectors: list[list[float]]):
        if len(vectors) != self.length:
            raise ValueError("Cluster vectors length mismatch")
        self.cluster_vectors = vectors

    def request_build_material_content(self) -> None:
        self.need_build_material_content = True

    def set_summary(self, summary: str):
        self.summary = summary

    def set_title(self, title: str):
        self.title = title

    def set_tags(self, tags: list[str]):
        self.tags = tags

    def set_category(self, category: QuizCategory):
        self.category = category

    def set_slug(self, slug: str):
        self.slug = f"{slug}-{self.id[:6]}"

    def merge_similar_quizes(self, quizes: list["Quiz"]):
        questions = list(
            set([q.question for quiz in quizes for q in quiz.items if q.question])
        )
        self.add_negative_questions(questions)

    def add_negative_questions(self, questions: list[str]):
        self.gen_config.negative_questions.extend(questions)

    def increment_generation(self) -> None:
        for item in self.items:
            item.regenerate()
        self.generation += 1

    def get_final_items(self) -> list[QuizItem]:
        return [item for item in self.items if item.status == QuizItemStatus.FINAL]

    def generate_patch(self) -> list[QuizItem]:
        ready_items = [
            item for item in self.items if item.status == QuizItemStatus.BLANK
        ][:PATCH_LIMIT]
        for item in ready_items:
            item.to_generating()
        return ready_items

    def generating_items(self) -> list[QuizItem]:
        return [
            item for item in self.items if item.status in {QuizItemStatus.GENERATING}
        ]

    def fresh_generated_items(self) -> list[QuizItem]:
        return [item for item in self.items if item.fresh_generated]

    def prev_items(self) -> list[QuizItem]:
        return [
            item
            for item in self.items
            if item.status in {QuizItemStatus.FINAL, QuizItemStatus.GENERATED}
        ]

    def fail(self):
        # Only fail items that are currently generating
        # Other items (BLANK, FINAL, GENERATED, FAILED) should remain unchanged
        for item in self.generating_items():
            item.to_failed()

    def generation_step(self, question: str, variants: list[QuizItemVariant]) -> None:
        items = self.generating_items()
        if len(items) == 0:
            raise ValueError("No items to generate")
        items[0].to_generated(question, variants)
