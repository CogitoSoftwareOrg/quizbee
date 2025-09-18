import logging
from pocketbase import PocketBase  # pyright: ignore[reportAttributeAccessIssue]
from fastapi import FastAPI, HTTPException, Request, Depends
from typing import Annotated

from src.lib.settings import settings


def get_admin_pb(request: Request) -> PocketBase:
    return request.app.state.admin_pb


AdminPB = Annotated[PocketBase, Depends(get_admin_pb)]


def init_admin_pb(app: FastAPI) -> None:
    app.state.admin_pb = PocketBase(settings.pb_url)


async def ensure_admin_pb(request: Request):
    pb = get_admin_pb(request)
    token = pb._inners.auth._token

    if not token or pb._inners.auth._is_token_expired():
        try:
            a = await pb.collection("_superusers").auth.with_password(
                settings.pb_email, settings.pb_password
            )
            pb._inners.auth.set_user(
                {"token": a.get("token", ""), "record": a.get("record", {})}
            )
        except Exception as e:
            raise HTTPException(500, "Can't auth PB admin")