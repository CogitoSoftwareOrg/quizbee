"""
PPTX парсер для извлечения текста и изображений из .pptx файлов.

TODO: Реализовать парсинг PPTX используя python-pptx библиотеку.
"""
import logging

from ....domain.ports import DocumentParser
from ....domain.models import ParsedDocument, DocumentImage

logger = logging.getLogger(__name__)


class PptxDocumentParser(DocumentParser):
    """
    Парсер для PPTX файлов.
    
    TODO: Реализовать извлечение:
    - Текста из слайдов
    - Изображений из презентации
    - Структуры презентации (заголовки слайдов)
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
        Парсит PPTX документ.

        Args:
            file_bytes: Байты PPTX файла
            file_name: Имя файла (для логирования)
            process_images: Извлекать ли изображения

        Returns:
            ParsedDocument с результатом парсинга

        Raises:
            NotImplementedError: Парсинг PPTX пока не реализован
        """
        logger.warning(f"PPTX парсинг пока не реализован для файла: {file_name}")
        raise NotImplementedError(
            "PPTX парсинг будет реализован позже. "
            "Используйте python-pptx библиотеку для извлечения текста и изображений."
        )
