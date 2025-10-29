# APP
from dataclasses import dataclass
from typing import Protocol

from ..domain.models import Material, MaterialFile, MaterialChunk


@dataclass
class AddMaterialCmd:
    token: str
    file: MaterialFile
    title: str
    material_id: str


@dataclass
class SearchCmd:
    token: str
    query: str
    user_id: str
    material_ids: list[str]
    limit_tokens: int


class MaterialSearchApp(Protocol):
    async def add_material(self, cmd: AddMaterialCmd) -> Material: ...

    async def search(self, cmd: SearchCmd) -> list[MaterialChunk]: ...
