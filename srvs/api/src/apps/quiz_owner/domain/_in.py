from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from src.apps.user_owner.domain._in import Principal


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


class QuizStarter(Protocol):
    async def start(self, cmd: GenerateCmd) -> None: ...


class QuizGenerator(Protocol):
    async def generate(self, cmd: GenerateCmd) -> None: ...


class QuizFinalizer(Protocol):
    async def finalize(self, cmd: FinalizeQuizCmd) -> None: ...


class QuizApp(QuizStarter, QuizGenerator, QuizFinalizer): ...
