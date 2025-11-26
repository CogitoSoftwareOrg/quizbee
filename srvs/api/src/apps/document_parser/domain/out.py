from typing import Protocol

from .models import ParsedDocument, DocumentImage


class ImageDescriber(Protocol):
    """
    Port: Интерфейс для описания изображений с помощью LLM.
    """

    async def describe(self, image_bytes: bytes, mime_type: str = "image/png") -> str:
        """
        Генерирует текстовое описание изображения.

        Args:
            image_bytes: Байты изображения
            mime_type: MIME-тип изображения

        Returns:
            Текстовое описание изображения
        """
        ...

    async def describe_batch(self, images: list[DocumentImage]) -> dict[str, str]:
        """
        Параллельно описывает несколько изображений.

        Args:
            images: Список изображений для описания

        Returns:
            Словарь {marker: description}
        """
        ...


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
        process_images: bool = True,
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
