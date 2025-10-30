from dataclasses import dataclass, field
from enum import StrEnum


class MessageRole(StrEnum):
    USER = "user"
    AI = "ai"


class MessageStatus(StrEnum):
    FINAL = "final"
    STREAMING = "streaming"


@dataclass(slots=True, kw_only=True)
class MessageMetadata:
    tool_calls: list[str] = field(default_factory=list)
    tool_results: list[str] = field(default_factory=list)


@dataclass(slots=True, kw_only=True)
class MessageRef:
    id: str
    attempt_id: str
    content: str
    role: MessageRole
    status: MessageStatus
    metadata: MessageMetadata

    


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
