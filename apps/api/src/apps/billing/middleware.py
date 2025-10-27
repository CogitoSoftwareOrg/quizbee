from typing import Annotated
from fastapi import Depends, HTTPException, Request
from pocketbase.models.dtos import Record

from src.lib.clients import AdminPBDeps as AdminPB
from src.apps.auth.middleware import User

from .utils import ensure_active_and_maybe_reset, remaining


def get_subscription(request: Request):
    return request.state.subscription


Subscription = Annotated[Record, Depends(get_subscription)]


async def load_subscription(request: Request, admin_pb: AdminPB, user: User):
    user_id = user.get("id")
    subscription = await admin_pb.collection("subscriptions").get_first(
        options={"params": {"filter": f"user = '{user_id}'"}},
    )
    request.state.subscription = subscription


async def quiz_patch_quota_protection(
    request: Request, user: User, subscription: Subscription, admin_pb: AdminPB
):
    if not subscription:
        raise HTTPException(status_code=401, detail=f"Unauthorized: no subscription")
    subscription_id = subscription.get("id", "")

    await ensure_active_and_maybe_reset(admin_pb, subscription)

    body = await request.json()
    quiz_id = request.path_params.get("quiz_id") or body.get("quiz_id") or ""
    if not quiz_id:
        raise HTTPException(status_code=400, detail=f"Quiz ID is required")
    quiz = await admin_pb.collection("quizes").get_one(
        quiz_id, options={"params": {"filter": f"author = '{user.get('id')}'"}}
    )

    cost = abs(int(body.get("limit", 5)))

    remained = remaining(subscription, "quizItems")
    if cost > remained:
        raise HTTPException(status_code=400, detail=f"Quiz items limit exceeded")

    await admin_pb.collection("subscriptions").update(
        subscription_id, {"quizItemsUsage+": cost}
    )


async def explainer_call_quota_protection(
    request: Request, user: User, subscription: Subscription, admin_pb: AdminPB
):
    if not subscription:
        raise HTTPException(status_code=401, detail=f"Unauthorized: no subscription")
    subscription_id = subscription.get("id", "")

    await ensure_active_and_maybe_reset(admin_pb, subscription)

    try:
        body = await request.json()
    except Exception:
        body = {}

    attempt_id = request.query_params.get("attempt", "") or body.get("attempt_id", "")
    quiz_attempt = await admin_pb.collection("quizAttempts").get_one(
        attempt_id, options={"params": {"filter": f"user = '{user.get('id')}'"}}
    )
    if not quiz_attempt:
        raise HTTPException(status_code=404, detail=f"Quiz attempt not found")

    remained = remaining(subscription, "quizItems")
    if remained <= 0:
        raise HTTPException(status_code=400, detail=f"Quiz items limit exceeded")

    await admin_pb.collection("subscriptions").update(
        subscription_id, {"quizItemsUsage+": 1}
    )
