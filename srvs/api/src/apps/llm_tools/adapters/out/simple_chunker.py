import re

from ...domain.out import Chunker, TextTokenizer, TextChunk
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

    def chunk(self, text: str, respect_pages: bool = False) -> list[str] | list[TextChunk]:
        """
        Split text into overlapping chunks.

        Args:
            text: Input text to chunk
            respect_pages: If True, returns TextChunk objects with page information extracted from markers

        Returns:
            List of text chunks (str) or TextChunk objects if respect_pages=True
        """
        if not text or not text.strip():
            return []

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()

        if respect_pages:
            return self._chunk_with_pages(text)
        else:
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

    def _chunk_with_pages(self, text: str) -> list[TextChunk]:
        """
        Chunk text while preserving page information from markers.
        
        Extracts page numbers from {quizbee_page_number_N} markers and assigns
        them to chunks.
        
        Args:
            text: Input text with page markers
            
        Returns:
            List of TextChunk objects with page information
        """
        # Pattern to find page markers: {quizbee_page_number_N}
        page_pattern = r'\{quizbee_page_number_(\d+)\}'
        
        # Split text into segments by page markers
        segments = re.split(page_pattern, text)
        
        # segments will be [text_before_first_marker, page1, text1, page2, text2, ...]
        # If text starts with a marker: ['', page1, text1, page2, text2, ...]
        
        page_texts: list[tuple[int | None, str]] = []
        
        if len(segments) == 1:
            # No page markers found
            page_texts.append((None, segments[0]))
        else:
            # First segment is text before any marker (usually empty)
            if segments[0].strip():
                page_texts.append((None, segments[0]))
            
            # Process pairs of (page_number, text)
            for i in range(1, len(segments), 2):
                if i < len(segments):
                    page_num = int(segments[i])
                    text_content = segments[i + 1] if i + 1 < len(segments) else ""
                    if text_content.strip():
                        page_texts.append((page_num, text_content))
        
        # Now chunk each page's text separately
        all_chunks: list[TextChunk] = []
        global_char_offset = 0
        
        for page_num, page_text in page_texts:
            # Chunk this page's text
            if self._split_on_sentences:
                text_chunks = self._chunk_by_sentences(page_text)
            else:
                text_chunks = self._chunk_by_tokens(page_text)
            
            # Convert to TextChunk objects with page info
            for chunk_text in text_chunks:
                start_char = global_char_offset
                end_char = start_char + len(chunk_text)
                
                all_chunks.append(TextChunk(
                    content=chunk_text,
                    page=page_num,
                    start_char=start_char,
                    end_char=end_char
                ))
                
                global_char_offset = end_char
        
        return all_chunks
