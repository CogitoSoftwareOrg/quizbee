from dataclasses import dataclass
import logging
import asyncio
from voyageai.client_async import AsyncClient as VoyageAsyncClient
from langfuse import Langfuse
from meilisearch_python_sdk import AsyncClient
from meilisearch_python_sdk.models.search import Hybrid
from meilisearch_python_sdk.models.settings import Embedders, UserProvidedEmbedder

from src.lib.config import LLMS
from src.lib.settings import settings

from ....domain.models import Material, MaterialChunk, MaterialKind
from ....domain.constants import MAX_TEXT_INDEX_TOKENS
from ....domain.out import MaterialIndexer, LLMTools
from ....domain.errors import TooManyTextTokensError
from src.apps.llm_tools.domain.out import TextChunk

EMBEDDER_NAME = "materialChunk"  # здесь я поменял с materialChunks потому что иначе у меня требовало размерность прошлого эмбедера
EMBEDDER_TEMPLATE = "Chunk {{doc.title}}: {{doc.content}}"

meiliVoyageEmbeddings = {
    EMBEDDER_NAME: UserProvidedEmbedder(
        source="userProvided",
        dimensions=1024,
    ),
}


@dataclass
class Doc:
    id: str
    materialId: str
    userId: str
    title: str
    content: str
    idx: int = 0
    used: bool = False
    page: int | None = None
    _vectors: dict[str, dict[str, list[list[float]]]] | None = None

    @classmethod
    def from_hit(cls, hit: dict) -> "Doc":
        return cls(
            id=hit.get("id", ""),
            materialId=hit.get("materialId", ""),
            userId=hit.get("userId", ""),
            title=hit.get("title", ""),
            content=hit.get("content", ""),
            idx=hit.get("idx", 0),
            used=hit.get("used", False),
            page=hit.get("page"),
            _vectors=hit.get("_vectors", {}),
        )

    def to_chunk(self) -> MaterialChunk:
        vectors = (self._vectors or {}).get(EMBEDDER_NAME, {}).get("embeddings", [])
        vector = vectors[0] if len(vectors) > 0 else None

        return MaterialChunk(
            id=self.id,
            idx=self.idx,
            material_id=self.materialId,
            title=self.title,
            content=self.content,
            vector=vector,
            used=self.used,
        )

    def to_dict(self) -> dict:
        doc_dict = {
            "id": self.id,
            "materialId": self.materialId,
            "userId": self.userId,
            "title": self.title,
            "content": self.content,
            "idx": self.idx,
            "used": self.used,
        }
        if self.page is not None:
            doc_dict["page"] = self.page
        if self._vectors:
            doc_dict["_vectors"] = self._vectors
        return doc_dict


