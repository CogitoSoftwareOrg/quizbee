import logging
from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.responses import JSONResponse
import httpx

from apps.auth import auth_user
from apps.billing import load_subscription
from lib.clients import AdminPB, langfuse_client, HTTPAsyncClient
from lib.utils import cache_key

from .ai import FeedbackerDeps, feedbacker_agent


quiz_attempts_router = APIRouter(
    prefix="/quiz_attempts",
    tags=["attempts", "feedback"],
    dependencies=[Depends(auth_user), Depends(load_subscription)],
)


async def _generate_feedback_task(
    admin_pb: AdminPB, http: httpx.AsyncClient, attempt_id: str
):
    quiz_attempt = await admin_pb.collection("quizAttempts").get_one(
        attempt_id,
        options={
            "params": {"expand": "quiz,quiz.quizItems_via_quiz,quiz.materials_via_quiz"}
        },
    )
    user_id = quiz_attempt.get("user", "")
    attempt_id = quiz_attempt.get("id", "")
    quiz = quiz_attempt.get("expand", {}).get("quiz", {})
    quiz_items = quiz.get("expand", {}).get("quizItems_via_quiz", [])

    prompt_cache_key = cache_key(attempt_id)
    with langfuse_client.start_as_current_span(name="feedbacker-agent") as span:
        res = await feedbacker_agent.run(
            deps=FeedbackerDeps(
                quiz=quiz,
                quiz_items=quiz_items,
                quiz_attempt=quiz_attempt,
                http=http,
            ),
            model_settings={"extra_body": {"prompt_cache_key": prompt_cache_key}},
        )

        if res.output.data.mode != "feedback":
            raise ValueError(f"Unexpected output type: {type(res.output)}")

        data = res.output.data
        usage = res.usage()
        read_cache_input = usage.cache_read_tokens
        write_cache_input = usage.cache_write_tokens

        span.update_trace(
            user_id=user_id,
            session_id=attempt_id,
            metadata={
                "read_cache_input": read_cache_input,
                "write_cache_input": write_cache_input,
                "prompt_cache_key": prompt_cache_key,
            },
        )

    await admin_pb.collection("quizAttempts").update(
        attempt_id,
        {
            "feedback": data.feedback.model_dump_json(),
        },
    )

    # Update quiz with adds if not final
    status = quiz.get("status")
    if status != "final":
        adds = data.additional
        await admin_pb.collection("quizes").update(
            quiz.get("id"),
            {"title": adds.quiz_title, "status": "final"},
        )


@quiz_attempts_router.put("/{attempt_id}")
async def update_quiz_attempt_with_feedback(
    admin_pb: AdminPB,
    attempt_id: str,
    background: BackgroundTasks,
    http: HTTPAsyncClient,
):

    background.add_task(_generate_feedback_task, admin_pb, http, attempt_id)

    return JSONResponse(
        content={"scheduled": True, "attempt_id": attempt_id},
        status_code=status.HTTP_202_ACCEPTED,
    )
