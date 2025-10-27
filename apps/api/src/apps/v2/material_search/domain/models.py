from dataclasses import dataclass
from enum import StrEnum

from src.lib.utils import genID


class MaterialKind(StrEnum):
    SIMPLE = "simple"
    COMPLEX = "complex"


class MaterialStatus(StrEnum):
    UPLOADED = "uploaded"
    USED = "used"
    INDEXING = "indexing"
    INDEXED = "indexed"


@dataclass(frozen=True)
class MaterialFile:
    file_name: str
    file_bytes: bytes = b""


@dataclass(frozen=False)
class Material:
    title: str
    user_id: str
    status: MaterialStatus
    kind: MaterialKind
    tokens: int
    file: MaterialFile
    images: list[MaterialFile]
    contents: str  # JSON
    id: str
    is_book: bool = False
    text_file: MaterialFile | None = None

    # def create(
    #     self,
    #     user_id: str,
    #     title: str,
    #     kind: MaterialKind,
    #     tokens: int,
    #     file: MaterialFile,
    #     images: list[MaterialFile],
    #     contents: str,
    # ) -> "Material":
    #     return Material(
    #         id=genID(),
    #         title=title,
    #         user_id=user_id,
    #         status=MaterialStatus.UPLOADED,
    #         kind=kind,
    #         tokens=tokens,
    #         file=file,
    #         images=images,
    #         contents=contents,
    #     )
