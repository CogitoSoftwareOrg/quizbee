"""
Фабрика для выбора парсера документов по расширению файла.
"""

import logging

from ...domain.out import DocumentParser, DocumentParserProvider

logger = logging.getLogger(__name__)


class ParserProviderV1(DocumentParserProvider):
    """
    Фабрика для создания парсеров документов.

    Выбирает подходящий парсер на основе расширения файла.
    Позволяет регистрировать новые парсеры динамически.
    """

    def __init__(self, parsers: dict[str, DocumentParser]):
        self._parsers = parsers

    def get(self, file_name: str) -> DocumentParser:
        """
        Получить парсер по расширению файла.

        Args:
            file_ext: Расширение файла (например, 'pdf', 'docx', 'pptx')

        Returns:
            Экземпляр парсера для указанного расширения

        Raises:
            ValueError: Если формат файла не поддерживается
        """
        file_ext = file_name.lower().strip(".")

        if file_ext not in self._parsers:
            supported = ", ".join(self._parsers.keys())
            logger.error(
                f"Неподдерживаемый формат файла: {file_ext}. "
                f"Поддерживаются: {supported}"
            )
            raise ValueError(
                f"Неподдерживаемый формат файла: {file_ext}. "
                f"Поддерживаются: {supported}"
            )

        return self._parsers[file_ext]

    def get_supported_extensions(self) -> list[str]:
        """
        Получить список поддерживаемых расширений файлов.

        Returns:
            Список расширений (например, ['pdf', 'docx', 'pptx'])
        """
        return list(self._parsers.keys())
