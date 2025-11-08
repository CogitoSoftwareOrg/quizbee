from dataclasses import dataclass, field
from enum import StrEnum

from src.lib.utils import genID


@dataclass
class ParsedDocumentImage:
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
    """Результат парсинга документа в material_search контексте."""
    text: str  # Извлечённый текст с маркерами изображений
    images: list[ParsedDocumentImage]  # Список извлечённых изображений
    contents: list[dict]  # Оглавление/структура документа
    is_book: bool  # Является ли документ книгой


class MaterialKind(StrEnum):
    SIMPLE = "simple"
    COMPLEX = "complex"


class MaterialStatus(StrEnum):
    UPLOADED = "uploaded"
    USED = "used"
    INDEXING = "indexing"
    INDEXED = "indexed"
    DELETING = "deleting"
    TOO_BIG = "too big"
    NO_TEXT = "no text"


@dataclass(slots=True, kw_only=True)
class MaterialFile:
    file_name: str
    file_bytes: bytes = b""


@dataclass(slots=True, kw_only=True)
class MaterialChunk:
    id: str
    idx: int
    material_id: str
    title: str
    content: str


@dataclass(slots=True, kw_only=True)
class Material:
    user_id: str
    title: str
    file: MaterialFile
    images: list[MaterialFile] = field(default_factory=list)
    kind: MaterialKind = MaterialKind.SIMPLE
    tokens: int = 0
    contents: str = ""
    is_book: bool = False
    status: MaterialStatus = MaterialStatus.UPLOADED
    text_file: MaterialFile | None = None
    id: str = field(default_factory=genID)

    @classmethod
    def create(
        cls,
        id: str,
        user_id: str,
        title: str,
        file: MaterialFile,
    ) -> "Material":
        return cls(
            id=id,
            title=title,
            user_id=user_id,
            file=file,
        )

    def to_big(self):
        self.status = MaterialStatus.TOO_BIG
