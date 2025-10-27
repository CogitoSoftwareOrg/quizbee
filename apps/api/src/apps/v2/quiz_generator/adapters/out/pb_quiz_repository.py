import asyncio
from pocketbase import PocketBase
from pocketbase.models.dtos import Record

from ...domain.ports import QuizRepository
from ...domain.models import Attempt, Choice, Quiz


class PBQuizRepository(QuizRepository):
    def __init__(self, admin_pb: PocketBase):
        self.admin_pb = admin_pb

    async def get(self, ids: list[str]) -> list[Quiz]:
        tasks = []
        for id in ids:
            tasks.append(self.admin_pb.collection("quizzes").get_one(id))
        recs = await asyncio.gather(*tasks)

        return [self._to_quiz(rec) for rec in recs]

    def _to_quiz(self, rec: Record) -> Quiz:
        return Quiz(
            id=rec.get("id", ""),
            author_id=rec.get("author", ""),
            materials=rec.get("materials", []),
            title=rec.get("title", ""),
            length=rec.get("length", 0),
            query=rec.get("query", ""),
            difficulty=rec.get("difficulty", ""),
        )
