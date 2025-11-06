from dataclasses import dataclass
from typing import Any, Protocol

from src.lib.config.llms import LLMS

from .models import Material, MaterialFile, MaterialChunk, ParsedDocument


# ======ADAPTERS INTERFACES======


# LLM Tools
class LLMTools(Protocol):
    """Интерфейс для работы с LLM инструментами (токенизация, chunking)."""

    @property
    def chunk_size(self) -> int:
        """Размер чанка в токенах."""
        ...

    def count_text(self, text: str, llm: LLMS = LLMS.GPT_5_MINI) -> int:
        """Подсчитать количество токенов в тексте."""
        ...

    def count_image(self, width: int, height: int) -> int:
        """Подсчитать количество токенов для изображения."""
        ...

    def chunk(self, text: str) -> list[str]:
        """Разбить текст на чанки."""
        ...


# Material Repository
class MaterialRepository(Protocol):
    async def get(self, id: str) -> Material | None: ...

    async def update(self, material: Material) -> None: ...
    async def create(self, material: Material) -> None: ...
    async def delete(self, material_id: str) -> None: ...

    async def attach_to_quiz(self, material: Material, quiz_id: str) -> None: ...


# Document Parsing (Port для работы с parsers Shared Kernel)
class DocumentParsing(Protocol):
    """
    Port для парсинга документов разных форматов.
    
    Зависит от parsers Shared Kernel.
    Реализация: DocumentParsingAdapter
    """
    
    def parse(
        self,
        file_bytes: bytes,
        file_name: str,
        process_images: bool = False,
    ) -> ParsedDocument:
        """
        Парсит документ.
        
        Args:
            file_bytes: Содержимое файла в виде байтов
            file_name: Имя файла (для выбора формата)
            process_images: Нужно ли извлекать изображения
            
        Returns:
            ParsedDocument с текстом, изображениями и структурой
        """
        ...


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
