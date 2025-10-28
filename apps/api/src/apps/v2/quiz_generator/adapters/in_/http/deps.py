from fastapi import HTTPException, Request

from src.lib.clients import AdminPBDeps

from src.apps.v2.user_auth.di import AuthUserAppDeps, SubscriptionDeps, UserDeps
from src.apps.v2.user_auth.domain.errors import NoTokenError, ForbiddenError

from ....domain.constants import PATCH_LIMIT


async def http_guard_and_set_user(request: Request, auth_user_app: AuthUserAppDeps):
    try:
        token = request.cookies.get("pb_token")
        user, sub = await auth_user_app.validate(token)
        request.state.user = user
        request.state.subscription = sub
    except NoTokenError as e:
        raise HTTPException(status_code=401, detail=e.message)
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=e.message)


async def http_guard_user_owns_materials(
    request: Request, admin_pb: AdminPBDeps, user: UserDeps
):
    dto = await request.json()
    user_id = user.id
    material_ids = dto.get("material_ids", [])

    if not material_ids:
        return

    for material_id in material_ids:
        material = await admin_pb.collection("materials").get_one(material_id)
        if material.get("user") != user_id:
            raise HTTPException(
                status_code=401, detail=f"Unauthorized: material not owned by user"
            )


async def http_guard_quiz_patch_quota_protection(
    request: Request, user: UserDeps, sub: SubscriptionDeps, admin_pb: AdminPBDeps
):
    body = await request.json()
    quiz_id = request.path_params.get("quiz_id") or body.get("quiz_id") or ""
    if not quiz_id:
        raise HTTPException(status_code=400, detail=f"Quiz ID is required")
    quiz = await admin_pb.collection("quizes").get_one(
        quiz_id, options={"params": {"filter": f"author = '{user.id}'"}}
    )

    remained = sub.quiz_items_limit - sub.quiz_items_usage
    if PATCH_LIMIT > remained:
        raise HTTPException(status_code=400, detail=f"Quiz items limit exceeded")

    await admin_pb.collection("subscriptions").update(
        sub.id, {"quizItemsUsage+": PATCH_LIMIT}
    )
