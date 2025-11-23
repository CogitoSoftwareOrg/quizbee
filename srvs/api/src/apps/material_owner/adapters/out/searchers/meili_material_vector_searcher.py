"""
MeiliMaterialVectorSearcher - поиск по векторам.

Находит наиболее похожие чанки для каждого вектора из списка central_vectors.
Используется для генерации квизов на основе кластеризации.
"""

import logging
from langfuse import Langfuse
from meilisearch_python_sdk import AsyncClient
from meilisearch_python_sdk.models.search import Hybrid

from ....domain.models import MaterialChunk
from ....domain.out import SearchDto, Searcher, LLMTools
from .....quiz_owner.domain.constants import PATCH_CHUNK_TOKEN_LIMIT

from ..indexers.meili_material_indexer import EMBEDDER_NAME, Doc


class MeiliMaterialVectorSearcher(Searcher):
    """
    Searcher для поиска материалов по векторам.

    Для каждого вектора из списка находит наиболее похожие чанки
    используя косинусное сходство. Используется для генерации
    квизов на основе кластеризации материалов.
    """

    def __init__(self, lf: Langfuse, llm_tools: LLMTools, meili: AsyncClient):
        self._lf = lf
        self._llm_tools = llm_tools
        self._meili = meili
        self._material_index = meili.index(EMBEDDER_NAME)

    async def search(
        self,
        dto: SearchDto,
    ) -> list[MaterialChunk]:
        """
        Ищет наиболее похожие чанки для векторов с использованием реранкинга.

        Args:
            dto: SearchDto с параметрами поиска
                - user_id: ID пользователя
                - material_ids: Список ID материалов для поиска
                - limit: Максимальное количество чанков (обычно 4)
                - vectors: Список векторов для поиска

        Returns:
            Список найденных чанков после реранкинга
        """
        if not dto.vectors or len(dto.vectors) == 0:
            logging.warning("No vectors provided for vector search")
            return []

        all_chunks: list[MaterialChunk] = []
        seen_chunk_ids = set()

        for idx, vector in enumerate(dto.vectors):
            f_unused = f"userId = {dto.user_id} AND used = false"
            if dto.material_ids:
                f_unused += f" AND materialId IN [{','.join(dto.material_ids)}]"

            logging.info(f"Meili Vector Search {idx + 1}/{len(dto.vectors)} (unused): {f_unused}, limit: 20")

            try:
                res = await self._material_index.search(
                    query="",
                    vector=vector,
                    hybrid=Hybrid(
                        semantic_ratio=1.0, embedder=EMBEDDER_NAME
                    ),
                    filter=f_unused,
                    limit=20,
                    ranking_score_threshold=0,
                    show_ranking_score=True,
                )

                docs: list[Doc] = [Doc.from_hit(hit) for hit in res.hits]
                
                if len(docs) < 20:
                    needed = 20 - len(docs)
                    logging.info(
                        f"Found only {len(docs)} unused chunks, fetching {needed} used chunks"
                    )
                    
                    f_used = f"userId = {dto.user_id} AND used = true"
                    if dto.material_ids:
                        f_used += f" AND materialId IN [{','.join(dto.material_ids)}]"
                    
                    res_used = await self._material_index.search(
                        query="",
                        vector=vector,
                        hybrid=Hybrid(
                            semantic_ratio=1.0, embedder=EMBEDDER_NAME
                        ),
                        filter=f_used,
                        limit=needed,
                        ranking_score_threshold=0,
                        show_ranking_score=True,
                    )
                    
                    docs_used: list[Doc] = [Doc.from_hit(hit) for hit in res_used.hits]
                    docs.extend(docs_used)
                    logging.info(
                        f"Added {len(docs_used)} used chunks, total: {len(docs)}"
                    )

                if len(docs) > 0:
                    documents = [doc.content for doc in docs]
                    query_for_reranking = f"Cluster {idx + 1}: semantically related educational content"
                    
                    logging.info(f"Reranking {len(documents)} chunks for vector {idx + 1}")
                    rerank_results = await self._llm_tools.rerank(
                        query=query_for_reranking,
                        documents=documents,
                        top_k=4
                    )
                    
                    for result in rerank_results:
                        doc = docs[result.index]
                        chunk = doc.to_chunk()
                        
                        if chunk.id not in seen_chunk_ids:
                            seen_chunk_ids.add(chunk.id)
                            all_chunks.append(chunk)
                            logging.info(
                                f"Vector {idx + 1}: Reranked chunk #{result.index} "
                                f"(score: {result.relevance_score:.3f})"
                            )

            except Exception as e:
                logging.error(f"Error searching for vector {idx + 1}: {e}")
                continue

        logging.info(f"Vector search complete: {len(all_chunks)} total unique chunks from {len(dto.vectors)} vectors")
        return all_chunks
