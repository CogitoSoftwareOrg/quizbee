import json
import logging
from meilisearch_python_sdk.models.search import Hybrid
from pocketbase import FileUpload
from pocketbase.models.dtos import Record

from apps.materials.utils import (
    load_file_text,
)

from lib.ai.models import DynamicConfig
from lib.clients import (
    HTTPAsyncClient,
    MeilisearchClient,
    AdminPB,
    ENCODERS,
)
from lib.config import LLMS

from .generate_patch import GenMode, generate_oneshot, generate_quiz_task


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
    estimated = tokens[:3000] + tokens[-3000:]
    texts = ENCODERS[LLMS.GPT_5_MINI].decode(truncated)

    estimated_summary = ENCODERS[LLMS.GPT_5_MINI].decode(estimated)

    q = f"Query: {quiz.get('query', '')}\n\nEstimated summary: {estimated_summary}"

    logging.info("Estimated summary: %s", len(estimated_summary))
    search_result = await summaries_index.search(
        query=q,
        hybrid=Hybrid(
            semantic_ratio=0.75,
            embedder="quizSummaries",
        ),
        ranking_score_threshold=0.4,
        filter=[f"userId = {user_id}"],
        limit=50,
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

    questions = questions[:500]
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
            "generation": 1,
        },
        options={
            "params": {"expand": "materials,quizItems_via_quiz"},
        },
    )

    await generate_quiz_task(
        admin_pb, http, user_id, attempt_id, quiz_id, limit, 1, GenMode.Continue, True
    )
    # await generate_oneshot(
    #     admin_pb, http, user_id, attempt_id, quiz, limit, GenMode.Continue
    # )
