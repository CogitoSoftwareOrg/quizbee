from dataclasses import dataclass
from typing import Protocol

from ..domain.models import Attempt


@dataclass(frozen=True, slots=True)
class FinalizeCmd:
    quiz_id: str
    cache_key: str
    attempt_id: str
    token: str


class QuizAttempterApp(Protocol):
    async def finalize(self, cmd: FinalizeCmd) -> None: ...
