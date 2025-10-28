from pocketbase import PocketBase
from pocketbase.models.dtos import Record

from ...domain.ports import AttemptRepository, QuizRepository
from ...domain.models import Attempt, Choice, Quiz


class PBAttemptRepository(AttemptRepository):
    def __init__(self, admin_pb: PocketBase):
        self.admin_pb = admin_pb

    async def get(self, id: str) -> Attempt:
        rec = await self.admin_pb.collection("quizAttempts").get_one(id)
        return self._to_attempt(rec)

    async def save(self, attempt: Attempt) -> None:
        try:
            await self.admin_pb.collection("quizAttempts").create(
                {
                    "quiz": attempt.quiz_id,
                    "user": attempt.user_id,
                }
            )
        except:
            await self.admin_pb.collection("quizAttempts").update(
                attempt.id,
                {
                    "quiz": attempt.quiz_id,
                    "user": attempt.user_id,
                },
            )

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
            quiz_id=rec.get("quiz", ""),
            user_id=rec.get("user", ""),
        )
