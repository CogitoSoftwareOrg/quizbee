from enum import StrEnum
import logging
import httpx
from pocketbase.models.dtos import Record
from lib.clients import AdminPB, HTTPAsyncClient, langfuse_client
from lib.utils import cache_key
from lib.ai.models import QuizerDeps

from .agent import (
    QUIZER_COSTS,
    QUIZER_PRIORITY_COSTS,
    quizer_agent,
    event_stream_handler,
)


class GenMode(StrEnum):
    Continue = "continue"
    Regenerate = "regenerate"


async def generate_quiz_task(
    admin_pb: AdminPB,
    http: HTTPAsyncClient,
    user_id: str,
    attempt_id: str,
    quiz_id: str,
    limit: int,
    generation: int,
    mode: GenMode,
    priority: bool = False,
):
    quiz = await admin_pb.collection("quizes").get_one(
        quiz_id,
        options={
            "params": {
                "expand": "materials,quizItems_via_quiz",
            }
        },
    )

    materials = quiz.get("expand", {}).get("materials", [])
    logging.info("Materials order: %s", [m.get("id", "") for m in materials])

    prev_quiz_items, ready_items, holdout_items = _chunk_items(quiz, limit, mode)
    ready_items_ids = [qi.get("id", "") for qi in ready_items]
    for holdout_item in holdout_items:
        if holdout_item.get("status", "") in ("generated", "generating"):
            await admin_pb.collection("quizItems").update(
                holdout_item.get("id", ""), {"status": "blank"}
            )
    for ready_item in ready_items:
        if ready_item.get("status") in ("generating", "final"):
            continue
        await admin_pb.collection("quizItems").update(
            ready_item.get("id", ""),
            {"status": "generating"},
        )

    # Prepare request to LLM
    cancelled = False
    seen = 0
    prompt_cache_key = cache_key(attempt_id)
    try:
        with langfuse_client.start_as_current_span(name=f"quiz-patch") as span:
            async with quizer_agent.run_stream(
                deps=QuizerDeps(
                    quiz=quiz,
                    prev_quiz_items=prev_quiz_items,
                    materials=materials,
                    http=http,
                ),
                event_stream_handler=event_stream_handler,
                model_settings={
                    "extra_body": {
                        "reasoning_effort": "low",
                        # "service_tier": "priority" if priority else "default",
                        "service_tier": "default",
                        "prompt_cache_key": prompt_cache_key,
                    },
                },
            ) as result:
                stream = result.stream_output()
                async for partial in stream:
                    if partial.data.mode != "quiz":
                        raise ValueError(f"Unexpected output type: {type(partial)}")

                    if not await _same_generation(admin_pb, quiz_id, generation):
                        cancelled = True
                        break

                    items = partial.data.quiz_items or []
                    if len(items) > 0:
                        for qi_id, qi in zip(
                            ready_items_ids[seen : len(items)], items[seen:]
                        ):
                            if await _qi_is_final(admin_pb, qi_id):
                                continue

                            answers = [
                                {
                                    "content": a.answer,
                                    "explanation": a.explanation,
                                    "correct": a.correct,
                                }
                                for a in qi.answers
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

            usage = result.usage()
            input_nc = usage.input_tokens - usage.cache_read_tokens
            input_cah = usage.cache_read_tokens
            outp = usage.output_tokens

            costs = QUIZER_PRIORITY_COSTS if priority else QUIZER_COSTS

            input_nc_price = round(input_nc * costs.input_nc, 4)
            input_cah_price = round(input_cah * costs.input_cah, 4)
            outp_price = round(outp * costs.output, 4)

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
        if cancelled:
            logging.info(
                "Quiz %s stream ended due to graceful cancellation: %s",
                quiz_id,
                e,
            )
            return

        logging.exception("Agent run failed for quiz %s: %s", quiz_id, e)
        for qi in ready_items[seen:limit]:
            try:
                await admin_pb.collection("quizItems").update(
                    qi.get("id", ""), {"status": "failed"}
                )
            except Exception:
                pass
        return


async def generate_oneshot(
    admin_pb: AdminPB,
    http: HTTPAsyncClient,
    user_id: str,
    attempt_id: str,
    expanded_quiz: Record,
    limit: int,
    mode: GenMode,
):
    quiz_id = expanded_quiz.get("id", "")
    materials = expanded_quiz.get("expand", {}).get("materials", [])

    prev_items, ready_items, holdout_items = _chunk_items(expanded_quiz, limit, mode)
    ready_items_ids = [qi.get("id", "") for qi in ready_items]
    for holdout_item in holdout_items:
        if holdout_item.get("status", "") in ("generated", "generating"):
            await admin_pb.collection("quizItems").update(
                holdout_item.get("id", ""), {"status": "blank"}
            )

    for ready_item in ready_items:
        if ready_item.get("status") in ("generating", "final"):
            continue
        await admin_pb.collection("quizItems").update(
            ready_item.get("id", ""),
            {"status": "generating"},
        )

    prompt_cache_key = cache_key(attempt_id)
    try:
        with langfuse_client.start_as_current_span(name=f"quiz-patch") as span:
            res = await quizer_agent.run(
                deps=QuizerDeps(
                    quiz=expanded_quiz,
                    prev_quiz_items=prev_items,
                    materials=materials,
                    http=http,
                ),
                event_stream_handler=event_stream_handler,
                model_settings={
                    "extra_body": {
                        "prompt_cache_key": prompt_cache_key,
                    },
                },
            )
            payload = res.output.data
            if payload.mode != "quiz":
                raise ValueError(f"Unexpected output type: {type(payload)}")
            items = payload.quiz_items or []

            for qi_id, qi in zip(ready_items_ids, items):
                answers = [
                    {
                        "content": a.answer,
                        "explanation": a.explanation,
                        "correct": a.correct,
                    }
                    for a in qi.answers
                ]
                await admin_pb.collection("quizItems").update(
                    qi_id,
                    {
                        "status": "generated",
                        "answers": answers,  # pyright: ignore[reportArgumentType]
                        "question": qi.question,
                    },
                )
            usage = res.usage()
            input_nc = usage.input_tokens - usage.cache_read_tokens
            input_cah = usage.cache_read_tokens
            outp = usage.output_tokens

            input_nc_price = round(input_nc * QUIZER_COSTS.input_nc, 4)
            input_cah_price = round(input_cah * QUIZER_COSTS.input_cah, 4)
            outp_price = round(outp * QUIZER_COSTS.output, 4)

            span.update_trace(
                input=f"NC: {input_nc_price} + CAH: {input_cah_price} + OUTP: {outp_price} =>",
                output=f"Total: {input_nc_price + input_cah_price + outp_price}",
                user_id=user_id,
                session_id=attempt_id,
                metadata={
                    "quiz_id": quiz_id,
                },
            )

    except Exception as e:
        logging.exception("Agent run failed for quiz %s: %s", quiz_id, e)
        for ready_item in ready_items:
            try:
                await admin_pb.collection("quizItems").update(
                    ready_item.get("id", ""), {"status": "failed"}
                )
            except Exception:
                pass
        return


def _chunk_items(expanded_quiz: Record, limit: int, mode: GenMode):
    quiz_items = expanded_quiz.get("expand", {}).get("quizItems_via_quiz", [])
    quiz_items = sorted(
        quiz_items,
        key=lambda qi: qi.get("order", 0),
    )

    prev_quiz_items = [qi for qi in quiz_items if qi.get("status") == "final"]

    future_quiz_items = []
    if mode == GenMode.Regenerate:
        future_quiz_items = [qi for qi in quiz_items if qi.get("status") != "final"]
    elif mode == GenMode.Continue:
        future_quiz_items = [
            qi for qi in quiz_items if qi.get("status") not in ("final", "generated")
        ]

    limit = min(limit, len(future_quiz_items))
    ready_items = future_quiz_items[:limit]
    holdout_items = future_quiz_items[limit:]

    return (prev_quiz_items, ready_items, holdout_items)


async def _same_generation(admin_pb: AdminPB, quiz_id: str, expected: int) -> bool:
    gen = (await admin_pb.collection("quizes").get_one(quiz_id)).get("generation", 0)
    return gen == expected


async def _qi_is_final(admin_pb: AdminPB, qi_id: str) -> bool:
    qi_db = await admin_pb.collection("quizItems").get_one(qi_id)
    return qi_db.get("status") == "final"
