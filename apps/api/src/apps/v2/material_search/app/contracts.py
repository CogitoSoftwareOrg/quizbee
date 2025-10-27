# APP
from dataclasses import dataclass
from typing import Protocol

from ..domain.models import Material, MaterialFile


@dataclass
class AddMaterialCmd:
    file: MaterialFile
    title: str
    material_id: str
    user_id: str


@dataclass
class SearchCmd:
    query: str
    user_id: str
    material_ids: list[str]
    limit: int


class MaterialAdder(Protocol):
    async def add_material(self, cmd: AddMaterialCmd) -> Material: ...


class MaterialSearcher(Protocol):
    def search(self, cmd: SearchCmd) -> list[Material]: ...
