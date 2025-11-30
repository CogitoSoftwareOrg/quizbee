import re

from ...domain.out import Chunker, TextTokenizer
from ...domain.constants import DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP

class SimpleChunker(Chunker):
    """
    Classical text chunker for RAG scenarios with token-aware splitting.

    Features:
    - Splits text into chunks of approximately chunk_size tokens
    - Maintains overlap between chunks for context preservation
    - Attempts to split on sentence boundaries when possible
    - Returns text chunks (not tokens) for embedding
    """

    def __init__(
        self,
        tokenizer: TextTokenizer,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap: int = DEFAULT_CHUNK_OVERLAP,
        split_on_sentences: bool = True,
    ):
        self._tokenizer = tokenizer
        self._chunk_size = chunk_size
        self._overlap = overlap
        self._split_on_sentences = split_on_sentences

    @property
    def chunk_size(self) -> int:
        return self._chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        text = re.sub(r"\s+", " ", text).strip()

        if self._split_on_sentences:
            return self._chunk_by_sentences(text)
        else:
            return self._chunk_by_tokens(text)

    def _chunk_by_sentences(self, text: str) -> list[str]:
        sentence_endings = r"(?<=[.!?])\s+(?=[A-ZА-ЯЁ])"
        sentences = re.split(sentence_endings, text)

        if not sentences:
            return self._chunk_by_tokens(text)

        chunks = []
        current_chunk = []
        current_tokens = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence_tokens = self._tokenizer.count_text(sentence)

            if sentence_tokens > self._chunk_size:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = []
                    current_tokens = 0
                chunks.extend(self._split_long_text(sentence))
                continue

            potential_tokens = current_tokens + sentence_tokens

            if potential_tokens <= self._chunk_size:
                current_chunk.append(sentence)
                current_tokens = potential_tokens
            else:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    
                    if self._overlap > 0:
                        overlap_chunk, overlap_tokens = self._create_overlap(current_chunk)
                        current_chunk = overlap_chunk
                        current_tokens = overlap_tokens
                    else:
                        current_chunk = []
                        current_tokens = 0
                
                current_chunk.append(sentence)
                current_tokens += sentence_tokens

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def _chunk_by_tokens(self, text: str) -> list[str]:
        words = text.split()

        chunks = []
        current_chunk = []
        current_tokens = 0

        for word in words:
            word_tokens = self._tokenizer.count_text(word)
            potential_tokens = current_tokens + word_tokens

            if potential_tokens <= self._chunk_size:
                current_chunk.append(word)
                current_tokens = potential_tokens
            else:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    
                    if self._overlap > 0:
                        overlap_chunk, overlap_tokens = self._create_overlap(current_chunk)
                        current_chunk = overlap_chunk
                        current_tokens = overlap_tokens
                    else:
                        current_chunk = []
                        current_tokens = 0
                
                current_chunk.append(word)
                current_tokens += word_tokens

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def _create_overlap(
        self, previous_chunk: list[str]
    ) -> tuple[list[str], int]:
        overlap_items = []
        overlap_tokens = 0

        for item in reversed(previous_chunk):
            item_tokens = self._tokenizer.count_text(item)
            if overlap_tokens + item_tokens > self._overlap:
                break
            overlap_items.insert(0, item)
            overlap_tokens += item_tokens

        return overlap_items, overlap_tokens

    def _split_long_text(self, text: str) -> list[str]:
        words = text.split()
        chunks = []
        current_chunk = []
        current_tokens = 0

        for word in words:
            word_tokens = self._tokenizer.count_text(word)
            potential_tokens = current_tokens + word_tokens

            if potential_tokens <= self._chunk_size:
                current_chunk.append(word)
                current_tokens = potential_tokens
            else:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_tokens = word_tokens

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks
