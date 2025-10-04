import logging

from lib.ai.models import SummarizerDeps
from lib.clients import AdminPB, HTTPAsyncClient, MeilisearchClient, langfuse_client
from lib.config.llms import LLMSCosts
from lib.utils import cache_key

from apps.materials.utils import load_file_text

from .agent import summarizer_agent


async def summary_and_index(
    admin_pb: AdminPB,
    http: HTTPAsyncClient,
    meilisearch_client: MeilisearchClient,
    user_id: str,
    attempt_id: str,
    quiz_id: str,
):
    quiz = await admin_pb.collection("quizes").get_one(
        quiz_id,
        options={
            "params": {"expand": "materials"},
        },
    )

    texts = await load_file_text(
        http, "quizes", quiz_id, quiz.get("materialsContext", "")
    )

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

        payload = res.output.data
        if payload.mode != "summary":
            raise ValueError(f"Unexpected output type: {type(res.output)}")

        summary = payload.summary

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
