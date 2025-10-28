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

from ...domain.models import Material, MaterialChunk, MaterialKind
from ...domain.constants import MAX_TEXT_INDEX_TOKENS
from ...domain.ports import Indexer
from ...domain.errors import TooManyTextTokensError

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
    def __init__(self, llm_tools: LLMToolsApp, meili: AsyncClient):
        self.llm_tools = llm_tools
        self.meili = meili
        self.material_index = meili.index(EMBEDDER_NAME)

    @classmethod
    async def ainit(cls, llm_tools: LLMToolsApp, meili: AsyncClient) -> "MeiliIndexer":
        instance = cls(llm_tools, meili)

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

        chunks = self.llm_tools.chunk(text)
        docs = []
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
            [asdict(doc) for doc in docs], primary_key="id"
        )

        logging.info(f"Created task for {len(docs)} documents")

        task = await self.meili.wait_for_task(
            task.task_uid,
            timeout_in_ms=int(120 * 1000),
            interval_in_ms=int(1 * 1000),
        )

        if task.status == "failed":
            logging.error(f"Failed to index material batch: {task}")
            # raise ValueError(f"Failed to index material batch: {task}")
        elif task.status == "succeeded":
            # All documents in this batch are indexed successfully
            for doc in docs:
                indexed = self._fill_template(doc)
                total_tokens += self.llm_tools.count_text(
                    indexed, LLMS.TEXT_EMBEDDING_3_SMALL
                )
                logging.info(f"Indexed chunk {doc.id}: (tokens: {total_tokens})")
        else:
            logging.error(f"Unknown task status: {task}")

        self._log_langfuse(material.user_id, material.id, total_tokens)

    async def search(
        self,
        user_id: str,
        query: str,
        material_ids: list[str] | None = None,
        limit: int = 100,
        ratio: float = 0.5,
        threshold: float = 0.4,
    ) -> list[MaterialChunk]:
        f = f"userId = {user_id}"
        if material_ids is not None:
            f += f" AND materialId IN [{','.join(material_ids)}]"

        logging.info(f"Meili Searching... {f}")

        if ratio == 0:
            res = await self.material_index.search(
                query=query,
                ranking_score_threshold=threshold,
                filter=f,
                limit=limit,
            )
        else:
            total_tokens = self.llm_tools.count_text(query, LLMS.TEXT_EMBEDDING_3_SMALL)

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

            self._log_langfuse(user_id, "", total_tokens)

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

    def _fill_template(self, doc: Doc):
        return EMBEDDER_TEMPLATE.replace("{{doc.title}}", doc.title).replace(
            "{{doc.content}}", doc.content
        )

    def _log_langfuse(self, user_id: str, session_id: str, total_tokens: int) -> None:
        with langfuse_client.start_as_current_span(name="material-indexing") as span:
            langfuse_client.update_current_generation(
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
