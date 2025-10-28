import asyncio
import json
from dataclasses import asdict
from typing import Any
import httpx
from pocketbase import FileUpload, PocketBase
from pocketbase.models.dtos import Record

from src.lib.settings import settings

from ...domain.ports import QuizRepository
from ...domain.models import (
    Attempt,
    Choice,
    MaterialRef,
    Quiz,
    QuizGenConfig,
    QuizItem,
    QuizStatus,
)


class PBQuizRepository(QuizRepository):
    def __init__(self, admin_pb: PocketBase, http: httpx.AsyncClient):
        self.admin_pb = admin_pb
        self.http = http

    async def get(self, id: str) -> Quiz:
        rec = await self.admin_pb.collection("quizes").get_one(
            id, options={"params": {"expand": "quizItems_via_quiz,materials"}}
        )
        return await self._to_quiz(rec)

    async def get_user_quizzes(self, user_id: str) -> list[Quiz]:
        recs = await self.admin_pb.collection("quizes").get_full_list(
            options={
                "params": {
                    "filter": f"author = '{user_id}'",
                    "expand": "quizItems_via_quiz,materials",
                }
            }
        )

        return [await self._to_quiz(rec) for rec in recs]

    async def save(self, quiz: Quiz):
        try:
            await self.admin_pb.collection("quizes").create(await self._to_record(quiz))
        except:
            await self.admin_pb.collection("quizes").update(
                quiz.id, await self._to_record(quiz)
            )

    async def _to_quiz(self, rec: Record) -> Quiz:
        materials_recs = rec.get("expand", {}).get("materials", [])
        items_recs = rec.get("expand", {}).get("quizItems_via_quiz", [])
        q_id = rec.get("id", "")

        items = [self._to_item(i) for i in items_recs]
        materials = await asyncio.gather(
            *[self._to_material(m) for m in materials_recs]
        )

        fname = rec.get("materialsContext")
        material_content = ""
        if fname:
            total_content = await self._load_file_text("quizes", q_id, fname)
            material_content = total_content

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
            gen_config=self._to_gen_config(rec),
        )

        if not len(quiz.material_content) == 0 and len(quiz.materials) > 0:
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

        dto = {
            # Simple fields
            "id": quiz.id,
            "author": quiz.author_id,
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
            "dynamicConfig": json.dumps(asdict(quiz.gen_config)),
            "materials": [m.id for m in quiz.materials],
        }

        f = (
            FileUpload(
                (
                    self._file_url("quizes", quiz.id, "materialsContext.txt"),
                    content.encode("utf-8"),
                )
            )
            if quiz.status == QuizStatus.PREPARING
            else None
        )

        if f:
            dto["materialsContext"] = f

        return dto

    def _to_gen_config(self, rec: Record) -> QuizGenConfig:
        return QuizGenConfig(
            negative_questions=rec.get("negativeQuestions", []),
            additional_instructions=rec.get("adds", []),
            more_on_topic=rec.get("moreOnTopic", []),
            less_on_topic=rec.get("lessOnTopic", []),
            extra_beginner=rec.get("extraBeginner", []),
            extra_expert=rec.get("extraExpert", []),
        )

    def _file_url(self, col: str, id: str, file: str) -> str:
        return f"{settings.pb_url}api/files/{col}/{id}/{file}"

    async def _load_file_text(self, col: str, id: str, file: str) -> str:
        url = self._file_url(col, id, file)
        response = await self.http.get(url)
        return response.text
