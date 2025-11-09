# APP
from dataclasses import dataclass
from typing import Protocol
from enum import StrEnum

from src.apps.user_owner.app.contracts import Principal

from ..domain.models import Material, MaterialFile, MaterialChunk


@dataclass
class AddMaterialCmd:
    user: Principal
    file: MaterialFile
    title: str
    material_id: str
    quiz_id: str


@dataclass
class SearchCmd:
    user: Principal
    query: str
    material_ids: list[str]
    limit_tokens: int


@dataclass
class RemoveMaterialCmd:
    user: Principal
    material_id: str


class MaterialApp(Protocol):
    async def add_material(self, cmd: AddMaterialCmd) -> Material: ...

    async def search(self, cmd: SearchCmd) -> list[MaterialChunk]: ...

    async def remove_material(self, cmd: RemoveMaterialCmd) -> None: ...
