from pocketbase import PocketBase, FileUpload
from fastapi import (
    APIRouter,
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

from pydantic import BaseModel

from src.apps.messages import pb_to_ai
from src.lib.settings import settings
from src.lib.clients import AdminPB

from .ai import QUIZER_LLM, quizer_agent, QuizerDeps

quizes_router = APIRouter(prefix="/quizes", tags=["quizes"])


@quizes_router.post("/")
async def create_quiz_endpoint(
    admin_pb: AdminPB,
    request: Request,
    query: str = Form(),
    old_file_names: list[str] = Form(default=[]),
    files: list[UploadFile] = File(default=[]),
    user_id: str = Form(),
    with_attempt: bool = Form(default=True),
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
            "question": query,
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


@quizes_router.post("/{quiz_id}")
async def generate_quiz_items(
    admin_pb: AdminPB,
    quiz_id: str,
):
    LIMIT = 2

    quiz_items = await admin_pb.collection("quizeItems").get_full_list(
        options={
            "params": {
                "filter": f"quiz = '{quiz_id}' && status = 'blank'",
                "sort": "order",
            }
        },
    )
    if not quiz_items:
        raise HTTPException(status_code=404, detail="Quiz items not found")

    for i in range(LIMIT):
        quiz_item = quiz_items[i]
        await admin_pb.collection("quizeItems").update(
            quiz_item.get("id", ""),
            {
                "status": "generating",
            },
        )

    return JSONResponse(
        content={"quiz_items": quiz_items}, status_code=status.HTTP_200_OK
    )
