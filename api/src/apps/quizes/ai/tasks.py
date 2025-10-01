import asyncio
import base64
import contextlib
import logging
import httpx
from pocketbase import FileUpload
from pydantic_ai.direct import model_request
from pydantic_ai.messages import (
    ModelRequest,
    SystemPromptPart,
    TextPart,
    UserPromptPart,
)
from lib.clients.http import HTTPAsyncClient
from lib.clients.pb import AdminPB
from lib.clients.tiktoken import ENCODERS
from lib.config import LLMS
from apps.materials.utils import load_file_bytes, load_materials_context
from lib.clients import langfuse_client

from .models import DynamicConfig, QuizerDeps, make_quiz_patch_model
from .agent import quizer_agent
from .agent import event_stream_handler


async def start_generating_quiz_task(
    admin_pb: AdminPB,
    http: HTTPAsyncClient,
    user_id: str,
    quiz_id: str,
    limit: int,
):
    quiz = await admin_pb.collection("quizes").get_one(
        quiz_id,
        options={
            "params": {"expand": "materials"},
        },
    )
    materials = quiz.get("expand", {}).get("materials", [])

    await admin_pb.collection("quizes").update(
        quiz_id,
        {
            "status": "preparing",
        },
    )

    # Load materials context
    contents = []
    for m in materials:
        mid = m.get("id", "")
        # simple text or image
        if m.get("kind") == "simple":
            f = m.get("file", "")
            content = await load_file_bytes(http, "materials", mid, f)
            if f.endswith((".md", ".txt", ".csv", ".json")):
                content = content.decode("utf-8")
            elif f.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                content = base64.b64encode(content).decode("ascii")
            contents.append(content)
        elif m.get("kind") == "complex":
            images = m.get("images", [])
            txt = m.get("textFile", "")
            if txt:
                content = await load_file_bytes(http, "materials", mid, txt)
                content = content.decode("utf-8")
                contents.append(content)
            for image in images:
                content = await load_file_bytes(http, "materials", mid, image)
                content = base64.b64encode(content).decode("ascii")
                contents.append(content)

    # Truncate content somehow
    tokens = ENCODERS[LLMS.GPT_5_MINI].encode("\n".join(contents))
    truncated = tokens[:80_000]
    contents = ENCODERS[LLMS.GPT_5_MINI].decode(truncated)

    # Generate summary
    summary = ""
    if len(contents) > 0:
        with langfuse_client.start_as_current_span(name="quiz-summary") as span:
            part = (
                await model_request(
                    LLMS.GPT_5_MINI,
                    messages=[
                        ModelRequest(
                            parts=[
                                SystemPromptPart(
                                    content="Summarize the following materials context"
                                ),
                                UserPromptPart(content=contents),
                            ]
                        )
                    ],
                    model_settings={
                        "max_tokens": 8000,
                        # "temperature": 0.2,
                        # "top_p": 1.0,
                    },
                )
            ).parts[0]
            span.update_trace(
                user_id=user_id,
                session_id=quiz_id,
            )
        summary = part.content if isinstance(part, TextPart) else ""

    quiz = await admin_pb.collection("quizes").update(
        quiz_id,
        {
            "status": "creating",
            "summary": summary,
            "materialsContext": FileUpload(
                ("materialsContext.txt", bytes(contents, "utf-8"))
            ),
        },
    )

    await generate_quiz_task(admin_pb, http, user_id, quiz_id, limit)


