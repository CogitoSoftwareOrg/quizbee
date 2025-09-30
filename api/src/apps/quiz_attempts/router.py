import logging
from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.responses import JSONResponse
import httpx

from apps.auth import auth_user
from apps.billing import load_subscription
from apps.materials.utils import load_materials_context
from lib.clients import AdminPB, langfuse_client, HTTPAsyncClient

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
    quiz = quiz_attempt.get("expand", {}).get("quiz", {})
    quiz_items = quiz.get("expand", {}).get("quizItems_via_quiz", [])

    materials_context_file = quiz.get("materialsContext", "")
    if materials_context_file:
        materials_context = await load_materials_context(
            http, quiz.get("id"), materials_context_file
        )
    else:
        materials_context = ""

    with langfuse_client.start_as_current_span(name="feedbacker-agent") as span:
        feedback = await feedbacker_agent.run(
            "Give me feedback on my quiz attempt",
            deps=FeedbackerDeps(
                quiz=quiz,
                quiz_items=quiz_items,
                quiz_attempt=quiz_attempt,
                materials_context=materials_context,
            ),
        )
        span.update_trace(
            user_id=quiz_attempt.get("user", ""),
            session_id=quiz_attempt.get("id", ""),
        )

    await admin_pb.collection("quizAttempts").update(
        attempt_id,
        {
            "feedback": feedback.output.feedback.model_dump_json(),
        },
    )

    # Update quiz with adds if not final
    status = quiz.get("status")
    if status != "final":
        adds = feedback.output.additional
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
