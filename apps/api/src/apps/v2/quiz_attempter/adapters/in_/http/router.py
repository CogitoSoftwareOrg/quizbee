from fastapi import APIRouter
from fastapi import Depends

router = APIRouter(
    prefix="/v2/quizes/{quiz_id}/attempts", tags=["attempts"], dependencies=[]
)


@router.put("/{attempt_id}", status_code=201)
async def finalize_attempt(
    # quiz_attempter_app: QuizAttempterAppDeps,
    quiz_id: str,
    token: str,
): ...


# return await quiz_attempter_app.create_attempt(CreateAttemptCmd(quiz_id=quiz_id, token=token))
