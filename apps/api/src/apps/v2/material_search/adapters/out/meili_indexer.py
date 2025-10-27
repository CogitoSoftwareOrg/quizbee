import logging
from statistics import mode
from meilisearch_python_sdk import AsyncClient
from meilisearch_python_sdk.models.settings import Embedders, OpenAiEmbedder

from src.lib.clients import langfuse_client
from src.lib.config import LLMS
from src.lib.settings import settings

from ...domain.models import Material, MaterialKind
from ...domain.ports import Indexer, Chunker, Tokenizer

EMBEDDER_TEMPLATE = "Chunk {{doc.title}}: {{doc.content}}"

meiliEmbeddings = {
    "materialChunks": OpenAiEmbedder(
        source="openAi",
        model=LLMS.TEXT_EMBEDDING_3_SMALL,
        api_key=settings.openai_api_key,
        document_template=EMBEDDER_TEMPLATE,
    ),
}


class MeiliIndexer(Indexer):
    def __init__(self, tokenizer: Tokenizer, chunker: Chunker, meili: AsyncClient):
        self.tokenizer = tokenizer
        self.chunker = chunker
        self.meili = meili
        self.material_index = meili.index("materialChunks")

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
                    total_tokens += self.tokenizer.count_text(indexed)
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
