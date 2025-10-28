import asyncio
from typing import Any
import httpx
from pocketbase import FileUpload, PocketBase
from pocketbase.models.dtos import Record

from src.lib.settings import settings

from ...domain.ports import QuizRepository
from ...domain.models import Attempt, Choice, MaterialRef, Quiz, QuizItem, QuizStatus


class PBQuizRepository(QuizRepository):
    def __init__(self, admin_pb: PocketBase, http: httpx.AsyncClient):
        self.admin_pb = admin_pb
        self.http = http

    async def get(self, id: str, material_content="") -> Quiz:
        rec = await self.admin_pb.collection("quizzes").get_one(
            id, options={"params": {"expand": "quizItems_via_quiz,materials"}}
        )
        return await self._to_quiz(rec, material_content)

    async def get_user_quizzes(self, user_id: str) -> list[Quiz]:
        recs = await self.admin_pb.collection("quizzes").get_full_list(
            options={
                "params": {
                    "filter": f"author = '{user_id}'",
                    "expand": "quizItems_via_quiz,materials",
                }
            }
        )

        return [await self._to_quiz(rec) for rec in recs]

    async def save(self, quiz: Quiz):
        await self.admin_pb.collection("quizzes").create(await self._to_record(quiz))

    async def _to_quiz(self, rec: Record, material_content="") -> Quiz:
        materials_recs = rec.get("expand", {}).get("materials", [])
        items_recs = rec.get("expand", {}).get("quizItems_via_quiz", [])
        q_id = rec.get("id", "")

        items = [self._to_item(i) for i in items_recs]
        materials = await asyncio.gather(
            *[self._to_material(m) for m in materials_recs]
        )

        quiz = Quiz(
            id=rec.get("id", ""),
            materials=materials,
            items=items,
            material_content=material_content,
            author_id=rec.get("author", ""),
            title=rec.get("title", ""),
            length=rec.get("itemsLimit", 0),
            query=rec.get("query", ""),
            difficulty=rec.get("difficulty", ""),
            summary=rec.get("summary", ""),
            tags=rec.get("tags", []),
            category=rec.get("category", ""),
            status=rec.get("status", ""),
            visibility=rec.get("visibility", ""),
            avoid_repeat=rec.get("avoidRepeat", False),
            gen_config=rec.get("genConfig", {}),
        )

        fname = rec.get("materialsContext")
        if quiz.material_content:
            pass
        elif fname:
            total_content = await self._load_file_text("quizes", q_id, fname)
            quiz.set_material_content(total_content)
        else:
            quiz.request_build_material_content()

        return quiz

    async def _to_material(self, material_rec: Record) -> MaterialRef:
        m_id = material_rec.get("id", "")
        kind = material_rec.get("kind", "")
        is_book = material_rec.get("isBook", False)
        f = (
            material_rec.get("file", "")
            if kind == "simple"
            else material_rec.get("textFile", "")
        )

        text = await self._load_file_text("materials", m_id, f)
        return MaterialRef(
            id=m_id,
            text=text,
            is_book=is_book,
            filename=f,
        )

    def _to_item(self, item_rec: Record) -> QuizItem:
        return QuizItem(
            id=item_rec.get("id", ""),
            question=item_rec.get("question", ""),
            variants=item_rec.get("answers", []),
            order=item_rec.get("order", 0),
            status=item_rec.get("status", ""),
        )

    async def _to_record(self, quiz: Quiz) -> dict[str, Any]:
        content = quiz.material_content

        f = (
            FileUpload(("materialsContext.txt", content.encode("utf-8")))
            if quiz.status == QuizStatus.PREPARING and len(content) > 0
            else None
        )

        return {
            # Simple fields
            "id": quiz.id,
            "author": quiz.author_id,
            "materials": [m.id for m in quiz.materials],
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

    async def _load_file_text(self, col: str, id: str, file: str) -> str:
        url = f"{settings.pb_url}api/files/{col}/{id}/{file}"
        response = await self.http.get(url)
        return response.text
