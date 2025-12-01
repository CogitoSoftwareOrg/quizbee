from typing import Protocol

from .models import ParsedDocument, DocumentImage


class DocumentParser(Protocol):
    """
    Port: Интерфейс для парсинга документов.

    Реализации:
    - FitzPDFParser (для .pdf)
    - DocxDocumentParser (для .docx)
    - PptxDocumentParser (для .pptx)
    """

    async def parse(
        self,
        file_bytes: bytes,
        file_name: str,
    ) -> ParsedDocument:
        """
        Парсит документ из байтов.

        Args:
            file_bytes: Содержимое файла в виде байтов
            file_name: Имя файла (для контекста и определения типа)

        Returns:
            ParsedDocument с текстом, изображениями и структурой
        """
        ...


class DocumentParserProvider(Protocol):
    """
    Port: Интерфейс для создания парсеров документов.
    """

    def get(self, file_name: str) -> DocumentParser:
        """
        Создает парсер для конкретного типа файла.
        """
        ...
