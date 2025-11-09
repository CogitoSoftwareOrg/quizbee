from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from src.apps.user_owner.app.contracts import Principal


class GenMode(StrEnum):
    Continue = "continue"
    Regenerate = "regenerate"


@dataclass(frozen=True, slots=True)
class FinalizeQuizCmd:
    cache_key: str
    quiz_id: str
    user: Principal


@dataclass(frozen=True, slots=True)
class GenerateCmd:
    cache_key: str
    quiz_id: str
    mode: GenMode
    user: Principal


@dataclass(frozen=True, slots=True)
class AttachMaterialCmd:
    quiz_id: str
    material_id: str
    user: Principal


class QuizGeneratorApp(Protocol):
    async def start(self, cmd: GenerateCmd) -> None: ...
    async def generate(self, cmd: GenerateCmd) -> None: ...
    async def finalize(self, cmd: FinalizeQuizCmd) -> None: ...
