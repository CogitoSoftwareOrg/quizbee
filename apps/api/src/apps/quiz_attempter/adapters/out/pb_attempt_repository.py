import json
from dataclasses import asdict
import logging
from typing import Any
import httpx
from pocketbase import PocketBase
from pocketbase.models.dtos import Record

from src.lib.settings import settings

from ...domain.models import Attempt, Feedback
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
        return await self._rec_to_attempt(rec)

    async def create(self, attempt: Attempt) -> None:
        try:
            dto = self._attempt_to_rec(attempt)
            await self.admin_pb.collection("quizAttempts").create(dto)
        except Exception as e:
            raise

    async def update(self, attempt: Attempt) -> None:
        try:
            dto = self._attempt_to_rec(attempt)
            await self.admin_pb.collection("quizAttempts").update(attempt.id, dto)
        except Exception as e:
            raise

    def _attempt_to_rec(self, attempt: Attempt) -> dict[str, Any]:
        dto = {
            "id": attempt.id,
            "quiz": attempt.quiz.id,
            "user": attempt.user_id,
            "feedback": (
                self._feedback_to_rec(attempt.feedback) if attempt.feedback else None
            ),
        }

        if attempt.choices:
            dto["choices"] = json.dumps(
                [self._choice_to_rec(c) for c in attempt.choices]
            )

        return dto

    async def _rec_to_attempt(self, rec: Record) -> Attempt:
        quiz_rec = rec.get("expand", {}).get("quiz", {})
        choices = rec.get("choices", [])

        choices = [
            Choice(
                idx=choice.get("answerIndex", 0),
                correct=choice.get("correct", False),
            )
            for choice in choices
        ]

        quiz = await self._rec_to_quiz(quiz_rec, choices)

        feedback_rec = rec.get("feedback")
        feedback = self._rec_to_feedback(feedback_rec) if feedback_rec else None

        return Attempt(
            feedback=feedback,
            id=rec.get("id", ""),
            choices=choices,
            quiz=quiz,
            user_id=rec.get("user", ""),
        )

    def _rec_to_feedback(self, rec: Record) -> Feedback:
        return Feedback(
            overview=rec.get("overview", ""),
            problem_topics=rec.get("problemTopics", []),
            uncovered_topics=rec.get("uncoveredTopics", []),
        )

    def _feedback_to_rec(self, feedback: Feedback):
        return {
            "overview": feedback.overview,
            "problemTopics": feedback.problem_topics,
            "uncoveredTopics": feedback.uncovered_topics,
        }

    async def _rec_to_quiz(self, rec: Record, choices: list[Choice]) -> QuizRef:
        items_recs = rec.get("expand", {}).get("quizItems_via_quiz", [])

        padded_choices = choices + [None] * (len(items_recs) - len(choices))
        items = [
            self._rec_to_item(item, choice)
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

    def _rec_to_choice(self, rec: Record):
        return Choice(
            idx=rec.get("answerIndex", 0),
            correct=rec.get("correct", False),
        )

    def _choice_to_rec(self, choice: Choice):
        return {
            "answerIndex": choice.idx,
            "correct": choice.correct,
        }

    def _rec_to_item(self, rec: Record, choice: Choice | None) -> QuizItemRef:
        answers_recs = rec.get("answers") or []
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
