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
    DELETING = "deleting"


@dataclass(frozen=True)
class MaterialFile:
    file_name: str
    file_bytes: bytes = b""


@dataclass(frozen=True)
class MaterialChunk:
    id: str
    idx: int
    material_id: str
    title: str
    content: str


@dataclass(frozen=False)
class Material:
    id: str
    title: str
    user_id: str
    status: MaterialStatus
    kind: MaterialKind
    tokens: int
    file: MaterialFile
    images: list[MaterialFile]
    contents: str  # JSON
    is_book: bool = False
    text_file: MaterialFile | None = None

    @classmethod
    def create(
        cls,
        user_id: str,
        title: str,
        file: MaterialFile,
        id=genID(),
        status=MaterialStatus.UPLOADED,
        kind=MaterialKind.SIMPLE,
        tokens: int = 0,
        contents: str = "",
        images: list[MaterialFile] | None = None,
    ) -> "Material":
        if images is None:
            images = []

        return cls(
            id=id,
            title=title,
            status=status,
            user_id=user_id,
            kind=kind,
            tokens=tokens,
            file=file,
            images=images,
            contents=contents,
        )
