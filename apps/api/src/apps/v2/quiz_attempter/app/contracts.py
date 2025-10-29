from dataclasses import dataclass
from typing import Protocol

from ..domain.models import Attempt


@dataclass(frozen=True, slots=True)
class CreateCmd:
    quiz_id: str
    token: str


@dataclass(frozen=True, slots=True)
class FinalizeCmd:
    attempt_id: str
    token: str


class QuizAttempterApp(Protocol):
    async def create(self, cmd: CreateCmd) -> Attempt: ...

    async def finalize(self, cmd: FinalizeCmd) -> None: ...
