import json
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse

from apps.auth import auth_user
from apps.billing import Subscription, load_subscription
from apps.materials.utils import load_file_text
from lib.clients import AdminPB, HTTPAsyncClient, langfuse_client
from lib.utils import sse
from apps.auth import User

from .pb_to_ai import pb_to_ai
from .ai import ExplainerDeps, explainer_agent

messages_router = APIRouter(
    prefix="/messages",
    tags=["messages"],
    dependencies=[
        Depends(auth_user),
        Depends(load_subscription),
    ],
)


@messages_router.get("/sse")
async def sse_messages(
    admin_pb: AdminPB,
    http: HTTPAsyncClient,
    user: User,
    subscription: Subscription,
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
        options={
            "params": {"expand": "quiz,quiz.quizItems_via_quiz,quiz.materials_via_quiz"}
        },
    )
    choices = quiz_attempt.get("choices", [])
    quiz = quiz_attempt.get("expand", {}).get("quiz", {})
    quiz_items = quiz.get("expand", {}).get("quizItems_via_quiz", [])
    materials = quiz.get("expand", {}).get("materials_via_quiz", [])

    current_item = [item for item in quiz_items if item.get("id") == item_id][0]
    current_decision = [
        decision for decision in choices if decision.get("itemId") == item_id
    ][0]

    # GUARD
    if quiz_attempt.get("user") != user.get("id"):
        raise HTTPException(
            status_code=403, detail="You are not allowed to interact with this attempt"
        )

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
            materials_context="",
            current_item=current_item,
            current_decision=current_decision,
        )

        with langfuse_client.start_as_current_span(name="explainer-agent") as span:
            async with explainer_agent.run_stream(
                query,
                message_history=history,
                deps=deps,
                # event_stream_handler=event_stream_handler,
            ) as run:
                i = 0
                async for text in run.stream_text(delta=True):
                    i += 1
                    content += text
                    yield sse(
                        "chunk", json.dumps({"text": text, "msg_id": ai_msg_id, "i": i})
                    )
            span.update_trace(
                user_id=user.get("id", ""),
                session_id=quiz_attempt.get("id", ""),
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
