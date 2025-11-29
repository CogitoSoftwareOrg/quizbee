import logging
from meilisearch_python_sdk import AsyncClient
from meilisearch_python_sdk.models.search import Hybrid

from ....domain.models import MaterialChunk
from ....domain.out import SearchDto, Searcher

from ..indexers.meili_material_indexer import EMBEDDER_NAME, Doc


class MeiliMaterialVectorSearcher(Searcher):
    def __init__(self, meili: AsyncClient):
        self._meili = meili
        self._material_index = meili.index(EMBEDDER_NAME)

    async def search(self, dto: SearchDto) -> list[MaterialChunk]:
        if not dto.vectors or len(dto.vectors) == 0:
            logging.warning("No vectors provided for explainer search")
            return []

        vector = dto.vectors[0]

        filter_str = f"userId = {dto.user_id}"
        if dto.material_ids:
            filter_str += f" AND materialId IN [{','.join(dto.material_ids)}]"

        logging.info(f"Explainer search: filter={filter_str}, limit={dto.limit}")

        res = await self._material_index.search(
            query="",
            vector=vector,
            hybrid=Hybrid(semantic_ratio=1.0, embedder=EMBEDDER_NAME),
            filter=filter_str,
            limit=dto.limit,
            ranking_score_threshold=0,
            show_ranking_score=True,
        )

        chunks = [Doc.from_hit(hit).to_chunk() for hit in res.hits]
        logging.info(f"Explainer search found {len(chunks)} chunks")

        return chunks
