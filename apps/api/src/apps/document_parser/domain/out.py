from typing import Protocol

from .models import ParsedDocument


class DocumentParser(Protocol):
    """
    Port: Интерфейс для парсинга документов.

    Реализации:
    - FitzPDFParser (для .pdf)
    - DocxDocumentParser (для .docx)
    - PptxDocumentParser (для .pptx)
    """

    def parse(
        self,
        file_bytes: bytes,
        file_name: str,
        process_images: bool = False,
    ) -> ParsedDocument:
        """
        Парсит документ из байтов.

        Args:
            file_bytes: Содержимое файла в виде байтов
            file_name: Имя файла (для контекста и определения типа)
            process_images: Нужно ли извлекать изображения

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
