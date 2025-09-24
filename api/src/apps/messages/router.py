import json
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse

from apps.materials.utils import materials_to_ai_docs
from src.lib.clients import AdminPB
from src.lib.utils import sse
from src.apps.auth import User

from .pb_to_ai import pb_to_ai
from .ai import ExplainerDeps, explainer_agent

messages_router = APIRouter(prefix="/messages", tags=["messages"], dependencies=[])


@messages_router.get("/see")
async def see_messages(
    admin_pb: AdminPB,
    user: User,
    query: str = Query(alias="q"),
    attempt_id: str = Query(alias="attempt"),
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
            "params": {"expand": "quiz,quizItems_via_quiz,quiz.materials_via_quiz"}
        },
    )
    quiz = quiz_attempt.get("expand", {}).get("quiz", {})
    quiz_items = quiz.get("expand", {}).get("quizItems_via_quiz", [])
    materials = quiz.get("expand", {}).get("materials_via_quiz", [])
    ai_docs = await materials_to_ai_docs(materials)

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
            "metadata": {},
        }
    )
    user_msg_id = user_msg.get("id", "")

    ai_msg = await admin_pb.collection("messages").create(
        {
            "quizAttempt": attempt_id,
            "content": "",
            "role": "ai",
            "status": "streaming",
            "metadata": {},
        }
    )
    ai_msg_id = ai_msg.get("id", "")

    async def event_generator():
        content = ""

        deps = ExplainerDeps(
            admin_pb=admin_pb,
            quiz_attempt=quiz_attempt,
            quiz=quiz,
            quiz_items=quiz_items,
        )

        async with explainer_agent.run_stream(
            [query, *ai_docs],
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

    return StreamingResponse(event_generator(), media_type="text/event-stream")
