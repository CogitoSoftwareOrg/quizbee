"""
DOCX парсер для извлечения текста и изображений из .docx файлов.

TODO: Реализовать парсинг DOCX используя python-docx библиотеку.
"""
import logging

from ....domain.ports import DocumentParser
from ....domain.models import ParsedDocument, DocumentImage

logger = logging.getLogger(__name__)


class DocxDocumentParser(DocumentParser):
    """
    Парсер для DOCX файлов.
    
    TODO: Реализовать извлечение:
    - Текста из параграфов
    - Изображений из документа
    - Структуры документа (заголовки)
    """

    def __init__(
        self,
        min_width: int = 50,
        min_height: int = 50,
        min_file_size: int = 3 * 1024,
    ):
        """
        Args:
            min_width: Минимальная ширина изображения в пикселях
            min_height: Минимальная высота изображения в пикселях
            min_file_size: Минимальный размер файла изображения в байтах
        """
        self.min_width = min_width
        self.min_height = min_height
        self.min_file_size = min_file_size

    def parse(
        self,
        file_bytes: bytes,
        file_name: str,
        process_images: bool = False,
    ) -> ParsedDocument:
        """
        Парсит DOCX документ.

        Args:
            file_bytes: Байты DOCX файла
            file_name: Имя файла (для логирования)
            process_images: Извлекать ли изображения

        Returns:
            ParsedDocument с результатом парсинга

        Raises:
            NotImplementedError: Парсинг DOCX пока не реализован
        """
        logger.warning(f"DOCX парсинг пока не реализован для файла: {file_name}")
        raise NotImplementedError(
            "DOCX парсинг будет реализован позже. "
            "Используйте python-docx библиотеку для извлечения текста и изображений."
        )
