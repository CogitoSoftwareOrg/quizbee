"""
Адаптер для DocumentParsing в material_search.

Связывает domain port DocumentParsing с parsers Shared Kernel.
"""
import logging

from ...domain.ports import DocumentParsing
from ...domain.models import ParsedDocument, ParsedDocumentImage
from src.apps.parsers.domain.models import ParsedDocument as ParsersParsedDocument
from src.apps.parsers.adapters.out.parser_factory import ParserFactory

logger = logging.getLogger(__name__)


class DocumentParsingAdapter(DocumentParsing):
    """
    Адаптер для работы с parsers Shared Kernel.
    
    Реализует domain port DocumentParsing через парсеры из parsers гексагона.
    Использует ParserFactory для выбора парсера по расширению файла.
    """

    def _convert_to_domain_model(self, parser_result: ParsersParsedDocument) -> ParsedDocument:
        """
        Преобразует модель из parsers гексагона в модель material_search домена.
        
        Args:
            parser_result: Результат парсинга из parsers гексагона
            
        Returns:
            ParsedDocument для material_search домена
        """
        # Преобразуем изображения
        images = [
            ParsedDocumentImage(
                bytes=img.bytes,
                ext=img.ext,
                width=img.width,
                height=img.height,
                page=img.page,
                index=img.index,
                marker=img.marker,
                file_name=img.file_name,
            )
            for img in parser_result.images
        ]
        
        return ParsedDocument(
            text=parser_result.text,
            images=images,
            contents=parser_result.contents,
            is_book=parser_result.is_book,
        )

    def parse(
        self,
        file_bytes: bytes,
        file_name: str,
        process_images: bool = False,
    ) -> ParsedDocument:
        """
        Парсит документ, выбрав подходящий парсер по расширению файла.

        Args:
            file_bytes: Содержимое файла
            file_name: Имя файла (используется для выбора парсера)
            process_images: Извлекать ли изображения

        Returns:
            ParsedDocument с результатом парсинга

        Raises:
            ValueError: Если формат файла не поддерживается
            NotImplementedError: Если парсер для формата ещё не реализован
        """
        logger.info(f"DocumentParsingAdapter: парсинг {file_name}")
        
        # Определяем тип файла по расширению
        file_ext = file_name.lower().split('.')[-1]
        
        # Получаем парсер из фабрики
        parser = ParserFactory.get_parser(file_ext)
        
        # Парсим документ через парсер из parsers гексагона
        parser_result: ParsersParsedDocument = parser.parse(
            file_bytes, file_name, process_images
        )
        
        # Преобразуем модель из parsers в модель material_search
        return self._convert_to_domain_model(parser_result)
