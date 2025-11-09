"""
Адаптер для DocumentParsing в material_search.

Связывает domain port DocumentParsing с parsers Shared Kernel.
"""

import logging

from src.apps.document_parser.domain import (
    DocumentParserApp,
    ParsedDocument as DocumentParserParsedDocument,
    DocumentParseCmd,
)

from ...domain.out import DocumentParser
from ...domain.models import ParsedDocument, ParsedDocumentImage

logger = logging.getLogger(__name__)


class DocumentParserAdapter(DocumentParser):
    """
    Адаптер для работы с parsers Shared Kernel.

    Реализует domain port DocumentParsing через парсеры из parsers гексагона.
    Использует ParserFactory для выбора парсера по расширению файла.
    """

    def __init__(self, document_parser_app: DocumentParserApp):
        self._document_parser_app = document_parser_app

    def parse(
        self,
        cmd: DocumentParseCmd,
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
        logger.info(f"DocumentParsingAdapter: парсинг {cmd.file_name}")

        parser_result = self._document_parser_app.parse(cmd)
        return self._convert_to_domain_model(parser_result)

    def _convert_to_domain_model(
        self, parser_result: DocumentParserParsedDocument
    ) -> ParsedDocument:
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
