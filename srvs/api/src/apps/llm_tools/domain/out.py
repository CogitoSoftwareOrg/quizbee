from typing import Protocol
import numpy as np
from dataclasses import dataclass, field

from src.lib.config import LLMS


@dataclass
class ChunkWithPages:
    content: str
    pages: list[int] = field(default_factory=list)


@dataclass
class TextChunk:
    """
    Chunk of text with metadata.

    Attributes:
        content: The text content of the chunk
        page: Page number where this chunk appears (1-indexed), or None if not tracked
        start_char: Starting character position in the original text
        end_char: Ending character position in the original text
    """

    content: str
    page: int | None = None
    start_char: int = 0
    end_char: int = 0


class TextTokenizer(Protocol):
    def encode(self, text: str, llm: LLMS = LLMS.GPT_5_MINI) -> list[int]: ...
    def decode(self, tokens: list[int], llm: LLMS = LLMS.GPT_5_MINI) -> str: ...
    def count_text(self, text: str, llm: LLMS = LLMS.GPT_5_MINI) -> int: ...


class ImageTokenizer(Protocol):
    def count_image(self, width: int, height: int) -> int: ...


class Chunker(Protocol):
    @property
    def chunk_size(self) -> int: ...

    def chunk(self, text: str) -> list[str]: ...

    def chunk_with_pages(self, text: str) -> list[ChunkWithPages]: ...


class Vectorizer(Protocol):
    async def vectorize(self, chunks: list[str]) -> np.ndarray: ...
    def embed(self, documents: list[str]) -> np.ndarray: ...


@dataclass
class RerankResult:
    """Result from reranking operation."""

    index: int
    document: str
    relevance_score: float


class Reranker(Protocol):
    async def rerank(
        self,
        user_id: str,
        session_id: str,
        query: str,
        documents: list[str],
        top_k: int = 4,
    ) -> list[RerankResult]: ...
