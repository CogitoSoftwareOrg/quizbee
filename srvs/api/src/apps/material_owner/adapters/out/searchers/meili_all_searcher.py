"""
MeiliMaterialQuerySearcher - поиск по запросу пользователя.

Использует гибридный поиск (semantic + keyword) с настраиваемым ratio.
"""

import logging
from langfuse import Langfuse
from meilisearch_python_sdk import AsyncClient
from meilisearch_python_sdk.models.search import Hybrid

from src.lib.config import LLMS

from ....domain.models import MaterialChunk
from ....domain.out import Searcher, LLMTools

from ..meili_material_indexer import EMBEDDER_NAME, Doc

logger = logging.getLogger(__name__)

ALL_CHUNKS_LIMIT = 100000


class MeiliMaterialAllSearcher(Searcher):
    def __init__(self, lf: Langfuse, llm_tools: LLMTools, meili: AsyncClient):
        self._lf = lf
        self._llm_tools = llm_tools
        self._meili = meili
        self._material_index = meili.index(EMBEDDER_NAME)

    async def search(
        self,
        user_id: str,
        material_ids: list[str],
        query: str = "*",
        limit: int = ALL_CHUNKS_LIMIT,
        ratio: float = 0.0,
    ) -> list[MaterialChunk]:
        f = f"userId = {user_id}"
        if material_ids:
            f += f" AND materialId IN [{','.join(material_ids)}]"

        logger.info(f"Meili All Search... {f}")

        res = await self._material_index.search(
            query=query,
            ranking_score_threshold=0,
            filter=f,
            limit=limit,
        )

        docs: list[Doc] = [Doc(**hit) for hit in res.hits]
        chunks = [self._doc_to_chunk(doc) for doc in docs]

        logging.info(f"Found {len(chunks)} chunks for query search")
        return chunks

    def _doc_to_chunk(self, doc: Doc) -> MaterialChunk:
        """Преобразует Doc в MaterialChunk."""
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
