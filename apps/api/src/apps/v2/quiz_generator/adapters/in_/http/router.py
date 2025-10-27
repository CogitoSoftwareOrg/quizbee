from fastapi import APIRouter
from fastapi import Depends

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


@quiz_generator_router.post(
    "",
    dependencies=[
        Depends(http_guard_user_owns_materials),
        Depends(http_guard_quiz_patch_quota_protection),
    ],
)
async def create_quiz(): ...
