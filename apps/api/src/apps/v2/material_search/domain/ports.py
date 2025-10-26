from dataclasses import dataclass
from typing import Any, Protocol

from .models import Material, MaterialFile


# ======ADAPTERS INTERFACES======


# Material Repository
@dataclass
class MaterialPatch:
    title: str | None = None
    text_file: MaterialFile | None = None


class MaterialRepository(Protocol):
    async def create(self, create: Material) -> Material: ...

    async def update(self, m_id: str, upd: MaterialPatch) -> Material: ...


# PDF Parser


class PdfParser(Protocol):
    def parse(self, material: bytes) -> dict[str, Any]: ...


# Tokenizer
class Tokenizer(Protocol):
    def encode(self, text: str) -> list[int]: ...

    def count_text(self, text: str) -> int: ...


class ImageTokenizer(Protocol):
    def count_image(self, width: int, height: int) -> int: ...
