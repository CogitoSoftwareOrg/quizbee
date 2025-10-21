import json
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from apps.auth import auth_user
from apps.billing import (
    Subscription,
    load_subscription,
    explainer_call_quota_protection,
)
from lib.clients import AdminPB, HTTPAsyncClient, langfuse_client
from lib.utils import sse, update_span_with_result
from apps.auth import User
from lib.utils.cache_key import cache_key

from .pb_to_ai import pb_to_ai
from .ai import EXPLAINER_COSTS, EXPLAINER_LLM, ExplainerDeps, explainer_agent

messages_router = APIRouter(
    prefix="/messages",
    tags=["messages"],
    dependencies=[
        Depends(auth_user),
        Depends(load_subscription),
    ],
)


@messages_router.get(
    "/sse",
    dependencies=[Depends(explainer_call_quota_protection)],
)
async def sse_messages(
    admin_pb: AdminPB,
    http: HTTPAsyncClient,
    user: User,
    query: str = Query(alias="q"),
    attempt_id: str = Query(alias="attempt"),
    item_id: str = Query(alias="item"),
):
    if not query:
        raise HTTPException(status_code=400, detail="No query provided")
    if not attempt_id:
        raise HTTPException(status_code=400, detail="No attempt ID provided")

    pb_history = await admin_pb.collection("messages").get_full_list(
        options={
            "params": {"filter": f"quizAttempt = '{attempt_id}'", "sort": "-created"}
        },
    )
    pb_history.reverse()
    history = pb_to_ai(pb_history)

    quiz_attempt = await admin_pb.collection("quizAttempts").get_one(
        attempt_id,
        options={"params": {"expand": "quiz,quiz.quizItems_via_quiz,quiz.materials"}},
    )
    choices = quiz_attempt.get("choices", [])
    quiz = quiz_attempt.get("expand", {}).get("quiz", {})
    quiz_items = quiz.get("expand", {}).get("quizItems_via_quiz", [])

    current_item = [item for item in quiz_items if item.get("id") == item_id][0]
    current_decision = [
        decision for decision in choices if decision.get("itemId") == item_id
    ][0]

    # GUARD
    user_id = quiz_attempt.get("user", "")
    attempt_id = quiz_attempt.get("id", "")
    prompt_cache_key = cache_key(attempt_id)

    user_msg = await admin_pb.collection("messages").create(
        {
            "quizAttempt": attempt_id,
            "content": query,
            "role": "user",
            "status": "final",
            "metadata": {"itemId": item_id},
        }
    )
    user_msg_id = user_msg.get("id", "")

    ai_msg = await admin_pb.collection("messages").create(
        {
            "quizAttempt": attempt_id,
            "content": "",
            "role": "ai",
            "status": "streaming",
            "metadata": {"itemId": item_id},
        }
    )
    ai_msg_id = ai_msg.get("id", "")

    async def event_generator():
        content = ""

        deps = ExplainerDeps(
            http=http,
            quiz=quiz,
            current_item=current_item,
            current_decision=current_decision,
        )

        with langfuse_client.start_as_current_span(name="explainer-agent") as span:
            async with explainer_agent.run_stream(
                query,
                message_history=history,
                deps=deps,
                model_settings={
                    "extra_body": {
                        "reasoning_effort": "low",
                        "prompt_cache_key": prompt_cache_key,
                    }
                },
                # event_stream_handler=event_stream_handler,
            ) as run:
                i = 0
                async for output in run.stream_output():
                    if output.data.mode != "explanation":
                        raise ValueError(f"Unexpected output type: {type(output)}")
                    text = output.data.explanation[len(content) :]
                    content += text
                    yield sse(
                        "chunk", json.dumps({"text": text, "msg_id": ai_msg_id, "i": i})
                    )
            await update_span_with_result(
                langfuse_client, run, span, user_id, attempt_id, EXPLAINER_LLM
            )

        await admin_pb.collection("messages").update(
            ai_msg_id,
            {
                "content": content,
                "status": "final",
            },
        )
        yield sse("done", json.dumps({}))

    return StreamingResponse(event_generator(), media_type="text/event-stream")


class CreateMessageDto(BaseModel):
    query: str
    attempt_id: str
    item_id: str


@messages_router.post("", dependencies=[Depends(explainer_call_quota_protection)])
async def create_message(
    admin_pb: AdminPB,
    http: HTTPAsyncClient,
    dto: CreateMessageDto,
):
    pb_history = await admin_pb.collection("messages").get_full_list(
        options={
            "params": {
                "filter": f"quizAttempt = '{dto.attempt_id}'",
                "sort": "-created",
            }
        },
    )
    pb_history.reverse()
    history = pb_to_ai(pb_history)

    quiz_attempt = await admin_pb.collection("quizAttempts").get_one(
        dto.attempt_id,
        options={
            "params": {"expand": "quiz,quiz.quizItems_via_quiz,quiz.materials_via_quiz"}
        },
    )
    choices = quiz_attempt.get("choices", [])
    quiz = quiz_attempt.get("expand", {}).get("quiz", {})
    quiz_items = quiz.get("expand", {}).get("quizItems_via_quiz", [])
    materials = quiz.get("expand", {}).get("materials_via_quiz", [])

    current_item = [item for item in quiz_items if item.get("id") == dto.item_id][0]
    current_decision = [
        decision for decision in choices if decision.get("itemId") == dto.item_id
    ][0]

    # GUARD
    user_id = quiz_attempt.get("user", "")
    attempt_id = quiz_attempt.get("id", "")
    prompt_cache_key = cache_key(attempt_id)

    user_msg = await admin_pb.collection("messages").create(
        {
            "quizAttempt": attempt_id,
            "content": dto.query,
            "role": "user",
            "status": "final",
            "metadata": {"itemId": dto.item_id},
        }
    )
    user_msg_id = user_msg.get("id", "")

    ai_msg = await admin_pb.collection("messages").create(
        {
            "quizAttempt": dto.attempt_id,
            "content": "",
            "role": "ai",
            "status": "streaming",
            "metadata": {"itemId": dto.item_id},
        }
    )
    ai_msg_id = ai_msg.get("id", "")

    with langfuse_client.start_as_current_span(name="explainer-agent") as span:
        res = await explainer_agent.run(
            dto.query,
            message_history=history,
            deps=ExplainerDeps(
                http=http,
                quiz=quiz,
                current_item=current_item,
                current_decision=current_decision,
            ),
            model_settings={"extra_body": {"prompt_cache_key": prompt_cache_key}},
            # event_stream_handler=event_stream_handler,
        )
        payload = res.output.data
        if payload.mode != "explanation":
            raise ValueError(f"Unexpected output type: {type(res.output)}")

        await update_span_with_result(
            langfuse_client, res, span, user_id, attempt_id, EXPLAINER_LLM
        )

    await admin_pb.collection("messages").update(
        ai_msg_id,
        {
            "content": payload.explanation,
            "status": "final",
        },
    )
