import asyncio
import json
import logging
import httpx
from meilisearch_python_sdk.models.search import Hybrid
from pocketbase import FileUpload
from pocketbase.models.dtos import Record

from apps.materials.utils import (
    load_file_text,
)

from lib.ai.models import QuizerOutput, QuizerDeps, SummarizerOutput, SummarizerDeps
from lib.ai.models.quizer import DynamicConfig
from lib.clients import (
    HTTPAsyncClient,
    MeilisearchClient,
    langfuse_client,
    AdminPB,
    ENCODERS,
)
from lib.config import LLMS
from lib.config.llms import LLMSCosts
from lib.utils import cache_key

from .summirizer import summarizer_agent
from .quizer import quizer_agent, event_stream_handler


async def summary_and_index(
    admin_pb: AdminPB,
    http: HTTPAsyncClient,
    meilisearch_client: MeilisearchClient,
    user_id: str,
    attempt_id: str,
    quiz: Record,
    texts: str,
):
    summary = ""
    if len(texts) == 0:
        logging.warning("No texts to summarize and index")
        return

    summaries_index = meilisearch_client.index("quizSummaries")

    prompt_cache_key = cache_key(attempt_id)

    # SUMMARIZE
    with langfuse_client.start_as_current_span(name="quiz-summary") as span:
        res = await summarizer_agent.run(
            deps=SummarizerDeps(
                http=http,
                quiz=quiz,
                materials_context=texts,
            ),
            model_settings={"extra_body": {"prompt_cache_key": prompt_cache_key}},
        )

        if res.output.data.mode != "summary":
            raise ValueError(f"Unexpected output type: {type(res.output)}")

        summary = res.output.data.summary

        usage = res.usage()
        input_nc = usage.input_tokens - usage.cache_read_tokens
        input_cah = usage.cache_read_tokens
        outp = usage.output_tokens

        input_nc_price = input_nc * LLMSCosts.GPT_5_MINI.input_nc
        input_cah_price = input_cah * LLMSCosts.GPT_5_MINI.input_cah
        outp_price = outp * LLMSCosts.GPT_5_MINI.output

        span.update_trace(
            input=f"NC: {round(input_nc_price, 3)} + CAH: {round(input_cah_price, 3)} = {round(input_nc_price + input_cah_price, 3)}",
            output=f"OUTP: {round(outp_price, 3)}",
            user_id=user_id,
            session_id=attempt_id,
            metadata={
                "input_nc_price": input_nc_price,
                "input_cah_price": input_cah_price,
                "outp_price": outp_price,
                "total_price": input_nc_price + input_cah_price + outp_price,
            },
        )

    # INDEX SUMMARY
    index_task = await summaries_index.add_documents(
        [
            {
                "id": quiz.get("id", ""),
                "summary": summary,
                "userId": user_id,
                "quizId": quiz.get("id", ""),
            }
        ],
        primary_key="id",
    )
    task = await meilisearch_client.wait_for_task(
        index_task.task_uid,
        timeout_in_ms=int(30 * 1000),
        interval_in_ms=int(0.5 * 1000),
    )

    if task.status == "succeeded":
        logging.info("Quiz summary indexed: %s", task)
        await admin_pb.collection("quizes").update(
            quiz.get("id", ""),
            {"summary": summary},
        )
    elif task.status == "failed":
        logging.error("Failed to index quiz summary: %s", task)
    else:
        logging.error("Unknown task status: %s", task)


async def start_generating_quiz_task(
    admin_pb: AdminPB,
    http: HTTPAsyncClient,
    meilisearch_client: MeilisearchClient,
    user_id: str,
    attempt_id: str,
    quiz_id: str,
    limit: int,
):
    summaries_index = meilisearch_client.index("quizSummaries")

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
    texts = []
    for m in materials:
        mid = m.get("id", "")
        if m.get("kind") == "simple":
            f = m.get("file", "")
            content = await load_file_text(http, "materials", mid, f)
            if f.endswith((".md", ".txt", ".csv", ".json")):
                texts.append(content)

        elif m.get("kind") == "complex":
            images = m.get("images", [])
            txt = m.get("textFile", "")
            if txt:
                content = await load_file_text(http, "materials", mid, txt)
                texts.append(content)
    texts = "\n".join(texts)

    # Truncate content somehow
    tokens = ENCODERS[LLMS.GPT_5_MINI].encode(texts)
    truncated = tokens[:25_000] + tokens[-25_000:]
    estimated = tokens[:4000] + tokens[-4000:]
    texts = ENCODERS[LLMS.GPT_5_MINI].decode(truncated)

    estimated_summary = ENCODERS[LLMS.GPT_5_MINI].decode(estimated)
    logging.info("Estimated summary: %s", len(estimated_summary))
    search_result = await summaries_index.search(
        query=estimated_summary,
        hybrid=Hybrid(
            semantic_ratio=0.75,
            embedder="quizSummaries",
        ),
        filter=[f"userId = {user_id}"],
        limit=5,
    )
    hits = search_result.hits
    quiz_ids = [hit.get("quizId", "") for hit in hits]
    questions = []
    for qid in quiz_ids:
        q = await admin_pb.collection("quizes").get_one(
            qid,
            options={
                "params": {
                    "expand": "quizItems_via_quiz",
                }
            },
        )
        items = q.get("expand", {}).get("quizItems_via_quiz", [])
        qs = [item.get("question", "") for item in items]
        questions.extend([q for q in qs if q])

    questions = questions[:50]
    config = DynamicConfig(**quiz.get("dynamicConfig", {}))
    config.negativeQuestions = questions

    quiz = await admin_pb.collection("quizes").update(
        quiz_id,
        {
            "status": "creating",
            "summary": estimated_summary,
            "materialsContext": FileUpload(
                ("materialsContext.txt", bytes(texts, "utf-8"))
            ),
            "dynamicConfig": json.dumps(config.model_dump()),
        },
    )

    async with asyncio.TaskGroup() as tg:
        tg.create_task(
            summary_and_index(
                admin_pb, http, meilisearch_client, user_id, attempt_id, quiz, texts
            )
        )
        tg.create_task(
            generate_quiz_task(
                admin_pb, http, user_id, attempt_id, quiz_id, limit, "regenerate"
            )
        )


async def generate_quiz_task(
    admin_pb: AdminPB,
    http: HTTPAsyncClient,
    user_id: str,
    attempt_id: str,
    quiz_id: str,
    limit: int,
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
    generation = quiz.get("generation", 0) + 1
    await admin_pb.collection("quizes").update(
        quiz_id,
        {"generation": generation},
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
        with langfuse_client.start_as_current_span(name="quiz-patch") as span:
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

            input_nc_price = input_nc * LLMSCosts.GPT_5_MINI.input_nc
            input_cah_price = input_cah * LLMSCosts.GPT_5_MINI.input_cah
            outp_price = outp * LLMSCosts.GPT_5_MINI.output

            span.update_trace(
                input=f"NC: {round(input_nc_price, 3)} + CAH: {round(input_cah_price, 3)} = {round(input_nc_price + input_cah_price, 3)}",
                output=f"OUTP: {round(outp_price, 3)}",
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
