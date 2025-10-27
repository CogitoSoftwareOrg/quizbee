import logging
from meilisearch_python_sdk import AsyncClient
from meilisearch_python_sdk.models.settings import Embedders, OpenAiEmbedder

from src.lib.config import LLMS
from src.lib.settings import settings

from ...domain.models import Material, MaterialKind
from ...domain.ports import Indexer, Chunker

meiliEmbeddings = {
    "materialChunks": OpenAiEmbedder(
        source="openAi",
        model=LLMS.TEXT_EMBEDDING_3_SMALL,
        api_key=settings.openai_api_key,
        document_template="Chunk {{doc.title}}: {{doc.content}}",
    ),
}


class MeiliIndexer(Indexer):
    def __init__(self, chunker: Chunker, meili: AsyncClient):
        self.chunker = chunker
        self.meili = meili
        self.material_index = meili.index("materialChunks")

    @classmethod
    async def ainit(cls, chunker: Chunker, meili: AsyncClient) -> "MeiliIndexer":
        instance = cls(chunker, meili)

        await instance.material_index.update_embedders(
            Embedders(embedders=meiliEmbeddings)  # pyright: ignore[reportArgumentType]
        )
        await instance.material_index.update_filterable_attributes(
            ["userId", "materialId"]
        )

        return instance

    async def index(self, material: Material) -> None:
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
        for task in tasks:
            await self.meili.wait_for_task(
                task.task_uid,
                timeout_in_ms=int(30 * 1000),  # 30 seconds
                interval_in_ms=int(0.5 * 1000),  # 0.5 seconds
            )
            if task.status == "failed":
                logging.error(f"Failed to index material chunks: {task}")
                # raise ValueError(f"Failed to index material chunks: {task}")
            elif task.status == "succeeded":
                logging.info(f"Indexed material chunks: {task}")
            else:
                logging.error(f"Unknown task status: {task}")
