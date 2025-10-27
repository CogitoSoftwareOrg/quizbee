from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from ..domain.models import Quiz


class GenMode(StrEnum):
    Continue = "continue"
    Regenerate = "regenerate"


@dataclass(frozen=True)
class FinilizeCmd:
    quiz_id: str


@dataclass(frozen=True)
class GenerateCmd:
    quiz_id: str
    user_id: str
    mode: GenMode


class QuizGenerator(Protocol):
    async def generate(self, cmd: GenerateCmd) -> None: ...


class QuizFinilizer(Protocol):
    async def finilize(self, cmd: FinilizeCmd) -> None: ...
