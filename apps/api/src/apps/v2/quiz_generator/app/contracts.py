from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from ..domain.models import Attempt


class GenMode(StrEnum):
    Continue = "continue"
    Regenerate = "regenerate"


@dataclass(frozen=True)
class FinalizeCmd:
    quiz_id: str


@dataclass(frozen=True)
class GenerateCmd:
    quiz_id: str
    user_id: str
    mode: GenMode


class QuizGeneratorApp(Protocol):
    async def start(self, cmd: GenerateCmd) -> None: ...
    async def generate(self, cmd: GenerateCmd) -> None: ...
    async def finalize(self, cmd: FinalizeCmd) -> None: ...
    async def create_attempt(self, quiz_id: str, user_id: str) -> Attempt: ...
