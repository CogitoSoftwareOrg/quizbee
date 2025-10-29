from dataclasses import dataclass, field
from enum import StrEnum


class Role(StrEnum):
    USER = "user"
    AI = "ai"


class Status(StrEnum):
    FINAL = "final"
    STREAMING = "streaming"


@dataclass(slots=True, kw_only=True)
class MessageMetadata:
    tool_calls: list[str] = field(default_factory=list)
    tool_results: list[str] = field(default_factory=list)


@dataclass(slots=True, kw_only=True)
class Message:
    id: str
    attempt_id: str
    content: str
    role: Role
    status: Status
    metadata: MessageMetadata

    def to_final(self):
        self.status = Status.FINAL
