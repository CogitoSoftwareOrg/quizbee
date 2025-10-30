from dataclasses import dataclass
from typing import AsyncIterable, Protocol

from src.apps..quiz_generator.app.contracts import GenMode
from src.apps..material_search.app.contracts import MaterialFile, Material

from src.apps..quiz_attempter.app.contracts import AskExplainerResult


@dataclass(frozen=True, slots=True)
class BaseCmd:
    token: str
    cache_key: str


@dataclass(frozen=True, slots=True)
class PublicStartQuizCmd(BaseCmd):
    quiz_id: str


@dataclass(frozen=True, slots=True)
class PublicGenerateQuizItemsCmd(BaseCmd):
    quiz_id: str
    mode: GenMode


@dataclass(frozen=True, slots=True)
class PublicFinalizeQuizCmd(BaseCmd):
    quiz_id: str


@dataclass(frozen=True, slots=True)
class PublicFinalizeAttemptCmd(BaseCmd):
    quiz_id: str
    attempt_id: str


@dataclass(frozen=True, slots=True)
class PublicAskExplainerCmd(BaseCmd):
    quiz_id: str
    item_id: str
    query: str
    attempt_id: str


@dataclass(frozen=True, slots=True)
class PublicAddMaterialCmd(BaseCmd):
    file: MaterialFile
    title: str
    material_id: str


class EdgeAPIApp(Protocol):
    async def start_quiz(self, cmd: PublicStartQuizCmd) -> None: ...
    async def generate_quiz_items(self, cmd: PublicGenerateQuizItemsCmd) -> None: ...
    async def finalize_quiz(self, cmd: PublicFinalizeQuizCmd) -> None: ...
    async def finalize_attempt(self, cmd: PublicFinalizeAttemptCmd) -> None: ...

    async def add_material(self, cmd: PublicAddMaterialCmd) -> Material: ...

    def ask_explainer(
        self, cmd: PublicAskExplainerCmd
    ) -> AsyncIterable[AskExplainerResult]: ...
