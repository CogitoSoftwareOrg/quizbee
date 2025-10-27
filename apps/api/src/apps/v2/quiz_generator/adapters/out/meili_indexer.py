from dataclasses import dataclass
import logging
from typing import TypedDict
from meilisearch_python_sdk import AsyncClient
from meilisearch_python_sdk.models.search import Hybrid
from meilisearch_python_sdk.models.settings import Embedders, OpenAiEmbedder

from src.lib.clients import langfuse_client
from src.lib.config import LLMS
from src.lib.settings import settings

from ...domain.models import Quiz, QuizItem
from ...domain.ports import Indexer, Chunker, Tokenizer

EMBEDDER_NAME = "materialChunks"
EMBEDDER_TEMPLATE = "Chunk {{doc.title}}: {{doc.content}}"

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
    materialId: str
    userId: str
    title: str
    content: str


class MeiliIndexer(Indexer):
    def __init__(self, tokenizer: Tokenizer, chunker: Chunker, meili: AsyncClient):
        self.tokenizer = tokenizer
        self.chunker = chunker
        self.meili = meili
        self.material_index = meili.index(EMBEDDER_NAME)

    @classmethod
    async def ainit(
        cls, tokenizer: Tokenizer, chunker: Chunker, meili: AsyncClient
    ) -> "MeiliIndexer":
        instance = cls(tokenizer, chunker, meili)

        await instance.material_index.update_embedders(
            Embedders(embedders=meiliEmbeddings)  # pyright: ignore[reportArgumentType]
        )
        await instance.material_index.update_filterable_attributes(
            ["userId", "materialId"]
        )

        return instance

    async def index(self, material: Material) -> None:
        total_tokens = 0

        if material.kind == MaterialKind.SIMPLE:
            text = material.file.file_bytes.decode("utf-8")
        elif material.text_file is not None:
            text = material.text_file.file_bytes.decode("utf-8")
        else:
            raise ValueError("Material has no text")

        chunks = self.chunker.chunk(text)
        docs = []
        for i, chunk in enumerate(chunks):
            docs.append(
                {
                    "id": f"{material.id}-{i}",
                    "materialId": material.id,
                    "userId": material.user_id,
                    "title": material.title,
                    "content": chunk,
                }
            )

        tasks = await self.material_index.add_documents_in_batches(
            docs, primary_key="id"
        )

        logging.info(f"Created {len(tasks)} tasks for {len(docs)} documents")

        # First: Wait for all tasks to complete and get updated task objects
        updated_tasks = []
        for task in tasks:
            updated_task = await self.meili.wait_for_task(
                task.task_uid,
                timeout_in_ms=int(30 * 1000),  # 30 seconds
                interval_in_ms=int(0.5 * 1000),  # 0.5 seconds
            )
            updated_tasks.append(updated_task)

        logging.info(f"Processing {len(updated_tasks)} tasks with {len(docs)} docs")

        # Second: Process results and count tokens
        # Each task represents a batch of documents, so all docs are processed by all tasks
        for task in updated_tasks:
            if task.status == "failed":
                logging.error(f"Failed to index material batch: {task}")
                # raise ValueError(f"Failed to index material batch: {task}")
            elif task.status == "succeeded":
                # All documents in this batch are indexed successfully
                for doc in docs:
                    indexed = EMBEDDER_TEMPLATE.replace(
                        "{{doc.title}}", doc["title"]
                    ).replace("{{doc.content}}", doc["content"])
                    total_tokens += self.tokenizer.count_text(
                        indexed, LLMS.TEXT_EMBEDDING_3_SMALL
                    )
                    logging.info(f"Indexed chunk {doc['id']}: (tokens: {total_tokens})")
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
                input=f"Material: {material.id}",
                output=f"Total tokens: {total_tokens}",
                metadata={
                    "material_id": material.id,
                    "total_tokens": total_tokens,
                },
                user_id=material.user_id,
                session_id=material.id,
            )

    async def search(
        self,
        user_id: str,
        query: str,
        material_ids: list[str],
        limit: int = 100,
        ratio=0.5,
        threshold=0.4,
    ) -> list[MaterialChunk]:
        f = f"userId = {user_id}"
        if material_ids:
            f += f" AND materialId IN [{','.join(material_ids)}]"

        if ratio == 0:
            res = await self.material_index.search(
                query=query,
                ranking_score_threshold=threshold,
                filter=f,
                limit=limit,
            )
        else:
            res = await self.material_index.search(
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
        chunks = [self._doc_to_chunk(doc) for doc in docs]

        return chunks

    async def delete(self, material_ids: list[str]) -> None:
        if len(material_ids) == 0:
            return

        task = await self.material_index.delete_documents_by_filter(
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

    def _doc_to_chunk(self, doc: Doc) -> MaterialChunk:
        idx = doc.id.split("-")[-1]

        if not idx.isdigit():
            raise ValueError(f"Invalid chunk id: {doc.id}")
        idx = int(idx)

        return MaterialChunk(
            id=doc.id,
            idx=int(idx),
            material_id=doc.materialId,
            title=doc.title,
            content=doc.content,
        )
