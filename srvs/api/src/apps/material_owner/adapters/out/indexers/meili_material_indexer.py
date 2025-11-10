from dataclasses import asdict, dataclass
import logging
from typing import Any, TypedDict
from langfuse import Langfuse
from meilisearch_python_sdk import AsyncClient
from meilisearch_python_sdk.models.search import Hybrid
from meilisearch_python_sdk.models.settings import Embedders, OpenAiEmbedder

from src.lib.config import LLMS
from src.lib.settings import settings

from ....domain.models import Material, MaterialChunk, MaterialKind
from ....domain.constants import MAX_TEXT_INDEX_TOKENS
from ....domain.out import MaterialIndexer, LLMTools
from ....domain.errors import TooManyTextTokensError

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
    _vectors: dict[str, dict[str, list[list[float]]]] | None = None

    @classmethod
    def from_hit(cls, hit: dict) -> "Doc":
        return cls(
            id=hit.get("id", ""),
            materialId=hit.get("materialId", ""),
            userId=hit.get("userId", ""),
            title=hit.get("title", ""),
            content=hit.get("content", ""),
            _vectors=hit.get("_vectors", {}),
        )

    def to_chunk(self) -> MaterialChunk:
        vectors = (self._vectors or {}).get(EMBEDDER_NAME, {}).get("embeddings", [])
        vector = vectors[0] if len(vectors) > 0 else None

        return MaterialChunk(
            id=self.id,
            idx=int(self.id.split("-")[-1]),
            material_id=self.materialId,
            title=self.title,
            content=self.content,
            vector=vector,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "materialId": self.materialId,
            "userId": self.userId,
            "title": self.title,
            "content": self.content,
        }


class MeiliMaterialIndexer(MaterialIndexer):
    def __init__(self, lf: Langfuse, llm_tools: LLMTools, meili: AsyncClient):
        self._lf = lf
        self.llm_tools = llm_tools
        self.meili = meili
        self.material_index = meili.index(EMBEDDER_NAME)

    @classmethod
    async def ainit(
        cls, lf: Langfuse, llm_tools: LLMTools, meili: AsyncClient
    ) -> "MeiliMaterialIndexer":
        instance = cls(lf, llm_tools, meili)

        await instance.material_index.update_embedders(
            Embedders(embedders=meiliEmbeddings)  # pyright: ignore[reportArgumentType]
        )
        await instance.material_index.update_filterable_attributes(
            ["userId", "materialId"]
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

        chunks = self.llm_tools.chunk(text)
        docs: list[Doc] = []
        for i, chunk in enumerate(chunks):
            docs.append(
                Doc(
                    id=f"{material.id}-{i}",
                    materialId=material.id,
                    userId=material.user_id,
                    title=material.title,
                    content=chunk,
                )
            )

        docs_tokens = sum(
            [
                self.llm_tools.count_text(
                    self._fill_template(doc), LLMS.TEXT_EMBEDDING_3_SMALL
                )
                for doc in docs
            ]
        )
        if docs_tokens > MAX_TEXT_INDEX_TOKENS:
            raise TooManyTextTokensError(docs_tokens)

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
                total_tokens += self.llm_tools.count_text(
                    indexed, LLMS.TEXT_EMBEDDING_3_SMALL
                )
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

    def _fill_template(self, doc: Doc):
        return EMBEDDER_TEMPLATE.replace("{{doc.title}}", doc.title).replace(
            "{{doc.content}}", doc.content
        )

    def _log_langfuse(
        self, user_id: str, session_id: str, total_tokens: int, name: str
    ) -> None:
        with self._lf.start_as_current_span(name=name) as span:
            self._lf.update_current_generation(
                model=LLMS.TEXT_EMBEDDING_3_SMALL,
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
