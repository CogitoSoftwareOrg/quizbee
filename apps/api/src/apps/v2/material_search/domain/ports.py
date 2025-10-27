from dataclasses import dataclass
from typing import Any, Protocol

from .models import Material, MaterialFile


# ======ADAPTERS INTERFACES======


# Material Repository
class MaterialRepository(Protocol):
    async def create(self, create: Material) -> Material: ...

    async def update(self, upd: Material) -> Material: ...


# PDF Parser
@dataclass
class PdfImage:
    width: int
    height: int
    page: int
    index: int
    ext: str
    bytes: bytes
    file_name: str
    marker: str | None = None


@dataclass
class PdfParseResult:
    text: str
    images: list[PdfImage]
    contents: list[dict[str, Any]]
    is_book: bool


class PdfParser(Protocol):
    def parse(self, file_bytes: bytes) -> PdfParseResult: ...


# Tokenizer
class Tokenizer(Protocol):
    def encode(self, text: str) -> list[int]: ...

    def count_text(self, text: str) -> int: ...


class ImageTokenizer(Protocol):
    def count_image(self, width: int, height: int) -> int: ...


# Chunker


class Chunker(Protocol):
    def chunk(self, text: str) -> list[str]: ...


# Indexer
class Indexer(Protocol):
    async def index(self, material: Material) -> None: ...