async def generate_quiz_task(
    admin_pb: AdminPB,
    http: HTTPAsyncClient,
    user_id: str,
    quiz_id: str,
    limit: int,
):
    quiz = await admin_pb.collection("quizes").get_one(
        quiz_id,
        options={
            "params": {
                "expand": "materials,quizItems_via_quiz",
            }
        },
    )
    generation = quiz.get("generation", 0) + 1
    await admin_pb.collection("quizes").update(
        quiz_id,
        {"generation": generation},
    )

    materials = quiz.get("expand", {}).get("materials", [])
    quiz_items = quiz.get("expand", {}).get("quizItems_via_quiz", [])
    quiz_items = sorted(
        quiz_items,
        key=lambda qi: qi.get("order", 0),
    )

    prev_quiz_items = [qi for qi in quiz_items if qi.get("status") == "final"]
    future_quiz_items = [qi for qi in quiz_items if qi.get("status") != "final"]

    limit = min(limit, len(future_quiz_items))
    quiz_items = future_quiz_items[:limit]  # ALL not final quiz items for now!

    quiz_items_ids = [qi.get("id", "") for qi in quiz_items]

    # Mark as "generating"
    for qi in quiz_items[:limit]:
        try:
            if qi.get("status") in ("generating", "final"):
                continue
            await admin_pb.collection("quizItems").update(
                qi.get("id", ""),
                {"status": "generating"},
            )
        except Exception as e:
            logging.exception("Failed to set generating for %s: %s", qi.get("id"), e)

    # Prepare request to LLM
    dynamic_config = DynamicConfig(**quiz.get("dynamicConfig", {}))
    q = quiz.get("query", "")
    materials_context_file = quiz.get("materialsContext", "")
    if materials_context_file:
        materials_context = await load_materials_context(
            http, quiz_id, materials_context_file
        )
    else:
        materials_context = ""

    cancelled = False
    seen = 0

    try:
        with langfuse_client.start_as_current_span(name="quiz-patch") as span:
            span.update_trace(
                user_id=user_id,
                session_id=quiz_id,
            )

            async with quizer_agent.run_stream(
                q,
                deps=QuizerDeps(
                    quiz=quiz,
                    prev_quiz_items=prev_quiz_items,
                    materials=materials,
                    dynamic_config=dynamic_config,
                    materials_context=materials_context,
                ),
                output_type=make_quiz_patch_model(limit),
                # event_stream_handler=event_stream_handler,
            ) as result:
                stream = result.stream_output()
                async for partial in stream:
                    if not await _same_generation(admin_pb, quiz_id, generation):
                        cancelled = True
                        break

                    items = partial.quiz_items or []
                    if len(items) > 0:
                        for qi_id, qi in zip(
                            quiz_items_ids[seen : len(items)], items[seen:]
                        ):
                            if await _qi_is_final(admin_pb, qi_id):
                                continue

                            answers = [
                                {
                                    "content": wa.answer,
                                    "explanation": wa.explanation,
                                    "correct": False,
                                }
                                for wa in qi.wrong_answers
                            ] + [
                                {
                                    "content": qi.right_answer.answer,
                                    "explanation": qi.right_answer.explanation,
                                    "correct": True,
                                }
                            ]
                            try:
                                await admin_pb.collection("quizItems").update(
                                    qi_id,
                                    {
                                        "answers": answers,  # pyright: ignore[reportArgumentType]
                                        "question": qi.question,
                                        "status": "generated",
                                    },
                                )
                            except Exception as e:
                                logging.exception("Failed to finalize %s: %s", qi_id, e)

                        seen = len(items)

    except httpx.ReadError as e:
        if cancelled:
            logging.info(
                "Quiz %s stream ended due to graceful cancellation: %s",
                quiz_id,
                e,
            )
            return
        raise

    except RuntimeError as e:
        if cancelled and "asynchronous generator is already running" in str(e):
            logging.info(
                "Quiz %s stream ended due to graceful cancellation (generator already running): %s",
                quiz_id,
                e,
            )
            return
        raise

    except Exception as e:
        logging.exception("Agent run failed for quiz %s: %s", quiz_id, e)
        for qi in quiz_items[seen:limit]:
            try:
                # if await _qi_is_final(admin_pb, qi.get("id", "")):
                # continue
                await admin_pb.collection("quizItems").update(
                    qi.get("id", ""), {"status": "failed"}
                )
            except Exception:
                pass
        return


async def _same_generation(admin_pb: AdminPB, quiz_id: str, expected: int) -> bool:
    gen = (await admin_pb.collection("quizes").get_one(quiz_id)).get("generation", 0)
    return gen == expected


async def _qi_is_final(admin_pb: AdminPB, qi_id: str) -> bool:
    qi_db = await admin_pb.collection("quizItems").get_one(qi_id)
    return qi_db.get("status") == "final"
