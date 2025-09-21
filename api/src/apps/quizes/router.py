from pocketbase import PocketBase, FileUpload
from fastapi import APIRouter, Form, Request, Query, HTTPException, File, UploadFile
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

    quiz_attempt = await admin_pb.collection("quizAttempts").create(
        {
            "user": user_id,
            "quiz": quiz.get("id", ""),
        }
    )

    return JSONResponse(
        content={
            "quiz_attempt_id": quiz_attempt.get("id", ""),
            "quiz_id": quiz.get("id", ""),
        }
    )
