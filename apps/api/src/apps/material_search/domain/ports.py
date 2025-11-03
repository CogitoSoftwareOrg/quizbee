from dataclasses import dataclass
from typing import Any, Protocol

from src.lib.config.llms import LLMS

from .models import Material, MaterialFile, MaterialChunk


# ======ADAPTERS INTERFACES======


# Material Repository
class MaterialRepository(Protocol):
    async def get(self, id: str) -> Material | None: ...

    async def update(self, material: Material) -> None: ...
    async def create(self, material: Material) -> None: ...
    async def delete(self, material_id: str) -> None: ...

    async def attach_to_quiz(self, material: Material, quiz_id: str) -> None: ...


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
    def parse(self, file_bytes: bytes, process_images: bool) -> PdfParseResult: ...


# Indexer
class MaterialIndexer(Protocol):
    async def index(self, material: Material) -> None: ...
    async def search(
        self,
        user_id: str,
        query: str,
        material_ids: list[str],
        limit: int,
        ratio: float,
    ) -> list[MaterialChunk]: ...
    async def delete(self, material_ids: list[str]) -> None: ...
