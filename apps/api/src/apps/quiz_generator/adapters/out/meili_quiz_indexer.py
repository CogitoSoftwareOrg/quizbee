import asyncio
from dataclasses import asdict, dataclass
import logging
from typing import TypedDict
from meilisearch_python_sdk import AsyncClient
from meilisearch_python_sdk.models.search import Hybrid
from meilisearch_python_sdk.models.settings import Embedders, OpenAiEmbedder

from src.lib.clients import langfuse_client
from src.lib.config import LLMS
from src.lib.settings import settings

from src.apps..llm_tools.app.contracts import LLMToolsApp

from ...domain.errors import InvalidQuiz
from ...domain.models import Quiz, QuizCategory, QuizDifficulty, QuizVisibility
from ...domain.ports import QuizIndexer, QuizRepository

FILTERABLE_ATTRIBUTES = [
    "userId",
    "quizId",
    "visibility",
    "tags",
    "category",
    "difficulty",
]

EMBEDDER_NAME = "quizSummaries"
EMBEDDER_TEMPLATE = """
Quiz {{doc.title}}
Query: {{doc.query}}
Summary: {{doc.summary}}
Difficulty: {{doc.difficulty}}
Tags: {{doc.tags}}
Category: {{doc.category}}
"""

meiliEmbeddings = {
    EMBEDDER_NAME: OpenAiEmbedder(
        source="openAi",
        model=LLMS.TEXT_EMBEDDING_3_SMALL,
        api_key=settings.openai_api_key,
        document_template=EMBEDDER_TEMPLATE,
    ),
}


@dataclass
class Doc:
    id: str
    quiz_id: str
    user_id: str
    visibility: QuizVisibility
    title: str
    query: str
    summary: str
    tags: list[str]
    category: QuizCategory
    difficulty: QuizDifficulty

    @classmethod
    def from_quiz(cls, quiz: Quiz) -> "Doc":
        return cls(
            id=quiz.id,
            quiz_id=quiz.id,
            user_id=quiz.author_id,
            visibility=quiz.visibility,
            title=quiz.title,
            query=quiz.query,
            summary=quiz.summary,  # pyright: ignore[reportArgumentType]
            tags=quiz.tags,  # pyright: ignore[reportArgumentType]
            category=quiz.category,  # pyright: ignore[reportArgumentType]
            difficulty=quiz.difficulty,
        )

    @classmethod
    def from_hit(cls, hit: dict) -> "Doc":
        return cls(
            id=hit.get("id", ""),
            quiz_id=hit.get("quizId", ""),
            user_id=hit.get("userId", ""),
            visibility=hit.get("visibility", ""),
            title=hit.get("title", ""),
            query=hit.get("query", ""),
            summary=hit.get("summary", ""),
            tags=hit.get("tags", []),
            category=hit.get("category", ""),
            difficulty=hit.get("difficulty", ""),
        )


class MeiliQuizIndexer(QuizIndexer):
    def __init__(
        self,
        llm_tools: LLMToolsApp,
        meili: AsyncClient,
        quiz_repository: QuizRepository,
    ):
        self.llm_tools = llm_tools
        self.meili = meili
        self.quiz_index = meili.index(EMBEDDER_NAME)
        self.quiz_repository = quiz_repository

    @classmethod
    async def ainit(
        cls, llm_tools: LLMToolsApp, meili: AsyncClient, quiz_repository: QuizRepository
    ) -> "MeiliQuizIndexer":
        instance = cls(llm_tools, meili, quiz_repository)

        await instance.quiz_index.update_embedders(
            Embedders(embedders=meiliEmbeddings)  # pyright: ignore[reportArgumentType]
        )
        await instance.quiz_index.update_filterable_attributes(
            FILTERABLE_ATTRIBUTES  # pyright: ignore[reportArgumentType]
        )

        return instance

    async def index(self, quiz: Quiz) -> None:
        total_tokens = 0

        if quiz.summary is None or quiz.tags is None or quiz.category is None:
            raise InvalidQuiz("Quiz summary, tags, and category are required")

        doc = Doc.from_quiz(quiz)

        task = await self.quiz_index.add_documents([asdict(doc)], primary_key="id")

        logging.info(f"Created task for document")

        # First: Wait for all tasks to complete and get updated task objects
        task = await self.meili.wait_for_task(
            task.task_uid,
            timeout_in_ms=int(60 * 1000),  # 30 seconds
            interval_in_ms=int(0.5 * 1000),  # 0.5 seconds
        )

        logging.info(f"Processing task")

        # Second: Process results and count tokens
        # Each task represents a batch of documents, so all docs are processed by all tasks
        if task.status == "failed":
            logging.error(f"Failed to index material batch: {task}")
            # raise ValueError(f"Failed to index material batch: {task}")
        elif task.status == "succeeded":
            logging.info(f"Indexed document")
        else:
            logging.error(f"Unknown task status: {task}")

        # Third: Log to langfuse after all tasks are complete and tokens are counted
        with langfuse_client.start_as_current_span(name="material-indexing") as span:
            langfuse_client.update_current_generation(
                model=LLMS.TEXT_EMBEDDING_3_SMALL,
                usage_details={
                    "total": total_tokens,
                },
            )
            span.update_trace(
                input=f"Quiz: {quiz.id}",
                output=f"Total tokens: {total_tokens}",
                metadata={
                    "quiz_id": quiz.id,
                    "total_tokens": total_tokens,
                },
                user_id=quiz.author_id,
                session_id=quiz.id,
            )

    async def search(
        self,
        user_id: str,
        query: str,
        limit: int = 100,
        ratio=0.5,
        threshold=0.4,
    ) -> list[Quiz]:
        f = f"userId = {user_id}"
        hybrid = (
            Hybrid(
                semantic_ratio=ratio,
                embedder=EMBEDDER_NAME,
            )
            if ratio > 0
            else None
        )

        res = await self.quiz_index.search(
            query=query,
            hybrid=hybrid,
            ranking_score_threshold=threshold,
            filter=f,
            limit=limit,
        )

        logging.info(f"Meili Searching... {f} (hits: {len(res.hits)})")

        docs: list[Doc] = [Doc.from_hit(hit) for hit in res.hits]
        logging.info(f"Docs: {docs}")
        quizes = await asyncio.gather(
            *[self.quiz_repository.get(doc.quiz_id) for doc in docs]
        )

        return quizes

    async def delete(self, material_ids: list[str]) -> None:
        if len(material_ids) == 0:
            return

        task = await self.quiz_index.delete_documents_by_filter(
            f"materialId IN [{','.join(material_ids)}]"
        )
        task = await self.meili.wait_for_task(
            task.task_uid,
            timeout_in_ms=int(30 * 1000),
            interval_in_ms=int(0.5 * 1000),
        )
        if task.status == "failed":
            logging.error(f"Failed to delete material: {task}")
            # raise ValueError(f"Failed to delete material: {task}")
        elif task.status == "succeeded":
            logging.info(f"Deleted materials: {material_ids}")
        else:
            logging.error(f"Unknown task status: {task}")
