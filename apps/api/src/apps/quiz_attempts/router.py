import logging
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import JSONResponse
import httpx

from src.apps.auth import User, auth_user
from src.apps.billing import load_subscription, Subscription
from src.apps.quizes.ai import summary_and_index
from src.lib.clients import AdminPB, langfuse_client, HTTPAsyncClient, MeilisearchClient
from src.lib.utils import cache_key, update_span_with_result

from .ai import FEEDBACKER_COSTS, FEEDBACKER_LLM, FeedbackerDeps, Feedbacker


quiz_attempts_router = APIRouter(
    prefix="/quiz_attempts",
    tags=["attempts"],
    dependencies=[Depends(auth_user), Depends(load_subscription)],
)


async def _generate_feedback_task(
    admin_pb: AdminPB, http: HTTPAsyncClient, feedbacker: Feedbacker, attempt_id: str
):
    quiz_attempt = await admin_pb.collection("quizAttempts").get_one(
        attempt_id,
        options={"params": {"expand": "quiz,quiz.quizItems_via_quiz,quiz.materials"}},
    )
    user_id = quiz_attempt.get("user", "")
    attempt_id = quiz_attempt.get("id", "")
    quiz = quiz_attempt.get("expand", {}).get("quiz", {})
    quiz_items = quiz.get("expand", {}).get("quizItems_via_quiz", [])

    deps = FeedbackerDeps(
        quiz=quiz,
        quiz_items=quiz_items,
        quiz_attempt=quiz_attempt,
        http=http,
    )

    prompt_cache_key = cache_key(attempt_id)
    with langfuse_client.start_as_current_span(name="feedbacker-agent") as span:
        res = await feedbacker.run(
            deps=deps,
            model_settings={
                "extra_body": {
                    "reasoning_effort": "low",
                    "prompt_cache_key": prompt_cache_key,
                }
            },
        )

        payload = res.output.data
        if payload.mode != "feedback":
            raise ValueError(f"Unexpected output type: {type(res.output)}")

        await update_span_with_result(
            langfuse_client, res, span, user_id, attempt_id, FEEDBACKER_LLM
        )

    await admin_pb.collection("quizAttempts").update(
        attempt_id,
        {
            "feedback": payload.feedback.model_dump_json(),
        },
    )


@quiz_attempts_router.put("/{attempt_id}")
async def update_quiz_attempt_with_feedback(
    admin_pb: AdminPB,
    user: User,
    sub: Subscription,
    feedbacker: Feedbacker,
    meilisearch_client: MeilisearchClient,
    attempt_id: str,
    background: BackgroundTasks,
    http: HTTPAsyncClient,
):
    # CRUD
    quiz_attempt = await admin_pb.collection("quizAttempts").get_one(
        attempt_id,
        options={
            "params": {
                "expand": "quiz,quiz.quizItems_via_quiz,quiz.materials_via_quiz"
            },
        },
    )
    quiz = quiz_attempt.get("expand", {}).get("quiz", {})

    # Only summarize and index if quiz is not final
    if quiz.get("status") != "final":
        await admin_pb.collection("quizes").update(
            quiz.get("id", ""),
            {"status": "answered"},
        )

        background.add_task(
            summary_and_index,
            admin_pb,
            http,
            meilisearch_client,
            user.get("id", ""),
            attempt_id,
        )

    # No feedback -> generate feedback
    feedback = quiz_attempt.get("feedback")
    logging.info(f"Feedback: {feedback}")
    if feedback is None:
        if sub.get("tariff") == "free":
            await admin_pb.collection("quizAttempts").update(
                attempt_id, {"feedback": {}}
            )
        else:
            background.add_task(
                _generate_feedback_task, admin_pb, http, feedbacker, attempt_id
            )
    else:
        logging.info(f"Feedback already exists: {feedback}")

    return JSONResponse(
        content={"scheduled": True, "attempt_id": attempt_id},
        status_code=status.HTTP_202_ACCEPTED,
    )
