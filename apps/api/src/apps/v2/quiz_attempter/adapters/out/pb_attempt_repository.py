import json
from dataclasses import asdict
from typing import Any
import httpx
from pocketbase import PocketBase
from pocketbase.models.dtos import Record

from src.lib.settings import settings

from ...domain.models import Attempt
from ...domain.refs import Choice, QuizItemRef, QuizRef
from ...domain.ports import AttemptRepository


class PBAttemptRepository(AttemptRepository):
    def __init__(self, admin_pb: PocketBase, http: httpx.AsyncClient):
        self.admin_pb = admin_pb
        self.http = http

    async def get(self, id: str) -> Attempt:
        rec = await self.admin_pb.collection("quizAttempts").get_one(
            id, options={"params": {"expand": "quiz,quiz.quizItems_via_quiz"}}
        )
        return await self._to_attempt(rec)

    async def save(self, attempt: Attempt) -> None:
        try:
            await self.admin_pb.collection("quizAttempts").create(
                self._to_record(attempt)
            )
        except:
            await self.admin_pb.collection("quizAttempts").update(
                attempt.id, self._to_record(attempt)
            )

    def _to_record(self, attempt: Attempt) -> dict[str, Any]:
        dto = {
            "id": attempt.id,
            "quiz": attempt.quiz.id,
            "user": attempt.user_id,
        }

        if attempt.choices:
            dto["choices"] = json.dumps([asdict(c) for c in attempt.choices])

        return dto

    async def _to_attempt(self, rec: Record) -> Attempt:
        quiz_rec = rec.get("expand", {}).get("quiz", {})
        choices = rec.get("choices", [])

        quiz = await self._to_quiz(quiz_rec, choices)

        choices = [
            Choice(
                idx=choice.get("answerIndex", 0),
                correct=choice.get("correct", False),
            )
            for choice in choices
        ]

        return Attempt(
            id=rec.get("id", ""),
            choices=choices,
            quiz=quiz,
            user_id=rec.get("user", ""),
        )

    async def _to_quiz(self, rec: Record, choices: list[Choice]) -> QuizRef:
        items_recs = rec.get("expand", {}).get("quizItems_via_quiz", [])

        padded_choices = choices + [None] * (len(items_recs) - len(choices))
        items = [
            self._to_item(item, choice)
            for item, choice in zip(items_recs, padded_choices)
        ]

        fname = rec.get("materialsContext")
        material_content = ""
        if fname:
            total_content = await self._load_file_text(
                "quizes", rec.get("id", ""), fname
            )
            material_content = total_content

        return QuizRef(
            id=rec.get("id", ""),
            items=items,
            query=rec.get("query", ""),
            material_content=material_content,
        )

    def _to_item(self, rec: Record, choice: Choice | None) -> QuizItemRef:
        answers_recs = rec.get("answers", [])
        answers = [
            f"Answer {i+1} {a.get('correct', False)}: {a.get('content', '')}\n\nExplanation: {a.get('explanation', '')}\n\n"
            for i, a in enumerate(answers_recs)
        ]
        return QuizItemRef(
            id=rec.get("id", ""),
            question=rec.get("question", ""),
            answers=answers,
            choice=choice,
        )

    def _file_url(self, col: str, id: str, file: str) -> str:
        return f"{settings.pb_url}api/files/{col}/{id}/{file}"

    async def _load_file_text(self, col: str, id: str, file: str) -> str:
        url = self._file_url(col, id, file)
        response = await self.http.get(url)
        return response.text
