import logging
from meilisearch_python_sdk import AsyncClient
from meilisearch_python_sdk.models.search import Hybrid

from ....domain.models import MaterialChunk
from ....domain.out import SearchDto, Searcher, LLMTools

from ..indexers.meili_material_indexer import EMBEDDER_NAME, Doc

MIN_CHUNK_CONTENT_LENGTH = 100
RERANK_TOP_K = 5


class MeiliMaterialVectorSearcher(Searcher):
    def __init__(self, meili: AsyncClient, llm_tools: LLMTools):
        self._meili = meili
        self._llm_tools = llm_tools
        self._material_index = meili.index(EMBEDDER_NAME)

    async def search(self, dto: SearchDto) -> list[MaterialChunk]:
        if not dto.vectors or len(dto.vectors) == 0:
            logging.warning("No vectors provided for explainer search")
            return []

        vector = dto.vectors[0]

        filter_str = f"userId = {dto.user_id}"
        if dto.material_ids:
            filter_str += f" AND materialId IN [{','.join(dto.material_ids)}]"

        fetch_limit = max(dto.limit * 3, 20)
        logging.info(
            f"Explainer search: filter={filter_str}, fetch_limit={fetch_limit}"
        )

        res = await self._material_index.search(
            query="",
            vector=vector,
            hybrid=Hybrid(semantic_ratio=1.0, embedder=EMBEDDER_NAME),
            filter=filter_str,
            limit=fetch_limit,
            ranking_score_threshold=0,
            show_ranking_score=True,
        )

        chunks = []
        for hit in res.hits:
            chunk = Doc.from_hit(hit).to_chunk()
            content_length = len(chunk.content.strip()) if chunk.content else 0
            if content_length >= MIN_CHUNK_CONTENT_LENGTH:
                chunks.append(chunk)
            else:
                logging.debug(
                    f"Skipping small chunk {chunk.id}: {content_length} chars"
                )

        if not chunks:
            logging.warning("No chunks found after filtering")
            return []

        if len(chunks) <= RERANK_TOP_K:
            logging.info(f"Skipping rerank: only {len(chunks)} chunks")
            return chunks[: dto.limit]

        documents = [c.content for c in chunks]
        base_query = (
            dto.query
            if dto.query and dto.query != "*"
            else "relevant educational content"
        )
        rerank_query = (
            f"{dto.rerank_prefix} {base_query}".strip()
            if dto.rerank_prefix
            else base_query
        )

        logging.info(
            f"Reranking {len(documents)} chunks with query: {rerank_query[:100]}..."
        )
        rerank_results = await self._llm_tools.rerank(
            user_id=dto.user_id,
            session_id=",".join(dto.material_ids),
            query=rerank_query,
            documents=documents,
            top_k=min(dto.limit, len(documents)),
        )

        reranked_chunks = []
        for result in rerank_results:
            chunk = chunks[result.index]
            reranked_chunks.append(chunk)
            logging.debug(
                f"Reranked chunk #{result.index} (score: {result.relevance_score:.3f})"
            )

        logging.info(f"Explainer search: {len(reranked_chunks)} chunks after reranking")
        return reranked_chunks
