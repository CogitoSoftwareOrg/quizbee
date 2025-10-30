from dataclasses import dataclass, field
from enum import StrEnum

from src.lib.utils import genID


class Role(StrEnum):
    USER = "user"
    AI = "ai"


class Status(StrEnum):
    INITIAL = "initial"
    FINAL = "final"
    STREAMING = "streaming"


@dataclass(slots=True, kw_only=True)
class MessageMetadata:
    tool_calls: list[str] = field(default_factory=list)
    tool_results: list[str] = field(default_factory=list)


@dataclass(slots=True, kw_only=True)
class Message:
    id: str = field(default_factory=genID)
    attempt_id: str
    content: str
    role: Role
    status: Status
    metadata: MessageMetadata

    @classmethod
    def create(cls, attempt_id: str, role: Role):
        return cls(
            attempt_id=attempt_id,
            content="",
            role=role,
            status=Status.INITIAL,
            metadata=MessageMetadata(),
        )

    def to_streaming(self):
        if self.status != Status.INITIAL:
            raise ValueError(f"Message {self.id} is not initial")
        if self.role != Role.AI:
            raise ValueError(f"Message {self.id} should be AI for streaming")
        self.status = Status.STREAMING

    def to_final(self, content: str, metadata: MessageMetadata):
        self.content = content
        self.metadata = metadata
        self.status = Status.FINAL
