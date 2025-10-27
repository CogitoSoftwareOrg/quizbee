import json
import logging
import re
from meilisearch_python_sdk.models.search import Hybrid
from pocketbase import FileUpload
from pocketbase.models.dtos import Record
import tiktoken

from src.apps.materials.utils import (
    load_file_text,
)
from src.apps.materials.important_sentences import summarize_to_fixed_tokens
from src.apps.quizes.ai.trimmer import trim_content, Trimmer

from src.lib.ai.models import DynamicConfig
from src.lib.clients import (
    HTTPAsyncClient,
    MeiliDeps as MeilisearchClient,
    AdminPBDeps as AdminPB,
    langfuse_client,
)
from src.lib.config import LLMS

from .generate_patch import GenMode, generate_oneshot, generate_quiz_task
from .agent import Quizer

ENCODER = tiktoken.encoding_for_model(LLMS.GPT_5_MINI)


def filter_content_by_page_ranges(content: str, page_ranges: list) -> str:
    """
    Фильтрует контент, оставляя только страницы из указанных диапазонов.

    Args:
        content: Текст с маркерами страниц вида {quizbee_page_number_N}
        page_ranges: Список диапазонов страниц [{"start": 10, "end": 20}, ...]

    Returns:
        Отфильтрованный текст, содержащий только указанные страницы
    """
    if not page_ranges:
        return content

    # Разбиваем контент на страницы по маркерам
    # Паттерн для поиска маркеров страниц
    page_pattern = r"\{quizbee_page_number_(\d+)\}"

    # Находим все позиции маркеров страниц
    page_markers = []
    for match in re.finditer(page_pattern, content):
        page_num = int(match.group(1))
        start_pos = match.start()
        page_markers.append((page_num, start_pos))

    if not page_markers:
        logging.warning("No page markers found in content, returning full content")
        return content

    # Сортируем по номеру страницы
    page_markers.sort(key=lambda x: x[0])

    # Создаем набор страниц, которые нужно включить
    pages_to_include = set()
    for pr in page_ranges:
        start = pr.get("start", pr.get("Start", 0))
        end = pr.get("end", pr.get("End", 0))
        for page in range(start, end + 1):
            pages_to_include.add(page)

    logging.info(f"Including pages: {sorted(pages_to_include)}")

    # Собираем фрагменты контента для нужных страниц
    filtered_parts = []

    for i, (page_num, start_pos) in enumerate(page_markers):
        if page_num not in pages_to_include:
            continue

        # Определяем конец текущей страницы (начало следующей или конец документа)
        if i + 1 < len(page_markers):
            end_pos = page_markers[i + 1][1]
        else:
            end_pos = len(content)

        # Извлекаем текст страницы
        page_content = content[start_pos:end_pos]
        filtered_parts.append(page_content)

    filtered_content = "".join(filtered_parts)

    logging.info(
        f"Filtered content: {len(content)} -> {len(filtered_content)} chars "
        f"({len(filtered_content) / len(content) * 100:.1f}% retained)"
    )

    return filtered_content


