import asyncio
from typing import Any
import httpx
from pocketbase import FileUpload, PocketBase
from pocketbase.models.dtos import Record

from src.lib.settings import settings

from ...domain.ports import QuizRepository
from ...domain.models import Attempt, Choice, Quiz


class PBQuizRepository(QuizRepository):
    def __init__(self, admin_pb: PocketBase, http: httpx.AsyncClient):
        self.admin_pb = admin_pb
        self.http = http

    async def get(self, id: str) -> Quiz:
        rec = await self.admin_pb.collection("quizzes").get_one(
            id, options={"params": {"expand": "quizItems_via_quiz"}}
        )
        return await self._to_quiz(rec)

    async def get_user_quizzes(self, user_id: str) -> list[Quiz]:
        recs = await self.admin_pb.collection("quizzes").get_full_list(
            options={
                "params": {
                    "filter": f"author = '{user_id}'",
                    "expand": "quizItems_via_quiz",
                }
            }
        )

        return [await self._to_quiz(rec) for rec in recs]

    async def save(self, quiz: Quiz):
        await self.admin_pb.collection("quizzes").create(await self._to_record(quiz))

    async def _to_quiz(self, rec: Record) -> Quiz:
        q_id = rec.get("id", "")
        total_content = ""
        fname = rec.get("materialsContext")
        if fname:
            url = f"{settings.pb_url}api/files/quizes/{q_id}/{fname}"
            response = await self.http.get(url)
            total_content = response.text

        return Quiz(
            id=rec.get("id", ""),
            author_id=rec.get("author", ""),
            material_ids=rec.get("materials", []),
            title=rec.get("title", ""),
            length=rec.get("itemsLimit", 0),
            query=rec.get("query", ""),
            difficulty=rec.get("difficulty", ""),
            summary=rec.get("summary", ""),
            tags=rec.get("tags", []),
            category=rec.get("category", ""),
            status=rec.get("status", ""),
            visibility=rec.get("visibility", ""),
            material_content=total_content,
            avoid_repeat=rec.get("avoidRepeat", False),
            items=rec.get("items", []),
            gen_config=rec.get("genConfig", {}),
        )

    async def _to_record(self, quiz: Quiz) -> dict[str, Any]:
        content = quiz.material_content
        f = FileUpload(("materialsContext.txt", content.encode("utf-8")))

        return {
            # Simple fields
            "id": quiz.id,
            "author": quiz.author_id,
            "materials": quiz.material_ids,
            "title": quiz.title,
            "itemsLimit": quiz.length,
            "query": quiz.query,
            "difficulty": quiz.difficulty,
            "summary": quiz.summary,
            "tags": quiz.tags,
            "category": quiz.category,
            "status": quiz.status,
            "visibility": quiz.visibility,
            "avoidRepeat": quiz.avoid_repeat,
            "items": quiz.items,
            "genConfig": quiz.gen_config,
            # Files
            "materialContent": f,
        }
