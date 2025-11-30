from langfuse import Langfuse
from voyageai.client_async import AsyncClient

from src.lib.settings import settings
from src.lib.config import LLMS

from ...domain.out import Reranker, RerankResult


class VoyageReranker(Reranker):
    """Voyage AI reranker for improving search result relevance."""

    def __init__(self, lf: Langfuse, model: str = LLMS.VOYAGE_RERANKER_2_5_LITE):
        self._aclient = AsyncClient(api_key=settings.voyageai_api_key)
        self._model = model
        self._lf = lf

    async def rerank(
        self,
        user_id: str,
        session_id: str,
        query: str,
        documents: list[str],
        top_k: int = 4,
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

        self._log_langfuse(user_id, session_id, result.total_tokens, "reranker")

        return [
            RerankResult(
                index=r.index,
                document=r.document,
                relevance_score=r.relevance_score,
            )
            for r in result.results
        ]

    def _log_langfuse(
        self, user_id: str, session_id: str, total_tokens: int, name: str
    ) -> None:
        with self._lf.start_as_current_span(name=name) as span:
            self._lf.update_current_generation(
                model=LLMS.VOYAGE_RERANKER_2_5_LITE,
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
