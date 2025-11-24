import re
from bisect import bisect_right
from itertools import accumulate
from dataclasses import dataclass
from typing import Any

from ...domain.out import Chunker, TextTokenizer, TextChunk
from ...domain.constants import DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP


@dataclass
class RecursiveLevel:
    """
    Defines a level in the recursive chunking hierarchy.
    
    Attributes:
        delimiters: List of delimiter strings to split on (e.g., ["\n\n"], ["."])
        include_delim: Where to attach the delimiter:
            - "prev": attach to previous chunk (default for punctuation)
            - "next": attach to next chunk (for headers like #)
            - None: remove delimiter
        whitespace: If True, split on whitespace (word-level splitting)
    """
    delimiters: list[str] | None = None
    include_delim: str | None = "prev"
    whitespace: bool = False


@dataclass
class RecursiveRules:
    """
    Container for hierarchical chunking rules.
    
    Attributes:
        levels: List of RecursiveLevel objects defining chunking strategy
                from coarsest to finest granularity
    """
    levels: list[RecursiveLevel] | None = None
    
    @classmethod
    def default(cls) -> "RecursiveRules":
        """Default rules: paragraphs -> sentences -> words."""
        return cls(levels=[
            RecursiveLevel(delimiters=["\n\n", "\r\n\r\n"], include_delim="prev"),
            RecursiveLevel(delimiters=[".", "!", "?", ";"], include_delim="prev"),
            RecursiveLevel(whitespace=True),
        ])
    
    @classmethod
    def markdown(cls) -> "RecursiveRules":
        """Markdown-aware rules: headers -> paragraphs -> sentences -> words."""
        return cls(levels=[
            RecursiveLevel(delimiters=["# "], include_delim="next"),
            RecursiveLevel(delimiters=["## "], include_delim="next"),
            RecursiveLevel(delimiters=["### "], include_delim="next"),
            RecursiveLevel(delimiters=["\n\n", "\r\n\r\n"], include_delim="prev"),
            RecursiveLevel(delimiters=[".", "!", "?"], include_delim="prev"),
            RecursiveLevel(whitespace=True),
        ])


