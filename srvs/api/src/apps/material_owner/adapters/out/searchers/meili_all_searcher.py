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
from ....domain.out import Searcher, LLMTools, SearchDto

from ..indexers.meili_material_indexer import EMBEDDER_NAME, Doc

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
        dto: SearchDto,
    ) -> list[MaterialChunk]:
        f = f"userId = {dto.user_id}"
        if dto.material_ids:
            f += f" AND materialId IN [{','.join(dto.material_ids)}]"

        logger.info(f"Meili All Search... {f}")

        res = await self._material_index.search(
            query="*",
            ranking_score_threshold=0,
            filter=f,
            limit=ALL_CHUNKS_LIMIT,
            retrieve_vectors=True,
            attributes_to_retrieve=["id", "_vectors"],
        )

        docs: list[Doc] = [Doc.from_hit(hit) for hit in res.hits]
        chunks = [doc.to_chunk() for doc in docs]

        logging.info(f"Found {len(chunks)} chunks for query search")
        return chunks
