from typing import AsyncIterable, Literal, Protocol
from dataclasses import dataclass

from src.apps.user_owner.domain._in import Principal

from .models import Attempt


@dataclass(frozen=True, slots=True)
class FinalizeAttemptCmd:
    quiz_id: str
    cache_key: str
    attempt_id: str
    user: Principal


@dataclass(frozen=True, slots=True)
class AskExplainerCmd:
    cache_key: str
    query: str
    item_id: str
    attempt_id: str
    user: Principal


@dataclass(frozen=True, slots=True)
class AskExplainerResult:
    text: str
    msg_id: str
    i: int
    status: Literal["chunk", "done", "error"]


class QuizAttempterApp(Protocol):
    async def finalize(self, cmd: FinalizeAttemptCmd) -> None: ...

    def ask_explainer(
        self, cmd: AskExplainerCmd
    ) -> AsyncIterable[AskExplainerResult]: ...
