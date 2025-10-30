from dataclasses import asdict
from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse, StreamingResponse

from src.lib.utils import cache_key, sse

from src.apps.v2.quiz_attempter.app.contracts import (
    AskExplainerCmd,
    FinalizeCmd as FinalizeAttemptCmd,
)
from src.apps.v2.quiz_generator.app.contracts import (
    GenerateCmd,
    GenMode,
    FinalizeCmd as FinalizeQuizCmd,
)
from src.apps.v2.material_search.app.contracts import AddMaterialCmd, MaterialFile

from .deps import (
    MaterialSearchAppDeps,
    QuizAttempterAppDeps,
    QuizGeneratorAppDeps,
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
    quiz_generator: QuizGeneratorAppDeps,
    quiz_id: str,
    background: BackgroundTasks,
    token: UserTokenDeps,
):
    background.add_task(
        quiz_generator.start,
        GenerateCmd(
            token=token,
            quiz_id=quiz_id,
            mode=GenMode.Continue,
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
    quiz_generator: QuizGeneratorAppDeps,
    background: BackgroundTasks,
    token: UserTokenDeps,
):
    background.add_task(
        quiz_generator.generate,
        GenerateCmd(
            quiz_id=quiz_id,
            token=token,
            mode=dto.mode,
            cache_key=cache_key(dto.attempt_id),
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
    quiz_generator: QuizGeneratorAppDeps,
    token: UserTokenDeps,
    background: BackgroundTasks,
):
    background.add_task(
        quiz_generator.finalize,
        FinalizeQuizCmd(
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
    quiz_attempter_app: QuizAttempterAppDeps,
    quiz_id: str,
    token: UserTokenDeps,
    background: BackgroundTasks,
):
    background.add_task(
        quiz_attempter_app.finalize,
        FinalizeAttemptCmd(
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
    quiz_attempter_app: QuizAttempterAppDeps,
    query: str = Query(alias="q"),
    item_id: str = Query(alias="item"),
):
    async def event_generator():
        async for run in quiz_attempter_app.ask_explainer(
            AskExplainerCmd(
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
    material_search_app: MaterialSearchAppDeps,
    file: UploadFile = File(...),
    title: str = Form(...),
    material_id: str = Form(...),
):
    file_bytes = await file.read()
    material = await material_search_app.add_material(
        AddMaterialCmd(
            token=token,
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
