"""
Фабрика для выбора парсера документов по расширению файла.
"""
import logging

from ...domain.ports import DocumentParser
from .concrete_parsers.pdf_parser import FitzPDFParser
from .concrete_parsers.docx_parser import DocxDocumentParser
from .concrete_parsers.pptx_parser import PptxDocumentParser

logger = logging.getLogger(__name__)


class ParserFactory:
    """
    Фабрика для создания парсеров документов.
    
    Выбирает подходящий парсер на основе расширения файла.
    Позволяет регистрировать новые парсеры динамически.
    """

    # Реестр парсеров: расширение -> класс парсера
    _parsers: dict[str, type[DocumentParser]] = {
        'pdf': FitzPDFParser,
        'docx': DocxDocumentParser,
        'pptx': PptxDocumentParser,
    }

    @classmethod
    def get_parser(cls, file_ext: str) -> DocumentParser:
        """
        Получить парсер по расширению файла.
        
        Args:
            file_ext: Расширение файла (например, 'pdf', 'docx', 'pptx')
            
        Returns:
            Экземпляр парсера для указанного расширения
            
        Raises:
            ValueError: Если формат файла не поддерживается
        """
        file_ext = file_ext.lower().strip('.')
        
        if file_ext not in cls._parsers:
            supported = ', '.join(cls._parsers.keys())
            logger.error(
                f"Неподдерживаемый формат файла: {file_ext}. "
                f"Поддерживаются: {supported}"
            )
            raise ValueError(
                f"Неподдерживаемый формат файла: {file_ext}. "
                f"Поддерживаются: {supported}"
            )
        
        parser_class = cls._parsers[file_ext]
        logger.debug(f"Создан парсер {parser_class.__name__} для расширения '{file_ext}'")
        
        # Создаем экземпляр парсера с параметрами по умолчанию
        return parser_class()
    
    @classmethod
    def register_parser(
        cls,
        file_ext: str,
        parser_class: type[DocumentParser]
    ) -> None:
        """
        Зарегистрировать новый парсер для расширения файла.
        
        Позволяет динамически добавлять поддержку новых форматов.
        
        Args:
            file_ext: Расширение файла (например, 'txt', 'md')
            parser_class: Класс парсера, реализующий DocumentParser
        """
        file_ext = file_ext.lower().strip('.')
        cls._parsers[file_ext] = parser_class
        logger.info(
            f"Зарегистрирован парсер {parser_class.__name__} "
            f"для расширения '{file_ext}'"
        )
    
    @classmethod
    def get_supported_extensions(cls) -> list[str]:
        """
        Получить список поддерживаемых расширений файлов.
        
        Returns:
            Список расширений (например, ['pdf', 'docx', 'pptx'])
        """
        return list(cls._parsers.keys())
