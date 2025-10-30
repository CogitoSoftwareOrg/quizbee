from dataclasses import dataclass, field
from typing import Protocol

from ..domain.models import Message, MessageMetadata


@dataclass(slots=True, kw_only=True)
class GetAttemptHistoryCmd:
    attempt_id: str
    limit: int = 100


@dataclass(slots=True, kw_only=True)
class StartMessageCmd:
    attempt_id: str
    item_id: str


@dataclass(slots=True, kw_only=True)
class FinalizeMessageCmd:
    message_id: str
    content: str
    metadata: MessageMetadata


class MessageOwnerApp(Protocol):
    async def get_attempt_history(self, cmd: GetAttemptHistoryCmd) -> list[Message]: ...

    async def start_message(self, cmd: StartMessageCmd) -> Message: ...
    async def finalize_message(self, cmd: FinalizeMessageCmd) -> None: ...
