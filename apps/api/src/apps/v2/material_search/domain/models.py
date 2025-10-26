from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class MaterialKind(StrEnum):
    SIMPLE = "simple"
    COMPLEX = "complex"


class MaterialStatus(StrEnum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    ERROR = "error"


@dataclass(frozen=True)
class MaterialFile:
    file_name: str
    file_bytes: bytes = b""


@dataclass(frozen=False)
class Material:
    title: str
    user_id: str
    status: str
    kind: str
    tokens: int
    file: MaterialFile
    images: list[MaterialFile]
    contents: str  # JSON
    is_book: bool = False
    text_file: MaterialFile | None = None
    id: str | None = None
