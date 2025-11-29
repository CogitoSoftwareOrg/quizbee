from voyageai.client_async import AsyncClient

from src.lib.settings import settings

from ...domain.out import Reranker, RerankResult


class VoyageReranker(Reranker):
    """Voyage AI reranker for improving search result relevance."""

    def __init__(self, model: str = "rerank-2.5-lite"):
        self._aclient = AsyncClient(api_key=settings.voyageai_api_key)
        self._model = model

    async def rerank(
        self, query: str, documents: list[str], top_k: int = 4
    ) -> list[RerankResult]:
        """
        Rerank documents by relevance to query.

        Args:
            query: The search query with optional instructions
            documents: List of document strings to rerank
            top_k: Number of top results to return

        Returns:
            List of RerankResult sorted by relevance score (descending)
        """
        if not documents:
            return []

        instruction = (
            "Retrieve academically rigorous passages that provide core definitions, "
            "formal terminology, theorems, and fundamental mechanisms. "
            "Focus on dense theoretical explanations containing substantive facts."
        )
        query_with_instruction = f"Instruct: {instruction}\n\nQuery: {query}"

        result = await self._aclient.rerank(
            query=query_with_instruction,
            documents=documents,
            model=self._model,
            top_k=top_k,
            truncation=True,
        )

        return [
            RerankResult(
                index=r.index,
                document=r.document,
                relevance_score=r.relevance_score,
            )
            for r in result.results
        ]
