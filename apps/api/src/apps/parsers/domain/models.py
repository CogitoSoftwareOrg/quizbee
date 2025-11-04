"""
Domain models для parsers гексагона.
"""
from dataclasses import dataclass


@dataclass
class DocumentImage:
    """Изображение, извлечённое из документа."""
    bytes: bytes
    ext: str  # png, jpg, jpeg и т.д.
    width: int
    height: int
    page: int  # номер страницы (для PDF) или слайда (для PPTX)
    index: int  # индекс изображения на странице
    marker: str | None = None  # маркер для вставки в текст
    file_name: str = ""


@dataclass
class ParsedDocument:
    """Результат парсинга документа любого типа."""
    text: str  # Извлечённый текст с маркерами изображений
    images: list[DocumentImage]  # Список извлечённых изображений
    contents: list[dict]  # Оглавление/структура документа
    is_book: bool  # Является ли документ книгой (применимо в основном к PDF)
