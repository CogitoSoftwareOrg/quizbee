from dataclasses import asdict, dataclass
import logging
from typing import TypedDict
from meilisearch_python_sdk import AsyncClient
from meilisearch_python_sdk.models.search import Hybrid
from meilisearch_python_sdk.models.settings import Embedders, OpenAiEmbedder

from src.lib.clients import langfuse_client
from src.lib.config import LLMS
from src.lib.settings import settings

from src.apps.v2.llm_tools.app.contracts import LLMToolsApp

from ...domain.models import Quiz, QuizItem
from ...domain.ports import QuizIndexer

EMBEDDER_NAME = "quizSummaries"
EMBEDDER_TEMPLATE = """
Quiz {{doc.title}}
Query: {{doc.query}}
Summary: {{doc.summary}}
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
    quizId: str
    authorId: str
    title: str
    query: str
    summary: str
    tags: list[str]
    category: str


class MeiliIndexer(QuizIndexer):
    def __init__(self, llm_tools: LLMToolsApp, meili: AsyncClient):
        self.llm_tools = llm_tools
        self.meili = meili
        self.quiz_index = meili.index(EMBEDDER_NAME)

    @classmethod
    async def ainit(cls, llm_tools: LLMToolsApp, meili: AsyncClient) -> "MeiliIndexer":
        instance = cls(llm_tools, meili)

        await instance.quiz_index.update_embedders(
            Embedders(embedders=meiliEmbeddings)  # pyright: ignore[reportArgumentType]
        )
        await instance.quiz_index.update_filterable_attributes(["userId", "quizId"])

        return instance

    async def index(self, quiz: Quiz) -> None:
        total_tokens = 0

        if quiz.summary is None or quiz.tags is None or quiz.category is None:
            raise ValueError("Quiz summary, tags, and category are required")

        doc = Doc(
            id=f"{quiz.id}",
            quizId=quiz.id,
            authorId=quiz.author_id,
            title=quiz.title,
            query=quiz.query,
            summary=quiz.summary,
            tags=quiz.tags,
            category=quiz.category,
        )

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
        quiz_ids: list[str],
        limit: int = 100,
        ratio=0.5,
        threshold=0.4,
    ) -> list[Quiz]:
        f = f"authorId = {user_id}"
        if quiz_ids:
            f += f" AND quizId IN [{','.join(quiz_ids)}]"

        if ratio == 0:
            res = await self.quiz_index.search(
                query=query,
                ranking_score_threshold=threshold,
                filter=f,
                limit=limit,
            )
        else:
            res = await self.quiz_index.search(
                query=query,
                hybrid=Hybrid(
                    semantic_ratio=ratio,
                    embedder=EMBEDDER_NAME,
                ),
                ranking_score_threshold=threshold,
                filter=f,
                limit=limit,
            )

        docs: list[Doc] = [Doc(**hit) for hit in res.hits]
        quizes = [self._doc_to_quiz(doc) for doc in docs]

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

    # def _doc_to_quiz(self, doc: Doc) -> Quiz:
    #     return Quiz(
    #         id=doc.id,
    #         author_id=doc.authorId,
    #         materials=[],
    #         length=0,
    #         title=doc.title,
    #         query=doc.query,
    #         summary=doc.summary,
    #         tags=doc.tags,
    #         category=QuizCategory(doc.category),
    #     )
