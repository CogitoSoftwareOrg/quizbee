import logging
from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.responses import JSONResponse
import httpx

from apps.auth import User, auth_user
from apps.billing import load_subscription
from apps.quizes.ai import summary_and_index
from lib.clients import AdminPB, langfuse_client, HTTPAsyncClient, MeilisearchClient
from lib.config.llms import LLMSCosts
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

        payload = res.output.data
        if payload.mode != "feedback":
            raise ValueError(f"Unexpected output type: {type(res.output)}")

        usage = res.usage()
        input_nc = usage.input_tokens - usage.cache_read_tokens
        input_cah = usage.cache_read_tokens
        outp = usage.output_tokens

        input_nc_price = round(input_nc * LLMSCosts.GPT_5_MINI.input_nc, 4)
        input_cah_price = round(input_cah * LLMSCosts.GPT_5_MINI.input_cah, 4)
        outp_price = round(outp * LLMSCosts.GPT_5_MINI.output, 4)

        span.update_trace(
            input=f"NC: {input_nc_price} + CAH: {input_cah_price} => {input_nc_price + input_cah_price}",
            output=f"OUTP: {outp_price} => Total: {input_nc_price + input_cah_price + outp_price}",
            user_id=user_id,
            session_id=attempt_id,
            metadata={
                "input_nc_price": input_nc_price,
                "input_cah_price": input_cah_price,
                "outp_price": outp_price,
                "total_price": input_nc_price + input_cah_price + outp_price,
            },
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
    meilisearch_client: MeilisearchClient,
    attempt_id: str,
    background: BackgroundTasks,
    http: HTTPAsyncClient,
):

    # Generate feedback
    background.add_task(_generate_feedback_task, admin_pb, http, attempt_id)

    # Summarize and index
    attempt = await admin_pb.collection("quizAttempts").get_one(
        attempt_id,
    )
    quiz_id = attempt.get("quiz", "")
    quiz = await admin_pb.collection("quizes").get_one(
        quiz_id,
        options={
            "params": {"expand": "materials,quizItems_via_quiz"},
        },
    )
    # Only summarize and index if quiz is not final
    if quiz.get("status") != "final":
        background.add_task(
            summary_and_index,
            admin_pb,
            http,
            meilisearch_client,
            user.get("id", ""),
            attempt_id,
        )

    return JSONResponse(
        content={"scheduled": True, "attempt_id": attempt_id},
        status_code=status.HTTP_202_ACCEPTED,
    )
