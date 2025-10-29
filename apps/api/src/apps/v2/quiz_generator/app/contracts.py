from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from ..domain.models import Attempt


class GenMode(StrEnum):
    Continue = "continue"
    Regenerate = "regenerate"


@dataclass(frozen=True, slots=True)
class FinalizeCmd:
    cache_key: str
    quiz_id: str
    token: str


@dataclass(frozen=True, slots=True)
class GenerateCmd:
    cache_key: str
    quiz_id: str
    mode: GenMode
    token: str


class QuizGeneratorApp(Protocol):
    async def start(self, cmd: GenerateCmd) -> None: ...
    async def generate(self, cmd: GenerateCmd) -> None: ...
    async def finalize(self, cmd: FinalizeCmd) -> None: ...
    async def create_attempt(self, quiz_id: str, token: str) -> Attempt: ...
