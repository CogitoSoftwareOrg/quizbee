import time
from typing import Annotated
from src.apps.edge_api.adapters.in_.http.schemas import JobDto
from arq import ArqRedis
from pocketbase import PocketBase
from fastapi import Depends, HTTPException, Request

from src.lib.settings import settings

from ....app.contracts import EdgeAPIApp
from ....domain.constants import ARQ_QUEUE_NAME


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


async def enqueue_job(r: ArqRedis, job: JobDto, window_ms: int):
    now_s = int(time.time())
    window_s = max(1, window_ms // 1000)

    kwargs = job.get("kwargs", {})

    if job.get("queue"):
        kwargs["_queue_name"] = job.get("queue")
    else:
        kwargs["_queue_name"] = ARQ_QUEUE_NAME

    kwargs["pb_job_id"] = job.get("id")
    kwargs["pb_job_run_id"] = job.get("job_run_id")
    kwargs["_job_id"] = f"{settings.arq_job_prefix}{job.get('id')}:{now_s//window_s}"

    return await r.enqueue_job(job.name, **kwargs)
