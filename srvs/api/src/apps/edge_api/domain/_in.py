from dataclasses import dataclass
from enum import StrEnum
from typing import AsyncIterable, Protocol

from src.apps.quiz_owner.domain._in import GenMode
from src.apps.material_owner.domain._in import MaterialFile, Material
from src.apps.quiz_attempter.domain._in import AskExplainerResult


class JobName(StrEnum):
    start_quiz = "start_quiz_job"
    generate_quiz_items = "generate_quiz_items_job"
    finalize_quiz = "finalize_quiz_job"
    finalize_attempt = "finalize_attempt_job"
    add_material = "add_material_job"
    remove_material = "remove_material_job"


@dataclass(frozen=True, slots=True)
class BaseCmd:
    quiz_id: str
    token: str
    cache_key: str


@dataclass(frozen=True, slots=True)
class PublicStartQuizCmd(BaseCmd): ...


@dataclass(frozen=True, slots=True)
class PublicGenerateQuizItemsCmd(BaseCmd):
    mode: GenMode


@dataclass(frozen=True, slots=True)
class PublicFinalizeQuizCmd(BaseCmd): ...


@dataclass(frozen=True, slots=True)
class PublicFinalizeAttemptCmd(BaseCmd):
    attempt_id: str


@dataclass(frozen=True, slots=True)
class PublicAskExplainerCmd(BaseCmd):
    item_id: str
    query: str
    attempt_id: str


@dataclass(frozen=True, slots=True)
class PublicAddMaterialCmd:
    token: str
    cache_key: str
    quiz_id: str | None
    file: MaterialFile
    title: str
    material_id: str
    hash: str = ""


@dataclass(frozen=True, slots=True)
class PublicRemoveMaterialCmd:
    token: str
    cache_key: str
    material_id: str


class EdgeAPIApp(Protocol):
    async def start_quiz(self, cmd: PublicStartQuizCmd) -> None: ...
    async def generate_quiz_items(self, cmd: PublicGenerateQuizItemsCmd) -> None: ...
    async def finalize_quiz(self, cmd: PublicFinalizeQuizCmd) -> None: ...
    async def finalize_attempt(self, cmd: PublicFinalizeAttemptCmd) -> None: ...

    async def add_material(self, cmd: PublicAddMaterialCmd) -> Material: ...
    async def remove_material(self, cmd: PublicRemoveMaterialCmd) -> None: ...

    def ask_explainer(
        self, cmd: PublicAskExplainerCmd
    ) -> AsyncIterable[AskExplainerResult]: ...
