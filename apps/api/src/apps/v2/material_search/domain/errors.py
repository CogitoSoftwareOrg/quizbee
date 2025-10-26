from .constants import MAX_SIZE_MB


class TooLargeFileError(Exception):
    def __init__(self, file_size_mb: float, max_size_mb: int = MAX_SIZE_MB):
        self.message = (
            f"File is too large ({file_size_mb}MB). Maximum size: {max_size_mb}MB"
        )
        super().__init__(self.message)