class ChonkieRecursiveChunker(Chunker):
    """
    Recursive chunker based on Chonkie's RecursiveChunker.
    
    Splits text hierarchically using customizable rules to create 
    semantically meaningful chunks. Uses a cascade of levels (rules) to 
    split text at natural boundaries (paragraphs, sentences, words).
    
    Features:
    - Hierarchical splitting with RecursiveLevel objects
    - Token-aware chunking
    - Preserves semantic boundaries
    - Supports recipes (default, markdown)
    - Supports page-aware chunking
    """

    def __init__(
        self,
        tokenizer: TextTokenizer,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        rules: RecursiveRules | None = None,
        min_characters_per_chunk: int = 24,
        overlap: int = DEFAULT_CHUNK_OVERLAP,
    ):
        self._tokenizer = tokenizer
        self._chunk_size = chunk_size
        self._rules = rules or RecursiveRules.default()
        self._min_characters_per_chunk = min_characters_per_chunk
        self._overlap = overlap
        self._sep = "✄"

    @classmethod
    def from_recipe(
        cls,
        tokenizer: TextTokenizer,
        name: str = "default",
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        min_characters_per_chunk: int = 24,
        overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> "ChonkieRecursiveChunker":
        """
        Create chunker from a recipe.
        
        Args:
            tokenizer: Tokenizer instance
            name: Recipe name ("default" or "markdown")
            chunk_size: Maximum chunk size in tokens
            min_characters_per_chunk: Minimum characters per chunk
            overlap: Number of tokens to overlap between chunks
            
        Returns:
            ChonkieRecursiveChunker instance
        """
        if name == "markdown":
            rules = RecursiveRules.markdown()
        else:
            rules = RecursiveRules.default()
        
        return cls(
            tokenizer=tokenizer,
            rules=rules,
            chunk_size=chunk_size,
            min_characters_per_chunk=min_characters_per_chunk,
            overlap=overlap,
        )

    @property
    def chunk_size(self) -> int:
        return self._chunk_size

    def chunk(
        self, text: str, respect_pages: bool = False
    ) -> list[str] | list[TextChunk]:
        """
        Split text into chunks using recursive hierarchical splitting.

        Args:
            text: Input text to chunk
            respect_pages: If True, returns TextChunk objects with page information

        Returns:
            List of text chunks (str) or TextChunk objects if respect_pages=True
        """
        if not text or not text.strip():
            return []

        text = text.strip()

        if respect_pages:
            return self._chunk_with_pages(text)
        else:
            chunks = self._recursive_chunk(text, level=0)
            if self._overlap > 0:
                chunks = self._apply_overlap(chunks)
            return chunks

    def _split_text(self, text: str, recursive_level: RecursiveLevel) -> list[str]:
        """
        Split text based on the current level's rules.
        
        Args:
            text: Text to split
            recursive_level: Current level configuration
            
        Returns:
            List of text splits
        """
        if recursive_level.whitespace:
            splits = text.split(" ")
        elif recursive_level.delimiters:
            if recursive_level.include_delim == "prev":
                for delimiter in recursive_level.delimiters:
                    text = text.replace(delimiter, delimiter + self._sep)
            elif recursive_level.include_delim == "next":
                for delimiter in recursive_level.delimiters:
                    text = text.replace(delimiter, self._sep + delimiter)
            else:
                for delimiter in recursive_level.delimiters:
                    text = text.replace(delimiter, self._sep)

            splits = [split for split in text.split(self._sep) if split != ""]

            current = ""
            merged = []
            for split in splits:
                if len(split) < self._min_characters_per_chunk:
                    current += split
                elif current:
                    current += split
                    merged.append(current)
                    current = ""
                else:
                    merged.append(split)

                if len(current) >= self._min_characters_per_chunk:
                    merged.append(current)
                    current = ""

            if current:
                merged.append(current)

            splits = merged
        else:
            encoded = self._tokenizer.encode(text)
            token_splits = [
                encoded[i : i + self._chunk_size]
                for i in range(0, len(encoded), self._chunk_size)
            ]
            splits = []
            for token_chunk in token_splits:
                splits.append(self._tokenizer.decode(token_chunk))

        return splits

    def _merge_splits(
        self,
        splits: list[str],
        token_counts: list[int],
        combine_whitespace: bool = False,
    ) -> tuple[list[str], list[int]]:
        """
        Merge short splits into larger chunks up to chunk_size.
        
        Args:
            splits: List of text segments
            token_counts: Token count for each segment
            combine_whitespace: Whether to join with spaces
            
        Returns:
            Tuple of (merged_texts, merged_token_counts)
        """
        if not splits or not token_counts:
            return [], []

        if len(splits) != len(token_counts):
            raise ValueError(
                f"Number of splits {len(splits)} does not match "
                f"number of token counts {len(token_counts)}"
            )

        if all(counts > self._chunk_size for counts in token_counts):
            return splits, token_counts

        merged = []
        if combine_whitespace:
            cumulative_token_counts = list(
                accumulate([0] + token_counts, lambda x, y: x + y + 1)
            )
        else:
            cumulative_token_counts = list(accumulate([0] + token_counts))
        
        current_index = 0
        combined_token_counts = []

        while current_index < len(splits):
            current_token_count = cumulative_token_counts[current_index]
            required_token_count = current_token_count + self._chunk_size

            index = min(
                bisect_right(
                    cumulative_token_counts,
                    required_token_count,
                    lo=current_index,
                )
                - 1,
                len(splits),
            )

            if index == current_index:
                index += 1

            if combine_whitespace:
                merged.append(" ".join(splits[current_index:index]))
            else:
                merged.append("".join(splits[current_index:index]))

            combined_token_counts.append(
                cumulative_token_counts[min(index, len(splits))] - current_token_count
            )
            current_index = index

        return merged, combined_token_counts

    def _recursive_chunk(self, text: str, level: int = 0) -> list[str]:
        """
        Recursively chunk text using hierarchical rules.
        
        Args:
            text: Text to chunk
            level: Current recursion level (index into rules.levels)
            
        Returns:
            List of text chunks
        """
        if not text:
            return []

        if not self._rules.levels or level >= len(self._rules.levels):
            token_count = self._tokenizer.count_text(text)
            if token_count <= self._chunk_size:
                return [text]
            else:
                encoded = self._tokenizer.encode(text)
                token_splits = [
                    encoded[i : i + self._chunk_size]
                    for i in range(0, len(encoded), self._chunk_size)
                ]
                return [self._tokenizer.decode(ts) for ts in token_splits]

        curr_rule = self._rules.levels[level]
        splits = self._split_text(text, curr_rule)
        token_counts = [self._tokenizer.count_text(split) for split in splits]

        if curr_rule.delimiters is None and not curr_rule.whitespace:
            merged, combined_token_counts = splits, token_counts
        elif curr_rule.delimiters is None and curr_rule.whitespace:
            merged, combined_token_counts = self._merge_splits(
                splits, token_counts, combine_whitespace=True
            )
            merged = merged[:1] + [" " + text for i, text in enumerate(merged) if i != 0]
        else:
            merged, combined_token_counts = self._merge_splits(
                splits, token_counts, combine_whitespace=False
            )

        chunks: list[str] = []
        for split, token_count in zip(merged, combined_token_counts):
            if token_count > self._chunk_size:
                recursive_result = self._recursive_chunk(split, level + 1)
                chunks.extend(recursive_result)
            else:
                chunks.append(split)

        return chunks

    def _chunk_with_pages(self, text: str) -> list[TextChunk]:
        """
        Chunk text while preserving page information from markers.

        Args:
            text: Input text with page markers

        Returns:
            List of TextChunk objects with page information
        """
        page_pattern = r'\{quizbee_page_number_(\d+)\}'
        segments = re.split(page_pattern, text)

        page_texts: list[tuple[int | None, str]] = []

        if len(segments) == 1:
            page_texts.append((None, segments[0]))
        else:
            if segments[0].strip():
                page_texts.append((None, segments[0]))

            for i in range(1, len(segments), 2):
                if i < len(segments):
                    page_num = int(segments[i])
                    text_content = segments[i + 1] if i + 1 < len(segments) else ""
                    if text_content.strip():
                        page_texts.append((page_num, text_content))

        all_chunks: list[TextChunk] = []
        global_char_offset = 0

        for page_num, page_text in page_texts:
            text_chunks = self._recursive_chunk(page_text)

            if self._overlap > 0:
                text_chunks = self._apply_overlap(text_chunks)

            for chunk_text in text_chunks:
                start_char = global_char_offset
                end_char = start_char + len(chunk_text)

                all_chunks.append(
                    TextChunk(
                        content=chunk_text,
                        page=page_num,
                        start_char=start_char,
                        end_char=end_char,
                    )
                )

                global_char_offset = end_char

        return all_chunks

    def _apply_overlap(self, chunks: list[str]) -> list[str]:
        """
        Apply overlap between consecutive chunks.
        
        Args:
            chunks: List of text chunks
            
        Returns:
            List of chunks with overlap applied
        """
        if len(chunks) <= 1 or self._overlap == 0:
            return chunks

        overlapped_chunks = [chunks[0]]
        
        for i in range(1, len(chunks)):
            prev_chunk = chunks[i - 1]
            current_chunk = chunks[i]
            
            overlap_text = self._create_overlap_from_text(prev_chunk)
            
            if overlap_text:
                combined = overlap_text + " " + current_chunk
                overlapped_chunks.append(combined)
            else:
                overlapped_chunks.append(current_chunk)
        
        return overlapped_chunks

    def _create_overlap_from_text(self, text: str) -> str:
        """
        Extract overlap text from the end of a chunk.
        
        Args:
            text: Text to extract overlap from
            
        Returns:
            Overlap text
        """
        words = text.split()
        overlap_words = []
        overlap_tokens = 0
        
        for word in reversed(words):
            word_tokens = self._tokenizer.count_text(word)
            if overlap_tokens + word_tokens > self._overlap:
                break
            overlap_words.insert(0, word)
            overlap_tokens += word_tokens
        
        return " ".join(overlap_words)
