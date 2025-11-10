from dataclasses import dataclass, field
from enum import StrEnum


class MessageRoleRef(StrEnum):
    USER = "user"
    AI = "ai"


class MessageStatusRef(StrEnum):
    FINAL = "final"
    STREAMING = "streaming"


@dataclass(slots=True, kw_only=True)
class MessageMetadataRef:
    tool_calls: list[str] = field(default_factory=list)
    tool_results: list[str] = field(default_factory=list)


@dataclass(slots=True, kw_only=True)
class MessageRef:
    id: str
    attempt_id: str
    content: str
    role: MessageRoleRef
    status: MessageStatusRef
    metadata: MessageMetadataRef


@dataclass(slots=True, kw_only=True)
class Choice:
    idx: int
    correct: bool


@dataclass(slots=True, kw_only=True)
class QuizItemRef:
    id: str
    question: str
    answers: list[str]
    choice: Choice | None = None


@dataclass(slots=True, kw_only=True)
class QuizRef:
    id: str
    items: list[QuizItemRef]
    query: str
    material_content: str
    cluster_vectors: list[list[float]] = field(default_factory=list)
