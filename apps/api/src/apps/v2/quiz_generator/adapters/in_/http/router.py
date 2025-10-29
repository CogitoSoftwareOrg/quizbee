from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from fastapi.responses import JSONResponse

from src.lib.utils.cache_key import cache_key

from ....app.contracts import FinalizeCmd, GenMode, GenerateCmd

from .schemas import FinalizeQuizDto, PatchQuizDto, StartQuizDto
from .deps import QuizGeneratorAppDeps

quiz_generator_router = APIRouter(
    prefix="/v2/quizes",
    tags=["v2"],
    dependencies=[],
)


@quiz_generator_router.put(
    "/{quiz_id}",
    dependencies=[],
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_quiz(
    dto: StartQuizDto,
    quiz_generator: QuizGeneratorAppDeps,
    quiz_id: str,
    background: BackgroundTasks,
    request: Request,
):
    token = request.cookies.get("pb_token")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized: no pb_token")

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


@quiz_generator_router.patch(
    "/{quiz_id}",
    dependencies=[],
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_quiz_items(
    dto: PatchQuizDto,
    quiz_id: str,
    quiz_generator: QuizGeneratorAppDeps,
    request: Request,
    background: BackgroundTasks,
):
    token = request.cookies.get("pb_token")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized: no pb_token")

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


@quiz_generator_router.put(
    "/{quiz_id}/finalize",
    dependencies=[],
    status_code=status.HTTP_202_ACCEPTED,
)
async def finalize_quiz(
    dto: FinalizeQuizDto,
    quiz_id: str,
    quiz_generator: QuizGeneratorAppDeps,
    request: Request,
    background: BackgroundTasks,
):
    token = request.cookies.get("pb_token")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized: no pb_token")

    background.add_task(
        quiz_generator.finalize,
        FinalizeCmd(
            quiz_id=quiz_id,
            token=token,
            cache_key=cache_key(dto.attempt_id),
        ),
    )

    return JSONResponse(
        content={"scheduled": True, "quiz_id": quiz_id},
    )
