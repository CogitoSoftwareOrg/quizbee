from dataclasses import asdict
from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    Form,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse, StreamingResponse

from src.lib.utils import cache_key, sse

from src.apps.v2.material_search.app.contracts import MaterialFile

from ....app.contracts import (
    PublicStartQuizCmd,
    PublicGenerateQuizItemsCmd,
    PublicFinalizeQuizCmd,
    PublicFinalizeAttemptCmd,
    PublicAskExplainerCmd,
    PublicAddMaterialCmd,
)

from .deps import (
    EdgeAPIAppDeps,
    UserTokenDeps,
)
from .schemas import StartQuizDto, PatchQuizDto, FinalizeQuizDto

edge_api_router = APIRouter(prefix="/v2", tags=["v2"], dependencies=[])


# Quiz Generator
@edge_api_router.put(
    "/quizes/{quiz_id}",
    dependencies=[],
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_quiz(
    dto: StartQuizDto,
    edge_api_app: EdgeAPIAppDeps,
    quiz_id: str,
    background: BackgroundTasks,
    token: UserTokenDeps,
):
    background.add_task(
        edge_api_app.start_quiz,
        PublicStartQuizCmd(
            token=token,
            quiz_id=quiz_id,
            cache_key=cache_key(dto.attempt_id),
        ),
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
    edge_api_app: EdgeAPIAppDeps,
    background: BackgroundTasks,
    token: UserTokenDeps,
):
    background.add_task(
        edge_api_app.generate_quiz_items,
        PublicGenerateQuizItemsCmd(
            token=token,
            quiz_id=quiz_id,
            cache_key=cache_key(dto.attempt_id),
            mode=dto.mode,
        ),
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
    edge_api_app: EdgeAPIAppDeps,
    token: UserTokenDeps,
    background: BackgroundTasks,
):
    background.add_task(
        edge_api_app.finalize_quiz,
        PublicFinalizeQuizCmd(
            quiz_id=quiz_id,
            token=token,
            cache_key=cache_key(dto.attempt_id),
        ),
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
    edge_api_app: EdgeAPIAppDeps,
    quiz_id: str,
    token: UserTokenDeps,
    background: BackgroundTasks,
):
    background.add_task(
        edge_api_app.finalize_attempt,
        PublicFinalizeAttemptCmd(
            quiz_id=quiz_id,
            cache_key=cache_key(attempt_id),
            attempt_id=attempt_id,
            token=token,
        ),
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
@edge_api_router.post("/materials", status_code=201)
async def add_material(
    token: UserTokenDeps,
    edge_api_app: EdgeAPIAppDeps,
    file: UploadFile = File(...),
    title: str = Form(...),
    material_id: str = Form(...),
):
    file_bytes = await file.read()
    material = await edge_api_app.add_material(
        PublicAddMaterialCmd(
            token=token,
            cache_key=cache_key(material_id),
            file=MaterialFile(
                file_name=file.filename or "unknown",
                file_bytes=file_bytes,
            ),
            title=title,
            material_id=material_id,
        )
    )

    file_size_mb = len(file_bytes) / (1024 * 1024)
    return JSONResponse(
        content={
            "id": material.id,
            "title": material.title,
            "filename": file.filename,
            "status": "uploaded",
            "success": True,
            "file_size_mb": round(file_size_mb, 2),
            "message": "Material uploaded successfully",
            "tokens": material.tokens,
            "kind": material.kind,
        }
    )
