from dataclasses import dataclass
from typing import Any, Protocol

from src.lib.config.llms import LLMS
from src.apps.document_parser.domain import DocumentParseCmd

from .models import Material, MaterialFile, MaterialChunk, ParsedDocument, SearchType


# ======ADAPTERS INTERFACES======



# Material Repository
class MaterialRepository(Protocol):
    async def get(self, id: str) -> Material | None: ...

    async def update(self, material: Material) -> None: ...
    async def create(self, material: Material) -> None: ...
    async def delete(self, material_id: str) -> None: ...

    async def attach_to_quiz(self, material: Material, quiz_id: str) -> None: ...


# Document Parsing (Port для работы с parsers Shared Kernel)
class DocumentParser(Protocol):
    """
    Port для парсинга документов разных форматов.

    Зависит от parsers Shared Kernel.
    Реализация: DocumentParsingAdapter
    """

    def parse(
        self,
        cmd: DocumentParseCmd,
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


# LLM Tools (Port для работы с LLM инструментами)
class LLMTools(Protocol):
    """
    Port для работы с LLM инструментами (подсчет токенов, chunking).
    
    Реализация: LLMToolsAdapter
    """

    @property
    def chunk_size(self) -> int:
        """Размер chunk'а в токенах."""
        ...

    def count_text(self, text: str, llm: LLMS = LLMS.GPT_5_MINI) -> int:
        """Подсчитывает токены в тексте для указанной модели."""
        ...

    def count_image(self, width: int, height: int) -> int:
        """Подсчитывает токены для изображения по его размерам."""
        ...

    def chunk(self, text: str) -> list[str]:
        """Разбивает текст на chunks."""
        ...


# Indexer
class MaterialIndexer(Protocol):
    async def index(self, material: Material) -> None: ...
    async def delete(self, material_ids: list[str]) -> None: ...



# Searcher
class Searcher(Protocol):
    async def search(
        self,
        user_id: str,
        query: str,
        material_ids: list[str],
        limit: int,
        ratio: float,
    ) -> list[MaterialChunk]: ...




# Indexer
class SearcherProvider(Protocol):
    def get(
        self,
        search_type: SearchType,
    ) -> Searcher : ...
