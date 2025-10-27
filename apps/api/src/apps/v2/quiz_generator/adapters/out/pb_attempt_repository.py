from pocketbase import PocketBase
from pocketbase.models.dtos import Record

from ...domain.ports import AttemptRepository, QuizRepository
from ...domain.models import Attempt, Choice, Quiz


class PBAttemptRepository(AttemptRepository):
    def __init__(self, admin_pb: PocketBase):
        self.admin_pb = admin_pb

    async def create(self, quiz_id: str, user_id: str) -> Attempt:
        rec = await self.admin_pb.collection("quizAttempts").create(
            {
                "quiz": quiz_id,
                "user": user_id,
            }
        )

        return self._to_attempt(rec)

    def _to_attempt(self, rec: Record) -> Attempt:
        choices = rec.get("choices", [])
        choices = [
            Choice(
                idx=choice.get("answerIndex", 0),
                correct=choice.get("correct", False),
                item_id=choice.get("itemId", ""),
            )
            for choice in choices
        ]
        return Attempt(
            id=rec.get("id", ""),
            choices=choices,
        )
