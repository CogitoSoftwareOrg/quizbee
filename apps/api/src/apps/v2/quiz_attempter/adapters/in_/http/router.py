from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import JSONResponse

from src.lib.utils import cache_key

from ....di import QuizAttempterAppDeps
from ....app.contracts import FinalizeCmd

quiz_attempter_router = APIRouter(
    prefix="/v2/quizes/{quiz_id}/attempts", tags=["v2"], dependencies=[]
)


@quiz_attempter_router.put("/{attempt_id}", status_code=201)
async def finalize_attempt(
    attempt_id: str,
    quiz_attempter_app: QuizAttempterAppDeps,
    quiz_id: str,
    token: str,
    background: BackgroundTasks,
):
    background.add_task(
        quiz_attempter_app.finalize,
        FinalizeCmd(
            quiz_id=quiz_id,
            cache_key=cache_key(attempt_id),
            attempt_id=attempt_id,
            token=token,
        ),
    )

    return JSONResponse(
        content={"scheduled": True, "quiz_id": quiz_id, "attempt_id": attempt_id}
    )
