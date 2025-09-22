from pocketbase import PocketBase, FileUpload
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Form,
    Request,
    Query,
    HTTPException,
    File,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse, JSONResponse
import json
import logging
from typing import Annotated

from pydantic import BaseModel, Field

from lib.clients.http import HTTPAsyncClient
from src.apps.messages import pb_to_ai
from src.lib.settings import settings
from src.lib.clients import AdminPB, langfuse_client

from .ai import (
    QuizPatch,
    make_quiz_patch_model,
    quizer_agent,
    QuizerDeps,
)

quizes_router = APIRouter(prefix="/quizes", tags=["quizes"])


@quizes_router.post("/")
async def create_quiz(
    admin_pb: AdminPB,
    request: Request,
    old_file_names: list[str] = Form(default=[]),
    files: list[UploadFile] = File(default=[]),
    with_attempt: bool = Form(default=True),
    query: str = Form(),
):
    # AUTH
    # pb_token = request.cookies.get("pb_token")
    # if not pb_token:
    #     raise HTTPException(status_code=401, detail=f"Unauthorized: no pb_token")
    # try:
    #     pb = PocketBase(settings.pb_url)
    #     pb._inners.auth.set_user({"token": pb_token, "record": {}})
    #     user = await pb.collection("users").auth.refresh()
    # except Exception as e:
    #     raise HTTPException(status_code=401, detail=f"Unauthorized: {e}")

    # SUBSCRIPTION
    # user_id = user.get("id", "")
    user_id = "lhjpor907gtxpry"
    try:
        subscription = await admin_pb.collection("subscriptions").get_first(
            options={"params": {"filter": f"user = '{user_id}'"}},
        )
    except Exception as e:
        ...
        # raise HTTPException(status_code=401, detail=f"Unauthorized: {e}")

    # CREATE QUIZ
    material_ids = []
    for file in files:
        material = await admin_pb.collection("materials").create(
            {
                "user": user_id,
                "file": FileUpload((file.filename or "material_file", file.file)),
            }
        )
        material_ids.append(material.get("id", ""))
    for name in old_file_names:
        material = await admin_pb.collection("materials").get_first(
            options={"params": {"filter": f"file = '{name}'"}},
        )
        material_ids.append(material.get("id", ""))

    quiz = await admin_pb.collection("quizes").create(
        {
            "author": user_id,
            "query": query,
            "materials": material_ids,
        }
    )

    if with_attempt:
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
        filter(lambda i: i.get("status") == "blank", quiz_items),
        key=lambda x: x.get("order", 0),
    )

    limit = min(limit, len(quiz_items))

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
    try:
        with langfuse_client.start_as_current_span(name="quiz-patch") as span:
            res = await quizer_agent.run(
                user_prompt=q,
                deps=QuizerDeps(
                    admin_pb=admin_pb, quiz=quiz, materials=materials, http=http
                ),
                output_type=make_quiz_patch_model(limit),
            )
            span.update_trace(
                user_id=user_id,
                session_id=quiz_id,
            )
    except Exception as e:
        logging.exception("Agent run failed for quiz %s: %s", quiz_id, e)
        # можно вернуть items в "failed"
        # for qi in quiz_items[:limit]:
        #     try:
        #         await admin_pb.collection("quizItems").update(
        #             qi.get("id", ""), {"status": "failed"}
        #         )
        #     except Exception:
        #         pass
        return

    patch = res.output  # QuizPatch_{n}

    # Update items with final data
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
            await admin_pb.collection("quizItems").update(
                qi.get("id", ""),
                {
                    "answers": answers,  # pyright: ignore[reportArgumentType]
                    "question": patch_qi.question,
                    "status": "final",
                },
            )
        except Exception as e:
            logging.exception("Failed to finalize %s: %s", qi.get("id"), e)


class GenerateQuizItems(BaseModel):
    limit: Annotated[int, Field(default=2, ge=2, le=5)]


@quizes_router.patch("/{quiz_id}")
async def generate_quiz_items(
    http: HTTPAsyncClient,
    admin_pb: AdminPB,
    quiz_id: str,
    dto: GenerateQuizItems,
    background: BackgroundTasks,
):
    # AUTH
    # pb_token = request.cookies.get("pb_token")
    # if not pb_token:
    #     raise HTTPException(status_code=401, detail=f"Unauthorized: no pb_token")
    # try:
    #     pb = PocketBase(settings.pb_url)
    #     pb._inners.auth.set_user({"token": pb_token, "record": {}})
    #     user = await pb.collection("users").auth.refresh()
    # except Exception as e:
    #     raise HTTPException(status_code=401, detail=f"Unauthorized: {e}")

    # SUBSCRIPTION
    # user_id = user.get("id", "")
    user_id = "lhjpor907gtxpry"

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