class MeiliMaterialIndexer(MaterialIndexer):
    def __init__(self, lf: Langfuse, llm_tools: LLMTools, meili: AsyncClient):
        self._lf = lf
        self.llm_tools = llm_tools
        self.meili = meili
        self.material_index = meili.index(EMBEDDER_NAME)
        self.voyage_client = VoyageAsyncClient(api_key=settings.voyageai_api_key)

    @classmethod
    async def ainit(
        cls, lf: Langfuse, llm_tools: LLMTools, meili: AsyncClient
    ) -> "MeiliMaterialIndexer":
        instance = cls(lf, llm_tools, meili)

        await instance.material_index.update_embedders(
            Embedders(
                embedders=meiliVoyageEmbeddings  # pyright: ignore[reportArgumentType]
            )
        )
        await instance.material_index.update_filterable_attributes(
            ["userId", "materialId", "idx", "used", "page"]
        )
        return instance

    async def index(self, material: Material) -> None:
        total_tokens = 0

        # Extract text from material
        if material.kind == MaterialKind.SIMPLE:
            text = material.file.file_bytes.decode("utf-8")
        elif material.text_file is not None:
            text = material.text_file.file_bytes.decode("utf-8")
        else:
            logging.warning(
                f"Material {material.id} is COMPLEX but has no text_file, trying to decode file as text"
            )
            raise ValueError("Material has no text content")

        if not text or not text.strip():
            raise ValueError("Material has no text content")

        # Check if text has page markers (O(n) worst case, but typically O(1) due to early match)
        has_page_markers = "{quizbee_page_number_" in text[:100_000]

        chunks_result = self.llm_tools.chunk(text, respect_pages=has_page_markers)
        docs: list[Doc] = []

        for i, chunk in enumerate(chunks_result):
            if isinstance(chunk, TextChunk):
                docs.append(
                    Doc(
                        id=f"{material.id}-{i}",
                        materialId=material.id,
                        userId=material.user_id,
                        title=material.title,
                        content=chunk.content,
                        idx=i,
                        used=False,
                        page=chunk.page,
                    )
                )
            else:
                docs.append(
                    Doc(
                        id=f"{material.id}-{i}",
                        materialId=material.id,
                        userId=material.user_id,
                        title=material.title,
                        content=str(chunk),
                        idx=i,
                        used=False,
                        page=None,
                    )
                )

        docs_tokens = sum(
            [
                self.llm_tools.count_text(
                    self._fill_template(doc), LLMS.VOYAGE_3_5_LITE
                )
                for doc in docs
            ]
        )
        if docs_tokens > MAX_TEXT_INDEX_TOKENS:
            raise TooManyTextTokensError(docs_tokens)

        # optimal batching
        batch_size = 1000

        embed_tasks = []
        for i in range(0, len(docs), batch_size):
            batch = docs[i : i + batch_size]
            batch_texts = [self._fill_template(doc) for doc in batch]
            embed_tasks.append(
                self.voyage_client.embed(
                    batch_texts,
                    model="voyage-3.5-lite",
                    input_type="document",
                    output_dimension=1024,
                )
            )

        logging.info(f"Sent {len(embed_tasks)} embedding requests to gather")
        results = await asyncio.gather(*embed_tasks)
        logging.info(f"Received all embedding results from gather")

        all_embeddings = []
        for result in results:
            all_embeddings.extend(result.embeddings)

        for doc, embedding in zip(docs, all_embeddings):
            doc._vectors = {EMBEDDER_NAME: embedding}

        task = await self.material_index.add_documents(
            [doc.to_dict() for doc in docs], primary_key="id"
        )

        logging.info(f"Created task for {len(docs)} documents")

        task = await self.meili.wait_for_task(
            task.task_uid,
            timeout_in_ms=int(120 * 1000),
            interval_in_ms=int(1 * 1000),
        )

        if task.status == "failed":
            logging.error(f"Failed to index material batch: {task}")
            raise ValueError(f"Failed to index material batch: {task}")
        elif task.status == "succeeded":
            for doc in docs:
                indexed = self._fill_template(doc)
                total_tokens += self.llm_tools.count_text(indexed, LLMS.VOYAGE_3_5_LITE)
                logging.info(f"Indexed chunk {doc.id}: (tokens: {total_tokens})")
        else:
            logging.error(f"Unknown task status: {task}")

        self._log_langfuse(
            material.user_id, material.id, total_tokens, "material-index-add"
        )

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

    async def mark_chunks_as_used(self, chunk_ids: list[str]) -> None:
        """
        Отмечает чанки как использованные.

        Args:
            chunk_ids: Список ID чанков для пометки
        """
        if len(chunk_ids) == 0:
            return

        # Обновляем документы, устанавливая used=True
        docs_to_update = [{"id": chunk_id, "used": True} for chunk_id in chunk_ids]

        task = await self.material_index.update_documents(
            docs_to_update, primary_key="id"
        )
        task = await self.meili.wait_for_task(
            task.task_uid,
            timeout_in_ms=int(30 * 1000),
            interval_in_ms=int(0.5 * 1000),
        )

        if task.status == "failed":
            logging.error(f"Failed to mark chunks as used: {task}")
        elif task.status == "succeeded":
            logging.info(f"Marked {len(chunk_ids)} chunks as used")
        else:
            logging.error(f"Unknown task status: {task}")

    async def get_chunks_info(self, chunk_ids: list[str]) -> list[tuple[str, int | None]]:
        """
        Получает информацию о чанках (название документа и страница).

        Args:
            chunk_ids: Список ID чанков

        Returns:
            Список кортежей (title, page) для каждого чанка
        """
        if len(chunk_ids) == 0:
            return []

        logging.info(f"Getting chunks info for {len(chunk_ids)} chunk IDs")
        chunks_info = []
        for chunk_id in chunk_ids:
            try:
                doc_dict = await self.material_index.get_document(chunk_id)
                doc = Doc.from_hit(doc_dict)
                chunks_info.append((doc.title, doc.page))
                logging.info(f"Chunk {chunk_id}: title='{doc.title}', page={doc.page}")
            except Exception as e:
                logging.warning(f"Failed to get chunk {chunk_id}: {e}")
                continue

        logging.info(f"Got info for {len(chunks_info)}/{len(chunk_ids)} chunks: {chunks_info}")
        return chunks_info

    def _fill_template(self, doc: Doc):
        return EMBEDDER_TEMPLATE.replace("{{doc.title}}", doc.title).replace(
            "{{doc.content}}", doc.content
        )

    def _log_langfuse(
        self, user_id: str, session_id: str, total_tokens: int, name: str
    ) -> None:
        with self._lf.start_as_current_span(name=name) as span:
            self._lf.update_current_generation(
                model=LLMS.VOYAGE_3_5_LITE,
                usage_details={
                    "total": total_tokens,
                },
            )
            span.update_trace(
                input=f"User: {user_id}, Session: {session_id}",
                output=f"Total tokens: {total_tokens}",
                user_id=user_id,
                session_id=session_id,
            )
