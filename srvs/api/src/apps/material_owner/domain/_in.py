# APP
from dataclasses import dataclass
from typing import Any, Protocol

from src.apps.user_owner.domain._in import Principal

from .models import Material, MaterialFile, MaterialChunk, SearchType


@dataclass
class AddMaterialCmd:
    user: Principal
    file: MaterialFile
    title: str
    material_id: str
    quiz_id: str
    hash: str = ""


# class SearchIntent(StrEnum):
#     QUERY = "query"
#     DISTRIBUTION = "ditribution"
#     ALL = "all"


@dataclass
class SearchCmd:
    user: Principal
    material_ids: list[str]
    limit_tokens: int = 100
    limit_chunks: int | None = None
    query: str = ""
    rerank_prefix: str = ""
    all_chunks: bool = False
    vectors: list[list[float]] | None = None
    vector_thresholds: list[float] | None = None
    search_type: SearchType | None = None


@dataclass
class RemoveMaterialCmd:
    user: Principal
    material_id: str


class MaterialApp(Protocol):
    async def add_material(self, cmd: AddMaterialCmd) -> Material: ...

    async def get_material(self, material_id: str) -> Material | None: ...

    async def search(self, cmd: SearchCmd) -> list[MaterialChunk]: ...

    async def remove_material(self, cmd: RemoveMaterialCmd) -> None: ...

    async def mark_chunks_as_used(self, chunk_ids: list[str]) -> None: ...

    async def get_chunks_info(self, chunk_ids: list[str]) -> list[dict[str, Any]]: ...
