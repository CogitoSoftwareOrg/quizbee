from typing import Annotated
from fastapi import Depends, HTTPException, Request
from pocketbase.models.dtos import Record

from lib.settings import settings
from lib.clients import AdminPB
from apps.auth.middleware import User


def get_subscription(request: Request):
    return request.state.subscription


Subscription = Annotated[Record, Depends(get_subscription)]


async def load_subscription(request: Request, admin_pb: AdminPB, user: User):
    user_id = user.get("id")
    subscription = await admin_pb.collection("subscriptions").get_first(
        options={"params": {"filter": f"user = '{user_id}'"}},
    )
    request.state.subscription = subscription


async def billing_protection(request: Request, subscription: Subscription):
    if not subscription:
        raise HTTPException(status_code=401, detail=f"Unauthorized: no subscription")
