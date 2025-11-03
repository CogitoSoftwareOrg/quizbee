from dataclasses import asdict
from fastapi import (
    APIRouter,
    File,
    Form,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse, StreamingResponse

from src.lib.utils import cache_key, sse

from src.apps.material_search.app.contracts import MaterialFile

from ....app.contracts import (
    PublicRemoveMaterialCmd,
    PublicStartQuizCmd,
    PublicGenerateQuizItemsCmd,
    PublicFinalizeQuizCmd,
    PublicFinalizeAttemptCmd,
    PublicAskExplainerCmd,
    PublicAddMaterialCmd,
)

from ....domain.constants import ARQ_QUEUE_NAME
from ....app.contracts import JobName

from .deps import (
    EdgeAPIAppDeps,
    UserTokenDeps,
    ArqPoolDeps,
)
from .schemas import StartQuizDto, PatchQuizDto, FinalizeQuizDto


edge_api_router = APIRouter(prefix="", tags=["Edge Logic"], dependencies=[])


# Quiz Generator
@edge_api_router.put(
    "/quizes/{quiz_id}",
    dependencies=[],
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_quiz(
    dto: StartQuizDto,
    quiz_id: str,
    arq_pool: ArqPoolDeps,
    token: UserTokenDeps,
):
    cmd = PublicStartQuizCmd(
        token=token,
        quiz_id=quiz_id,
        cache_key=cache_key(dto.attempt_id),
    )
    await arq_pool.enqueue_job(
        JobName.start_quiz, asdict(cmd), _queue_name=ARQ_QUEUE_NAME
    )

    return JSONResponse(
        content={"scheduled": True, "quiz_id": quiz_id, "attempt_id": dto.attempt_id},
    )


@edge_api_router.patch(
    "/quizes/{quiz_id}",
    dependencies=[],
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_quiz_items(
    dto: PatchQuizDto,
    quiz_id: str,
    arq_pool: ArqPoolDeps,
    token: UserTokenDeps,
):
    cmd = PublicGenerateQuizItemsCmd(
        token=token,
        quiz_id=quiz_id,
        cache_key=cache_key(dto.attempt_id),
        mode=dto.mode,
    )
    await arq_pool.enqueue_job(
        JobName.generate_quiz_items, asdict(cmd), _queue_name=ARQ_QUEUE_NAME
    )

    return JSONResponse(content={"scheduled": True, "quiz_id": quiz_id})


@edge_api_router.put(
    "/quizes/{quiz_id}/finalize",
    dependencies=[],
    status_code=status.HTTP_202_ACCEPTED,
)
async def finalize_quiz(
    dto: FinalizeQuizDto,
    quiz_id: str,
    token: UserTokenDeps,
    arq_pool: ArqPoolDeps,
):
    cmd = PublicFinalizeQuizCmd(
        quiz_id=quiz_id,
        token=token,
        cache_key=cache_key(dto.attempt_id),
    )
    await arq_pool.enqueue_job(
        JobName.finalize_quiz, asdict(cmd), _queue_name=ARQ_QUEUE_NAME
    )

    return JSONResponse(
        content={"scheduled": True, "quiz_id": quiz_id},
    )


# Attempter
@edge_api_router.put(
    "/quizes/{quiz_id}/attempts/{attempt_id}", status_code=status.HTTP_202_ACCEPTED
)
async def finalize_attempt(
    attempt_id: str,
    quiz_id: str,
    token: UserTokenDeps,
    arq_pool: ArqPoolDeps,
):
    cmd = PublicFinalizeAttemptCmd(
        quiz_id=quiz_id,
        cache_key=cache_key(attempt_id),
        attempt_id=attempt_id,
        token=token,
    )
    await arq_pool.enqueue_job(
        JobName.finalize_attempt, asdict(cmd), _queue_name=ARQ_QUEUE_NAME
    )

    return JSONResponse(
        content={"scheduled": True, "quiz_id": quiz_id, "attempt_id": attempt_id}
    )


@edge_api_router.get(
    "/quizes/{quiz_id}/attempts/{attempt_id}/messages/sse",
    status_code=status.HTTP_201_CREATED,
)
async def ask_explainer(
    quiz_id: str,
    attempt_id: str,
    token: UserTokenDeps,
    edge_api_app: EdgeAPIAppDeps,
    query: str = Query(alias="q"),
    item_id: str = Query(alias="item"),
):
    async def event_generator():
        async for run in edge_api_app.ask_explainer(
            PublicAskExplainerCmd(
                quiz_id=quiz_id,
                cache_key=cache_key(attempt_id),
                query=query,
                item_id=item_id,
                attempt_id=attempt_id,
                token=token,
            ),
        ):
            yield sse(run.status, asdict(run))

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# Material Search
@edge_api_router.post("/quizes/{quiz_id}/materials", status_code=201)
async def add_material(
    quiz_id: str,
    arq_pool: ArqPoolDeps,
    token: UserTokenDeps,
    edge_api_app: EdgeAPIAppDeps,
    file: UploadFile = File(...),
    title: str = Form(...),
    material_id: str = Form(...),
):
    file_bytes = await file.read()
    cmd = PublicAddMaterialCmd(
        quiz_id=quiz_id,
        token=token,
        cache_key=cache_key(material_id),
        file=MaterialFile(
            file_name=file.filename or "unknown",
            file_bytes=file_bytes,
        ),
        title=title,
        material_id=material_id,
    )
    await arq_pool.enqueue_job(
        JobName.add_material, asdict(cmd), _queue_name=ARQ_QUEUE_NAME
    )
    return JSONResponse(content={"scheduled": True, "material_id": material_id})


@edge_api_router.delete(
    "/quizes/{quiz_id}/materials/{material_id}", status_code=status.HTTP_202_ACCEPTED
)
async def remove_material(
    quiz_id: str,
    material_id: str,
    token: UserTokenDeps,
    arq_pool: ArqPoolDeps,
):
    cmd = PublicRemoveMaterialCmd(
        quiz_id=quiz_id,
        material_id=material_id,
        token=token,
        cache_key=cache_key(material_id),
    )
    await arq_pool.enqueue_job(
        JobName.remove_material, asdict(cmd), _queue_name=ARQ_QUEUE_NAME
    )
    return JSONResponse(content={"scheduled": True, "material_id": material_id})
