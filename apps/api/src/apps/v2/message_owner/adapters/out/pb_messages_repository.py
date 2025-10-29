from typing import Any
import asyncio
from pocketbase import PocketBase
from pocketbase.models.dtos import Record

from ...domain.ports import MessageHistoryRepository
from ...domain.models import AttemptHistory, Message


class PBMessageHistoryRepository(MessageHistoryRepository):
    def __init__(self, pb: PocketBase):
        self.pb = pb

    async def get(self, attempt_id: str, limit: int = 100) -> AttemptHistory:
        recs = await self.pb.collection("messages").get_full_list(
            options={
                "params": {
                    "filter": f"quizAttempt = '{attempt_id}'",
                    "sort": "-created",
                    "limit": limit,
                }
            },
        )
        recs.reverse()

        return AttemptHistory(
            attempt_id=attempt_id, messages=[self._to_message(rec) for rec in recs]
        )

    async def save(self, messages: list[Message]) -> None:
        for message in messages:
            try:
                await self.pb.collection("messages").create(self._to_record(message))
            except Exception as e:
                await self.pb.collection("messages").update(
                    message.id, self._to_record(message)
                )

    def _to_record(self, message: Message) -> dict[str, Any]:
        return {
            "id": message.id,
            "attempt": message.attempt_id,
            "content": message.content,
            "role": message.role,
            "status": message.status,
            "metadata": message.metadata,
        }

    def _to_message(self, rec: Record) -> Message:
        return Message(
            id=rec.get("id", ""),
            attempt_id=rec.get("attempt_id", ""),
            content=rec.get("content", ""),
            role=rec.get("role", ""),
            status=rec.get("status", ""),
            metadata=rec.get("metadata", {}),
        )
