from typing import Annotated
from fastapi import Request, Depends, HTTPException
from arq import ArqRedis
from pocketbase import PocketBase

from src.lib.settings import settings

from src.lib.pb_admin import ensure_admin_auth


async def http_ensure_admin_pb(request: Request):
    pb: PocketBase = request.app.state.admin_pb
    lock = request.app.state.admin_auth_lock

    tok = pb._inners.auth._token
    if tok and not pb._inners.auth._is_token_expired():
        return pb

    async with lock:
        tok = pb._inners.auth._token
        if tok and not pb._inners.auth._is_token_expired():
            return pb

        pb._inners.auth.clean()
        try:
            a = await pb.collection("_superusers").auth.with_password(
                settings.pb_email, settings.pb_password
            )
        except Exception:
            pb._inners.auth.clean()
            a = await pb.collection("_superusers").auth.with_password(
                settings.pb_email, settings.pb_password
            )

        pb._inners.auth.set_user(
            {"token": a.get("token", ""), "record": a.get("record", {})}
        )
        return pb


def get_arq_pool(request: Request) -> ArqRedis:
    """Получить ARQ Redis pool из app.state для отправки задач в очередь."""
    return request.app.state.arq_pool


ArqPoolDeps = Annotated[ArqRedis, Depends(get_arq_pool)]
