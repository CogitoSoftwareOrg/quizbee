from dataclasses import dataclass
from typing import Any, Protocol

from src.lib.config.llms import LLMS

from .models import Material, MaterialFile, MaterialChunk


# ======ADAPTERS INTERFACES======


# Material Repository
class MaterialRepository(Protocol):
    async def get(self, id: str, file_bytes: bytes = b"") -> Material | None: ...

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


# Chunker


class Chunker(Protocol):
    def chunk(self, text: str) -> list[str]: ...


# Indexer
class Indexer(Protocol):
    async def index(self, material: Material) -> None: ...
    async def search(
        self, user_id: str, query: str, material_ids: list[str], limit: int
    ) -> list[MaterialChunk]: ...
    async def delete(self, material_ids: list[str]) -> None: ...