async def start_generating_quiz_task(
    admin_pb: AdminPB,
    http: HTTPAsyncClient,
    trimmer: Trimmer,
    quizer: Quizer,
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
    has_book = any(m.get("isBook", False) for m in materials)

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
    tokens = ENCODER.encode(concatenated_texts)
    total_tokens = len(tokens)

    logging.info(f"Total tokens from all materials: {total_tokens}")

    # If exceeds 70k tokens and has books, use trimming
    material_page_ranges = (
        {}
    )  # Dictionary to store page ranges: {material_id: page_ranges}

    if total_tokens > 70_000 and has_book:
        logging.info(
            f"Token count ({total_tokens}) exceeds 70k and books detected, applying trim_content..."
        )

        # Get table of contents for book materials
        book_materials = [m for m in materials if m.get("isBook", True)]

        for m in book_materials:
            mid = m.get("id", "")
            toc = m.get("contents", "")

            if toc:
                try:
                    with langfuse_client.start_as_current_span(
                        name=f"trim-material-{mid}"
                    ) as span:
                        page_ranges = await trim_content(
                            trimmer,
                            contents=toc,
                            query=quiz.get("query", ""),
                            user_id=user_id,
                            session_id=attempt_id,
                        )

                        # Store page ranges in memory
                        material_page_ranges[mid] = page_ranges

                        logging.info(
                            f"Material {mid} trimmed to page ranges: {page_ranges}"
                        )

                        if span:
                            span.update_trace(
                                input=f"Material: {mid}, TOC length: {len(toc)}",
                                output=f"Page ranges: {page_ranges}",
                                user_id=user_id,
                                session_id=attempt_id,
                                metadata={
                                    "material_id": mid,
                                    "page_ranges_count": len(page_ranges),
                                    "page_ranges": page_ranges,
                                },
                            )

                except Exception as e:
                    logging.exception(f"Failed to trim material {mid}: {e}")

        # Reload materials context with trimmed ranges
        texts = []
        for m in materials:
            mid = m.get("id", "")

            if m.get("kind") == "simple":
                f = m.get("file", "")
                content = await load_file_text(http, "materials", mid, f)
                if f.endswith((".md", ".txt", ".csv", ".json")):
                    texts.append((f, content))

            elif m.get("kind") == "complex":
                txt = m.get("textFile", "")
                if txt:
                    content = await load_file_text(http, "materials", mid, txt)

                    # Apply page range filtering if available and material is a book
                    page_ranges = material_page_ranges.get(mid)
                    is_book_material = m.get("isBook", False)

                    if page_ranges and is_book_material:
                        try:
                            logging.info(
                                f"Filtering material {mid} ({txt}) to page ranges: {page_ranges}"
                            )

                            # Filter content based on page ranges
                            original_length = len(content)
                            content = filter_content_by_page_ranges(
                                content, page_ranges
                            )

                            logging.info(
                                f"Material {mid} filtered: {original_length} -> {len(content)} chars "
                                f"({len(content) / original_length * 100:.1f}% retained)"
                            )

                        except Exception as e:
                            logging.exception(
                                f"Failed to filter content for material {mid}: {e}"
                            )
                            # If filtering fails, keep original content

                    texts.append((txt, content))

        # Recalculate concatenated texts
        formatted_texts = []
        for filename, content in texts:
            formatted_texts.append(
                f"-------NEW FILE {filename}-------------\n{content}"
            )
        concatenated_texts = "\n\n".join(formatted_texts)

        tokens = ENCODER.encode(concatenated_texts)
        total_tokens = len(tokens)
        logging.info(f"After trimming: {total_tokens} tokens")

    if total_tokens > 70_000:
        logging.info(
            f"Token count ({total_tokens}) exceeds 70k, applying summarization to 52k tokens..."
        )
        concatenated_texts = summarize_to_fixed_tokens(
            concatenated_texts,
            target_token_count=70000,
            summary_token_count=6000,
        )
        # Recalculate tokens after summarization
        tokens = ENCODER.encode(concatenated_texts[0])
        logging.info(f"After summarization: {len(tokens)} tokens")
    elif total_tokens > 6000:
        concatenated_texts = summarize_to_fixed_tokens(
            concatenated_texts,
            target_token_count=int(total_tokens / 1.15),
            summary_token_count=6000,
        )
    elif total_tokens > 0:
        concatenated_texts = (concatenated_texts, concatenated_texts)
    else:
        concatenated_texts = ("User provided no additional material.", "")

    # Use the processed text (full summary with context)
    texts = concatenated_texts[0]

    # Create estimated summary from brief summary (without context)
    estimated_summary = concatenated_texts[1]
    estimated_summary_tokens = ENCODER.encode(estimated_summary)
    logging.info(
        f"Estimated summary: {len(estimated_summary)} chars, {len(estimated_summary_tokens)} tokens"
    )

    q = f"Query: {quiz.get('query', '')}\n\nEstimated summary: {estimated_summary}"
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

    # Avoid repeating questions from similar quizzes
    if quiz.get("avoidRepeat"):
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
        admin_pb,
        http,
        quizer,
        user_id,
        attempt_id,
        quiz_id,
        limit,
        1,
        GenMode.Continue,
    )
    # await generate_oneshot(
    #     admin_pb, http, user_id, attempt_id, quiz, limit, GenMode.Continue
    # )
