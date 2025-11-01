from typing import Annotated
from arq import ArqRedis
from pocketbase import PocketBase
from fastapi import Depends, HTTPException, Request

from ....app.contracts import EdgeAPIApp


def get_user_token(request: Request) -> str:
    token = request.cookies.get("pb_token")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized: no pb_token")
    return token


UserTokenDeps = Annotated[str, Depends(get_user_token)]


def get_edge_api_app(request: Request) -> EdgeAPIApp:
    return request.app.state.edge_api_app


EdgeAPIAppDeps = Annotated[EdgeAPIApp, Depends(get_edge_api_app)]


def get_arq_pool(request: Request) -> ArqRedis:
    """Получить ARQ Redis pool из app.state для отправки задач в очередь."""
    return request.app.state.arq_pool


ArqPoolDeps = Annotated[ArqRedis, Depends(get_arq_pool)]


def get_admin_pb(request: Request) -> PocketBase:
    return request.app.state.admin_pb


AdminPBDeps = Annotated[PocketBase, Depends(get_admin_pb)]
