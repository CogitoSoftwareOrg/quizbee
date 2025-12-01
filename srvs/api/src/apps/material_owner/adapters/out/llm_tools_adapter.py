"""
Адаптер для LLMTools.
Связывает порт LLMTools из domain с конкретной реализацией LLMToolsApp.
"""

from typing import Any

from src.lib.config import LLMS
from src.apps.llm_tools.domain._in import LLMToolsApp
from src.apps.llm_tools.domain.out import ChunkWithPages

from ...domain.out import LLMTools


class LLMToolsAdapter(LLMTools):
    """Адаптер, который делегирует вызовы к LLMToolsApp."""

    def __init__(self, llm_tools_app: LLMToolsApp):
        self._llm_tools_app = llm_tools_app

    @property
    def chunk_size(self) -> int:
        return self._llm_tools_app.chunk_size

    def count_text(self, text: str, llm: LLMS = LLMS.GPT_5_MINI) -> int:
        return self._llm_tools_app.count_text(text, llm)

    def count_image(self, width: int, height: int) -> int:
        return self._llm_tools_app.count_image(width, height)

    def chunk(self, text: str) -> list[str]:
        return self._llm_tools_app.chunk(text)

    def chunk_with_pages(self, text: str) -> list[ChunkWithPages]:
        return self._llm_tools_app.chunk_with_pages(text)

    async def rerank(
        self,
        user_id: str,
        session_id: str,
        query: str,
        documents: list[str],
        top_k: int = 4,
    ) -> list[Any]:
        return await self._llm_tools_app.rerank(
            user_id, session_id, query, documents, top_k
        )
