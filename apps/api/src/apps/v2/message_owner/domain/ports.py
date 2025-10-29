from typing import Protocol

from .models import AttemptHistory, Message


class MessageHistoryRepository(Protocol):
    async def get(self, attempt_id: str, limit: int) -> AttemptHistory: ...
    async def save(self, messages: list[Message]) -> None: ...
