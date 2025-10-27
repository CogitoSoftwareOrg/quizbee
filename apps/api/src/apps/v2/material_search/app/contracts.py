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


class MaterialAdder(Protocol):
    async def add_material(self, cmd: AddMaterialCmd) -> Material: ...


class MaterialSearcher(Protocol):
    def search(self, query: str) -> list[Material]: ...
