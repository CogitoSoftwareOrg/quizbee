import logging
import httpx
from pocketbase.models.dtos import Record
from lib.clients import AdminPB, HTTPAsyncClient, langfuse_client
from lib.config.llms import LLMSCosts
from lib.utils import cache_key
from lib.ai.models import QuizerDeps

from .agent import quizer_agent, event_stream_handler


async def generate_quiz_task(
    admin_pb: AdminPB,
    http: HTTPAsyncClient,
    user_id: str,
    attempt_id: str,
    quiz_id: str,
    limit: int,
    generation: int,
    mode: str,
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

    quiz_items = quiz.get("expand", {}).get("quizItems_via_quiz", [])
    quiz_items = sorted(
        quiz_items,
        key=lambda qi: qi.get("order", 0),
    )

    prev_quiz_items = [qi for qi in quiz_items if qi.get("status") == "final"]

    future_quiz_items = []
    if mode == "regenerate":
        future_quiz_items = [qi for qi in quiz_items if qi.get("status") != "final"]
    elif mode == "continue":
        future_quiz_items = [
            qi for qi in quiz_items if qi.get("status") not in ("final", "generated")
        ]

    limit = min(limit, len(future_quiz_items))
    quiz_items = future_quiz_items[:limit]
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
    cancelled = False
    seen = 0
    prompt_cache_key = cache_key(attempt_id)
    try:
        with langfuse_client.start_as_current_span(
            name=f"quiz-patch-{attempt_id}-{generation}"
        ) as span:
            async with quizer_agent.run_stream(
                deps=QuizerDeps(
                    quiz=quiz,
                    prev_quiz_items=prev_quiz_items,
                    materials=materials,
                    http=http,
                ),
                event_stream_handler=event_stream_handler,
                model_settings={"extra_body": {"prompt_cache_key": prompt_cache_key}},
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
                            quiz_items_ids[seen : len(items)], items[seen:]
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
