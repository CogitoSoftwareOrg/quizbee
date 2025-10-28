from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.responses import JSONResponse

from src.lib.utils.cache_key import cache_key

from src.apps.v2.user_auth.di import UserDeps

from ....app.contracts import GenMode, GenerateCmd
from ....di import QuizGeneratorAppDeps

from .schemas import PatchQuizDto

from .deps import (
    http_guard_and_set_user,
    http_guard_user_owns_materials,
    http_guard_quiz_patch_quota_protection,
)

quiz_generator_router = APIRouter(
    prefix="/v2/quizes",
    tags=["quizes"],
    dependencies=[Depends(http_guard_and_set_user)],
)


@quiz_generator_router.put(
    "/{quiz_id}",
    dependencies=[
        Depends(http_guard_user_owns_materials),
        Depends(http_guard_quiz_patch_quota_protection),
    ],
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_quiz(
    quiz_generator_app: QuizGeneratorAppDeps,
    quiz_id: str,
    user: UserDeps,
    background: BackgroundTasks,
):
    attempt = await quiz_generator_app.create_attempt(quiz_id, user.id)

    background.add_task(
        quiz_generator_app.start,
        GenerateCmd(
            quiz_id=quiz_id,
            user_id=user.id,
            mode=GenMode.Continue,
            cache_key=cache_key(attempt.id),
        ),
    )

    return JSONResponse(
        content={"scheduled": True, "quiz_id": quiz_id, "attempt_id": attempt.id},
    )


@quiz_generator_router.patch(
    "/{quiz_id}",
    dependencies=[
        Depends(http_guard_user_owns_materials),
        Depends(http_guard_quiz_patch_quota_protection),
    ],
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_quiz_items(
    dto: PatchQuizDto,
    quiz_id: str,
    quiz_generator_app: QuizGeneratorAppDeps,
    user: UserDeps,
    background: BackgroundTasks,
):
    background.add_task(
        quiz_generator_app.generate,
        GenerateCmd(
            quiz_id=quiz_id,
            user_id=user.id,
            mode=dto.mode,
            cache_key=cache_key(dto.attempt_id),
        ),
    )

    return JSONResponse(
        content={"scheduled": True, "quiz_id": quiz_id},
    )
