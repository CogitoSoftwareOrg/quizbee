from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    status,
)
from fastapi.responses import JSONResponse
from typing import Annotated

from pydantic import BaseModel, Field

from apps.auth import User, auth_user
from apps.billing import load_subscription
from apps.materials import user_owns_materials
from lib.clients import AdminPB, HTTPAsyncClient

from .ai import (
    generate_quiz_task,
    start_generating_quiz_task,
)

quizes_router = APIRouter(
    prefix="/quizes",
    tags=["quizes"],
    dependencies=[Depends(auth_user), Depends(load_subscription)],
)


class CreateQuizDto(BaseModel):
    quiz_id: str = Field(default="")
    attempt_id: str | None = Field(default=None)
    # number_of_questions: int = Field(default=10, ge=1, le=50)
    # material_ids: list[str] = Field(default=[])
    # query: str = Field(default="")
    # difficulty: str = Field(default="intermediate")


@quizes_router.post(
    "",
    dependencies=[
        Depends(user_owns_materials),
    ],
)
async def create_quiz(
    admin_pb: AdminPB,
    http: HTTPAsyncClient,
    user: User,
    dto: CreateQuizDto,
    background: BackgroundTasks,
):
    user_id = user.get("id", "")
    quiz_id = dto.quiz_id
    limit = 50

    attempt_id = dto.attempt_id
    if not attempt_id:
        quiz_attempt = await admin_pb.collection("quizAttempts").create(
            {
                "user": user_id,
                "quiz": quiz_id,
            }
        )
        attempt_id = quiz_attempt.get("id", "")

    background.add_task(
        start_generating_quiz_task, admin_pb, http, user_id, attempt_id, quiz_id, limit
    )

    return JSONResponse(
        content={
            "quiz_id": quiz_id,
            "quiz_attempt_id": attempt_id,
        },
        status_code=status.HTTP_202_ACCEPTED,
    )


class GenerateQuizItems(BaseModel):
    attempt_id: str = Field(default="")
    limit: Annotated[int, Field(default=50, ge=2, le=50)]


@quizes_router.patch("/{quiz_id}")
async def generate_quiz_items(
    admin_pb: AdminPB,
    http: HTTPAsyncClient,
    quiz_id: str,
    dto: GenerateQuizItems,
    background: BackgroundTasks,
    user: User,
):
    # Generate
    background.add_task(
        generate_quiz_task,
        admin_pb,
        http,
        user.get("id", ""),
        dto.attempt_id,
        quiz_id,
        dto.limit,
    )

    return JSONResponse(
        content={"scheduled": True, "quiz_id": quiz_id, "limit": dto.limit},
        status_code=status.HTTP_202_ACCEPTED,
    )
