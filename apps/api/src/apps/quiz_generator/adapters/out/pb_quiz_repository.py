import asyncio
import json
from dataclasses import asdict
import logging
from typing import Any
import httpx
from pocketbase import FileUpload, PocketBase
from pocketbase.models.dtos import Record

from src.lib.settings import settings

from ...domain.ports import QuizRepository
from ...domain.models import (
    MaterialRef,
    Quiz,
    QuizGenConfig,
    QuizItem,
    QuizItemVariant,
    QuizStatus,
)

logger = logging.getLogger(__name__)


class PBQuizRepository(QuizRepository):
    def __init__(self, admin_pb: PocketBase, http: httpx.AsyncClient):
        self.admin_pb = admin_pb
        self.http = http

    async def get(self, id: str) -> Quiz:
        rec = await self.admin_pb.collection("quizes").get_one(
            id, options={"params": {"expand": "quizItems_via_quiz,materials"}}
        )
        return await self._rec_to_quiz(rec)

    async def get_user_quizzes(self, user_id: str) -> list[Quiz]:
        recs = await self.admin_pb.collection("quizes").get_full_list(
            options={
                "params": {
                    "filter": f"author = '{user_id}'",
                    "expand": "quizItems_via_quiz,materials",
                }
            }
        )

        return [await self._rec_to_quiz(rec) for rec in recs]

    async def save(self, quiz: Quiz):
        await asyncio.gather(*[self.save_item(item) for item in quiz.items])

        try:
            await self.admin_pb.collection("quizes").update(
                quiz.id, await self._to_record(quiz)
            )
        except:
            await self.admin_pb.collection("quizes").create(await self._to_record(quiz))

    async def save_item(self, item: QuizItem):
        try:
            await self.admin_pb.collection("quizItems").create(
                await self._item_to_rec(item)
            )
        except:
            await self.admin_pb.collection("quizItems").update(
                item.id, await self._item_to_rec(item)
            )

    async def _rec_to_quiz(self, rec: Record) -> Quiz:
        materials_recs = rec.get("expand", {}).get("materials", [])
        items_recs = rec.get("expand", {}).get("quizItems_via_quiz", [])
        q_id = rec.get("id", "")

        items = sorted(
            [self._rec_to_item(i) for i in items_recs], key=lambda x: x.order
        )
        materials = await asyncio.gather(
            *[self._rec_to_material(m) for m in materials_recs]
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
            gen_config=self._rec_to_config(rec),
            generation=rec.get("generation", 0),
        )

        if not len(quiz.material_content) == 0 and len(quiz.materials) > 0:
            quiz.request_build_material_content()

        return quiz

    async def _rec_to_material(self, material_rec: Record) -> MaterialRef:
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

    def _rec_to_item(self, item_rec: Record) -> QuizItem:
        answers = item_rec.get("answers") or []
        return QuizItem(
            id=item_rec.get("id", ""),
            question=item_rec.get("question", ""),
            variants=[self._rec_to_variant(a) for a in answers],
            order=item_rec.get("order", 0),
            status=item_rec.get("status", ""),
        )

    def _rec_to_variant(self, rec: dict[str, Any]) -> QuizItemVariant:
        return QuizItemVariant(
            content=rec.get("content", ""),
            explanation=rec.get("explanation", ""),
            is_correct=rec.get("correct", False),
        )

    async def _to_record(self, quiz: Quiz) -> dict[str, Any]:
        content = quiz.material_content

        dto = {
            # Simple fields
            "generation": quiz.generation,
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
            "dynamicConfig": self._config_to_rec(quiz.gen_config),
            "materials": [m.id for m in quiz.materials],
            "slug": quiz.slug,
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

    async def _item_to_rec(self, item: QuizItem) -> dict[str, Any]:
        dto = {
            "id": item.id,
            "question": item.question,
            "order": item.order,
            "status": item.status,
        }

        if len(item.variants) > 0:
            dto["answers"] = [
                {
                    "content": v.content,
                    "explanation": v.explanation,
                    "correct": v.is_correct,
                }
                for v in item.variants
            ]

        return dto

    def _rec_to_config(self, rec: Record) -> QuizGenConfig:
        dynamic_config = rec.get("dynamicConfig", {})

        return QuizGenConfig(
            negative_questions=dynamic_config.get("negativeQuestions", []),
            additional_instructions=dynamic_config.get("adds", []),
            more_on_topic=dynamic_config.get("moreOnTopic", []),
            less_on_topic=dynamic_config.get("lessOnTopic", []),
            extra_beginner=dynamic_config.get("extraBeginner", []),
            extra_expert=dynamic_config.get("extraExpert", []),
        )

    def _config_to_rec(self, config: QuizGenConfig):
        dto = {
            "negativeQuestions": config.negative_questions,
            "adds": config.additional_instructions,
            "moreOnTopic": config.more_on_topic,
            "lessOnTopic": config.less_on_topic,
            "extraBeginner": config.extra_beginner,
            "extraExpert": config.extra_expert,
        }
        logger.debug(f"Config to rec: {asdict(config)} -> {dto}")
        return json.dumps(dto)

    def _file_url(self, col: str, id: str, file: str) -> str:
        return f"{settings.pb_url}api/files/{col}/{id}/{file}"

    async def _load_file_text(self, col: str, id: str, file: str) -> str:
        url = self._file_url(col, id, file)
        response = await self.http.get(url)
        return response.text

    def _to_camel_case(self, snake_case: dict[str, Any]) -> dict[str, Any]:
        camel_case = {}
        for key, value in snake_case.items():
            parts = key.split("_")
            camel_key = parts[0] + "".join(word.capitalize() for word in parts[1:])
            camel_case[camel_key] = value
        return camel_case
