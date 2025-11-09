from typing import Annotated
from fastapi import Request, Depends
from arq import ArqRedis

from src.lib.settings import settings


async def http_ensure_admin_pb(request: Request):
    pb = request.app.state.admin_pb
    token = pb._inners.auth._token

    if not token or pb._inners.auth._is_token_expired():
        a = await pb.collection("_superusers").auth.with_password(
            settings.pb_email, settings.pb_password
        )
        pb._inners.auth.set_user(
            {"token": a.get("token", ""), "record": a.get("record", {})}
        )


def get_arq_pool(request: Request) -> ArqRedis:
    """Получить ARQ Redis pool из app.state для отправки задач в очередь."""
    return request.app.state.arq_pool


ArqPoolDeps = Annotated[ArqRedis, Depends(get_arq_pool)]
