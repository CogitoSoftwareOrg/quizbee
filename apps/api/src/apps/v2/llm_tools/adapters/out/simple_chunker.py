import re

from ...app.contracts import Chunker, TextTokenizer


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
        chunk_size: int = 512,
        overlap: int = 128,
        split_on_sentences: bool = True,
    ):
        self._tokenizer = tokenizer
        self._chunk_size = chunk_size
        self._overlap = overlap
        self._split_on_sentences = split_on_sentences

    def chunk(self, text: str) -> list[str]:
        """
        Split text into overlapping chunks.

        Args:
            text: Input text to chunk

        Returns:
            List of text chunks
        """
        if not text or not text.strip():
            return []

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()

        if self._split_on_sentences:
            return self._chunk_by_sentences(text)
        else:
            return self._chunk_by_tokens(text)

    def _chunk_by_sentences(self, text: str) -> list[str]:
        """
        Chunk text by sentences, respecting token limits.
        """
        # Split into sentences using common sentence boundaries
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

            # If single sentence exceeds chunk_size, split it by tokens
            if sentence_tokens > self._chunk_size:
                # Save current chunk if exists
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = []
                    current_tokens = 0

                # Split long sentence
                chunks.extend(self._split_long_text(sentence))
                continue

            # Check if adding sentence exceeds limit
            if current_tokens + sentence_tokens > self._chunk_size and current_chunk:
                # Save current chunk
                chunk_text = " ".join(current_chunk)
                chunks.append(chunk_text)

                # Start new chunk with overlap
                if self._overlap > 0:
                    current_chunk, current_tokens = self._create_overlap(
                        current_chunk, chunk_text
                    )
                else:
                    current_chunk = []
                    current_tokens = 0

            current_chunk.append(sentence)
            current_tokens += sentence_tokens

        # Add remaining chunk
        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def _chunk_by_tokens(self, text: str) -> list[str]:
        """
        Simple chunking by character approximation of tokens.
        """
        # Split text into words for better chunking
        words = text.split()

        chunks = []
        current_chunk = []
        current_tokens = 0

        for word in words:
            word_tokens = self._tokenizer.count_text(word)

            if current_tokens + word_tokens > self._chunk_size and current_chunk:
                # Save current chunk
                chunk_text = " ".join(current_chunk)
                chunks.append(chunk_text)

                # Start new chunk with overlap
                if self._overlap > 0:
                    current_chunk, current_tokens = self._create_overlap(
                        current_chunk, chunk_text
                    )
                else:
                    current_chunk = []
                    current_tokens = 0

            current_chunk.append(word)
            current_tokens += word_tokens

        # Add remaining chunk
        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def _create_overlap(
        self, previous_chunk: list[str], previous_text: str
    ) -> tuple[list[str], int]:
        """
        Create overlap from previous chunk.

        Returns:
            Tuple of (overlap_sentences, overlap_token_count)
        """
        overlap_items = []
        overlap_tokens = 0

        # Add sentences from the end until we reach overlap size
        for item in reversed(previous_chunk):
            item_tokens = self._tokenizer.count_text(item)
            if overlap_tokens + item_tokens > self._overlap:
                break
            overlap_items.insert(0, item)
            overlap_tokens += item_tokens

        return overlap_items, overlap_tokens

    def _split_long_text(self, text: str) -> list[str]:
        """
        Split text that's longer than chunk_size into smaller pieces.
        """
        words = text.split()
        chunks = []
        current_chunk = []
        current_tokens = 0

        for word in words:
            word_tokens = self._tokenizer.count_text(word)

            if current_tokens + word_tokens > self._chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_tokens = 0

            current_chunk.append(word)
            current_tokens += word_tokens

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks
