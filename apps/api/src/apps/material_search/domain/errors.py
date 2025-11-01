from .constants import MAX_SIZE_MB, MAX_TEXT_INDEX_TOKENS


class TooLargeFileError(Exception):
    def __init__(self, file_size_mb: float, max_size_mb: int = MAX_SIZE_MB):
        self.message = (
            f"File is too large ({file_size_mb}MB). Maximum size: {max_size_mb}MB"
        )
        super().__init__(self.message)


class TooManyTextTokensError(Exception):
    def __init__(self, text_tokens: int, max_text_tokens: int = MAX_TEXT_INDEX_TOKENS):
        self.message = f"Text is too long ({text_tokens} tokens). Maximum tokens: {max_text_tokens}"
        super().__init__(self.message)
