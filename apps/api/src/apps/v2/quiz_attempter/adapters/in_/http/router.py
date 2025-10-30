from dataclasses import asdict
import json
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status, Query
from fastapi.responses import JSONResponse, StreamingResponse

from src.lib.utils import cache_key, sse

from ....app.contracts import FinalizeCmd, AskExplainerCmd

from .deps import QuizAttempterAppDeps

quiz_attempter_router = APIRouter(
    prefix="/v2/quizes/{quiz_id}/attempts", tags=["v2"], dependencies=[]
)


@quiz_attempter_router.put("/{attempt_id}", status_code=status.HTTP_202_ACCEPTED)
async def finalize_attempt(
    attempt_id: str,
    quiz_attempter_app: QuizAttempterAppDeps,
    quiz_id: str,
    request: Request,
    background: BackgroundTasks,
):
    token = request.cookies.get("pb_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized: no pb_token"
        )

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


@quiz_attempter_router.get(
    "/{attempt_id}/messages/sse", status_code=status.HTTP_201_CREATED
)
async def ask_explainer(
    quiz_id: str,
    attempt_id: str,
    quiz_attempter_app: QuizAttempterAppDeps,
    request: Request,
    query: str = Query(alias="q"),
    item_id: str = Query(alias="item"),
):
    token = request.cookies.get("pb_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized: no pb_token"
        )

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
