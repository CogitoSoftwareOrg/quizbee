from pocketbase import PocketBase
from pocketbase.models.dtos import Record

from ...domain.ports import QuizRepository
from ...domain.models import QuizAttempt


class PBQuizRepository(QuizRepository):
    def __init__(self, admin_pb: PocketBase):
        self.admin_pb = admin_pb

    async def create_attempt(self, quiz_id: str, user_id: str) -> QuizAttempt:
        rec = await self.admin_pb.collection("quizAttempts").create(
            {
                "quiz": quiz_id,
                "user": user_id,
            }
        )

        return self._to_attempt(rec)

    def _to_attempt(self, rec: Record) -> QuizAttempt:
        return QuizAttempt(
            id=rec.get("id", ""),
        )
