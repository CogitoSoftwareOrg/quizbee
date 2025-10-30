from dataclasses import asdict
import logging
from typing import Any
import asyncio
from pocketbase import PocketBase
from pocketbase.models.dtos import Record

from ...domain.ports import MessageRepository
from ...domain.models import Message, MessageMetadata


class PBMessageRepository(MessageRepository):
    def __init__(self, pb: PocketBase):
        self.pb = pb

    async def get(self, id: str) -> Message:
        rec = await self.pb.collection("messages").get_one(id)
        return self._to_message(rec)

    async def get_attempt(self, attempt_id: str, limit: int = 100) -> list[Message]:
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

        return [self._to_message(rec) for rec in recs]

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
            "quizAttempt": message.attempt_id,
            "content": message.content,
            "role": message.role,
            "status": message.status,
            "metadata": asdict(message.metadata),
        }

    def _to_message(self, rec: Record) -> Message:
        return Message(
            id=rec.get("id", ""),
            attempt_id=rec.get("quizAttempt", ""),
            content=rec.get("content", ""),
            role=rec.get("role", ""),
            status=rec.get("status", ""),
            metadata=MessageMetadata(**(rec.get("metadata", {}) or {})),
        )
