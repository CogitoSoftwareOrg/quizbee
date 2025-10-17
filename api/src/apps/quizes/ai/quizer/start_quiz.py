import json
import logging
from meilisearch_python_sdk.models.search import Hybrid
from pocketbase import FileUpload
from pocketbase.models.dtos import Record

from apps.materials.utils import (
    load_file_text,
)
from apps.materials.important_sentences import summarize_to_fixed_tokens

from lib.ai.models import DynamicConfig
from lib.clients import (
    HTTPAsyncClient,
    MeilisearchClient,
    AdminPB,
    ENCODERS,
)
from lib.config import LLMS

from .generate_patch import generate_quiz_task


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
                texts.append((f, content))

        elif m.get("kind") == "complex":
            images = m.get("images", [])
            txt = m.get("textFile", "")
            if txt:
                content = await load_file_text(http, "materials", mid, txt)
                texts.append((txt, content))
    
    # Concatenate all texts with file separators
    formatted_texts = []
    for filename, content in texts:
        formatted_texts.append(f"-------NEW FILE {filename}-------------\n{content}")
    concatenated_texts = "\n\n".join(formatted_texts)
    
    # Check total token count
    tokens = ENCODERS[LLMS.GPT_5_MINI].encode(concatenated_texts)
    total_tokens = len(tokens)
    
    logging.info(f"Total tokens from all materials: {total_tokens}")
    
    # If exceeds 100k tokens, use important_sentences to reduce to 50k
    if total_tokens > 80_000:
        logging.info(f"Token count ({total_tokens}) exceeds 100k, applying summarization to 50k tokens...")
        concatenated_texts = summarize_to_fixed_tokens(
            concatenated_texts, 
            target_token_count=52000, 
        )
        # Recalculate tokens after summarization
        tokens = ENCODERS[LLMS.GPT_5_MINI].encode(concatenated_texts)
        logging.info(f"After summarization: {len(tokens)} tokens")
    
    # Use the processed text
    texts = concatenated_texts

    # Create estimated summary from beginning and end
    estimated = tokens[:4000] + tokens[-4000:]
    estimated_summary = ENCODERS[LLMS.GPT_5_MINI].decode(estimated)

    q = f"Query: {quiz.get('query', '')}\n\nEstimated summary: {estimated_summary}"

    logging.info("Estimated summary: %s", len(estimated_summary))
    search_result = await summaries_index.search(
        query=q,
        hybrid=Hybrid(
            semantic_ratio=0.75,
            embedder="quizSummaries",
        ),
        ranking_score_threshold=0.3,
        filter=[f"userId = {user_id}"],
        limit=10,
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
            "generation": 1,
        },
    )

    await generate_quiz_task(
        admin_pb, http, user_id, attempt_id, quiz_id, limit, 1, "continue"
    )
