from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    status,
)
from fastapi.responses import JSONResponse
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from apps.auth import User, auth_user
from apps.billing import (
    load_subscription,
    quiz_patch_quota_protection,
)
from apps.materials import user_owns_materials
from lib.clients import AdminPB, HTTPAsyncClient, MeilisearchClient

from .ai import (
    generate_quiz_task,
    start_generating_quiz_task,
    GenMode,
    generate_oneshot,
    summary_and_index,
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
        Depends(quiz_patch_quota_protection),
    ],
)
async def create_quiz(
    admin_pb: AdminPB,
    http: HTTPAsyncClient,
    meilisearch_client: MeilisearchClient,
    user: User,
    dto: CreateQuizDto,
    background: BackgroundTasks,
):
    user_id = user.get("id", "")
    quiz_id = dto.quiz_id
    quiz = await admin_pb.collection("quizes").get_one(quiz_id)
    limit = 5

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
        start_generating_quiz_task,
        admin_pb,
        http,
        meilisearch_client,
        user_id,
        attempt_id,
        quiz_id,
        limit,
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
    limit: Annotated[int, Field(default=5, ge=2, le=50)]
    mode: Annotated[GenMode, Field(default=GenMode.Regenerate)]


@quizes_router.patch(
    "/{quiz_id}",
    dependencies=[Depends(quiz_patch_quota_protection)],
)
async def generate_quiz_items(
    admin_pb: AdminPB,
    http: HTTPAsyncClient,
    meilisearch_client: MeilisearchClient,
    quiz_id: str,
    dto: GenerateQuizItems,
    background: BackgroundTasks,
    user: User,
):
    quiz = await admin_pb.collection("quizes").get_one(
        quiz_id,
        options={
            "params": {
                "expand": "materials,quizItems_via_quiz",
            }
        },
    )
    generation = quiz.get("generation", 0)

    if dto.mode == GenMode.Regenerate:
        generation += 1
        await admin_pb.collection("quizes").update(
            quiz_id,
            {"generation+": 1},
        )

    # Generate
    background.add_task(
        generate_quiz_task,
        admin_pb,
        http,
        user.get("id", ""),
        dto.attempt_id,
        quiz_id,
        dto.limit,
        generation,
        dto.mode,
    )
    # background.add_task(
    #     generate_oneshot,
    #     admin_pb,
    #     http,
    #     user.get("id", ""),
    #     dto.attempt_id,
    #     quiz,
    #     dto.limit,
    #     dto.mode,
    # )

    return JSONResponse(
        content={"scheduled": True, "quiz_id": quiz_id, "limit": dto.limit},
        status_code=status.HTTP_202_ACCEPTED,
    )
