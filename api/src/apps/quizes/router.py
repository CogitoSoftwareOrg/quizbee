from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    status,
)
from fastapi.responses import JSONResponse
import logging
from typing import Annotated

from pydantic import BaseModel, Field

from apps.auth import User
from apps.materials import user_owns_materials, materials_to_ai_docs
from lib.clients.http import HTTPAsyncClient
from src.lib.clients import AdminPB, langfuse_client

from .ai import (
    make_quiz_patch_model,
    quizer_agent,
    QuizerDeps,
)

quizes_router = APIRouter(
    prefix="/quizes",
    tags=["quizes"],
    dependencies=[],
)


class CreateQuizDto(BaseModel):
    material_ids: list[str] = Field(default=[])
    with_attempt: bool = Field(default=True)
    query: str = Field(default="")


@quizes_router.post("", dependencies=[Depends(user_owns_materials)])
async def create_quiz(
    admin_pb: AdminPB,
    user: User,
    dto: CreateQuizDto,
):
    if not dto.material_ids and not dto.query:
        raise HTTPException(status_code=400, detail="Material IDs or query is required")

    user_id = user.get("id", "")

    # CREATE QUIZ
    quiz = await admin_pb.collection("quizes").create(
        {
            "author": user_id,
            "query": dto.query,
            "materials": dto.material_ids,  # pyright: ignore[reportArgumentType]
        }
    )

    if dto.with_attempt:
        quiz_attempt = await admin_pb.collection("quizAttempts").create(
            {
                "user": user_id,
                "quiz": quiz.get("id", ""),
            }
        )
    else:
        quiz_attempt = {}

    return JSONResponse(
        content={
            "quiz_attempt_id": quiz_attempt.get("id", ""),
            "quiz_id": quiz.get("id", ""),
        },
        status_code=status.HTTP_201_CREATED,
    )


# GENERATE QUIZ ITEMS TASK
async def _generate_quiz_task(
    http: HTTPAsyncClient,
    admin_pb: AdminPB,
    user_id: str,
    quiz_id: str,
    limit: int,
):
    quiz = await admin_pb.collection("quizes").get_one(
        quiz_id,
        options={
            "params": {
                "expand": "materials,quizItems_via_quiz",
            }
        },
    )
    materials = quiz.get("expand", {}).get("materials", [])
    quiz_items = quiz.get("expand", {}).get("quizItems_via_quiz", [])
    quiz_items = sorted(
        quiz_items,
        key=lambda qi: qi.get("order", 0),
    )

    prev_quiz_items = [qi for qi in quiz_items if qi.get("status") == "final"]
    blank_quiz_items = [qi for qi in quiz_items if qi.get("status") == "blank"]

    limit = min(limit, len(blank_quiz_items))
    quiz_items = blank_quiz_items[:limit]

    # Mark as "generating"
    for qi in quiz_items[:limit]:
        try:
            await admin_pb.collection("quizItems").update(
                qi.get("id", ""),
                {"status": "generating"},
            )
        except Exception as e:
            logging.exception("Failed to set generating for %s: %s", qi.get("id"), e)

    # Prepare request to LLM
    q = quiz.get("query", "")
    materials_docs = await materials_to_ai_docs(materials)
    try:
        with langfuse_client.start_as_current_span(name="quiz-patch") as span:
            res = await quizer_agent.run(
                user_prompt=[q, *materials_docs],
                deps=QuizerDeps(
                    admin_pb=admin_pb,
                    quiz=quiz,
                    prev_quiz_items=prev_quiz_items,
                    materials=materials,
                    http=http,
                ),
                output_type=make_quiz_patch_model(limit),
            )
            span.update_trace(
                user_id=user_id,
                session_id=quiz_id,
            )
    except Exception as e:
        logging.exception("Agent run failed for quiz %s: %s", quiz_id, e)
        for qi in quiz_items[:limit]:
            try:
                await admin_pb.collection("quizItems").update(
                    qi.get("id", ""), {"status": "failed"}
                )
            except Exception:
                pass
        return

    patch = res.output

    # Update items with final data
    upd = {}
    for qi, patch_qi in zip(quiz_items[:limit], patch.quiz_items):
        answers = [
            {
                "content": wa.answer,
                "explanation": wa.explanation,
                "correct": False,
            }
            for wa in patch_qi.wrong_answers
        ] + [
            {
                "content": patch_qi.right_answer.answer,
                "explanation": patch_qi.right_answer.explanation,
                "correct": True,
            }
        ]
        try:
            upd = await admin_pb.collection("quizItems").update(
                qi.get("id", ""),
                {
                    "answers": answers,  # pyright: ignore[reportArgumentType]
                    "question": patch_qi.question,
                    "status": "final",
                },
            )
        except Exception as e:
            logging.exception("Failed to finalize %s: %s", qi.get("id"), e)

    # HARD TRIGGER OF SUBSCRIPTION, IMPROVE TO SUBSCRIBE QUIZ ITEMS LATER
    await admin_pb.collection("quizes").update(
        quiz_id,
        {"updated": upd.get("updated", "")},
    )


class GenerateQuizItems(BaseModel):
    limit: Annotated[int, Field(default=2, ge=2, le=5)]


@quizes_router.patch("/{quiz_id}")
async def generate_quiz_items(
    http: HTTPAsyncClient,
    admin_pb: AdminPB,
    quiz_id: str,
    dto: GenerateQuizItems,
    background: BackgroundTasks,
    user: User,
):
    # SUBSCRIPTION
    user_id = user.get("id", "")

    # Prevalidate
    quiz = await admin_pb.collection("quizes").get_one(
        quiz_id, options={"params": {"expand": "materials,quizItems_via_quiz"}}
    )
    quiz_items = quiz.get("expand", {}).get("quizItems_via_quiz", [])
    if not quiz_items:
        raise HTTPException(status_code=404, detail="Quiz items not found")

    # Generate
    background.add_task(
        _generate_quiz_task, http, admin_pb, user_id, quiz_id, dto.limit
    )

    return JSONResponse(
        content={"scheduled": True, "quiz_id": quiz_id, "limit": dto.limit},
        status_code=status.HTTP_202_ACCEPTED,
    )
