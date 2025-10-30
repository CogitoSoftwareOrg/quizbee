from dataclasses import dataclass, field
from enum import StrEnum

from src.lib.utils import genID


class MessageRole(StrEnum):
    USER = "user"
    AI = "ai"


class MessageStatus(StrEnum):
    INITIAL = "initial"
    FINAL = "final"
    STREAMING = "streaming"


@dataclass(slots=True, kw_only=True)
class MessageMetadata:
    tool_calls: list[str] = field(default_factory=list)
    tool_results: list[str] = field(default_factory=list)
    item_id: str = field(default="")

    def update(self, tool_calls: list[str], tool_results: list[str]):
        self.tool_calls.extend(tool_calls)
        self.tool_results.extend(tool_results)


@dataclass(slots=True, kw_only=True)
class Message:
    id: str = field(default_factory=genID)
    attempt_id: str
    content: str
    role: MessageRole
    status: MessageStatus
    metadata: MessageMetadata

    @classmethod
    def create(cls, attempt_id: str, role: MessageRole, item_id):
        return cls(
            attempt_id=attempt_id,
            content="",
            role=role,
            status=MessageStatus.INITIAL,
            metadata=MessageMetadata(item_id=item_id),
        )

    def to_streaming(self):
        if self.status != MessageStatus.INITIAL:
            raise ValueError(f"Message {self.id} is not initial")
        if self.role != MessageRole.AI:
            raise ValueError(f"Message {self.id} should be AI for streaming")
        self.status = MessageStatus.STREAMING

    def to_final(self, content: str, metadata: MessageMetadata):
        self.metadata.update(metadata.tool_calls, metadata.tool_results)
        self.content = content
        self.status = MessageStatus.FINAL
