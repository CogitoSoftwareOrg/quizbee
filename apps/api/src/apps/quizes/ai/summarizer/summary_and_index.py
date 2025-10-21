import logging
import json

from lib.ai.models import SummarizerDeps
from lib.clients import AdminPB, HTTPAsyncClient, MeilisearchClient, langfuse_client
from lib.utils import cache_key, update_span_with_result

from apps.materials.utils import load_file_text

from .agent import SUMMARIZER_COSTS, SUMMARIZER_LLM, summarizer_agent


async def summary_and_index(
    admin_pb: AdminPB,
    http: HTTPAsyncClient,
    meilisearch_client: MeilisearchClient,
    user_id: str,
    attempt_id: str,
    force: bool = False,
):
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
    if quiz.get("status") == "final" and not force:
        logging.info("Quiz is already final, skipping summary and index")
        return

    # Prepare quiz items
    quiz_items = quiz.get("expand", {}).get("quizItems_via_quiz", [])
    questions = [qi.get("question", "") for qi in quiz_items]
    item_contents = "\n\n".join(
        [
            f"Question: {qi.get('question', '')}\nAnswers:\n{qi.get('answers', [])}"
            for qi in quiz_items
        ]
    )

    texts = await load_file_text(
        http, "quizes", quiz_id, quiz.get("materialsContext", "")
    )

    summaries_index = meilisearch_client.index("quizSummaries")

    prompt_cache_key = cache_key(attempt_id)

    # SUMMARIZE
    with langfuse_client.start_as_current_span(name="quiz-summary") as span:
        res = await summarizer_agent.run(
            deps=SummarizerDeps(
                http=http,
                quiz=quiz,
                materials_context=texts,
                quiz_contents=item_contents,
            ),
            model_settings={
                "extra_body": {
                    "reasoning_effort": "low",
                    "prompt_cache_key": prompt_cache_key,
                }
            },
        )

        payload = res.output.data
        if payload.mode != "summary":
            raise ValueError(f"Unexpected output type: {type(res.output)}")

        summary = payload.summary

        await update_span_with_result(
            langfuse_client, res, span, user_id, attempt_id, SUMMARIZER_LLM
        )

    adds = payload.additional
    await admin_pb.collection("quizes").update(
        quiz_id,
        {
            "title": adds.quiz_title,
            "status": "final",
            "slug": f"{adds.quiz_slug}-{quiz_id[:4]}",
            "tags": json.dumps(adds.quiz_tags),
            "summary": summary,
            "category": adds.quiz_category,
        },
    )

    full_summary = f"Summary: {summary}\n\nTags: {adds.quiz_tags}\n\nTitle: {adds.quiz_title}\n\nQuiz questions: {questions}"

    # INDEX SUMMARY
    index_task = await summaries_index.add_documents(
        [
            {
                "id": quiz_id,
                "summary": full_summary,
                "userId": user_id,
                "quizId": quiz_id,
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
    elif task.status == "failed":
        logging.error("Failed to index quiz summary: %s", task)
    else:
        logging.error("Unknown task status: %s", task)
