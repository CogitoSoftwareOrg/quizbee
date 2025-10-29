from typing import Any, AsyncGenerator, AsyncIterable, Literal, Protocol
from dataclasses import dataclass

from ..domain.models import Attempt


@dataclass(frozen=True, slots=True)
class FinalizeCmd:
    quiz_id: str
    cache_key: str
    attempt_id: str
    token: str


@dataclass(frozen=True, slots=True)
class AskExplainerCmd:
    query: str
    item_id: str
    attempt_id: str
    token: str


@dataclass(frozen=True, slots=True)
class AskExplainerOutput:
    text: str
    msg_id: str
    i: int
    status: Literal["chunk", "done", "error"]


class QuizAttempterApp(Protocol):
    async def finalize(self, cmd: FinalizeCmd) -> None: ...

    def ask_explainer(
        self, cmd: AskExplainerCmd
    ) -> AsyncIterable[AskExplainerOutput]: ...
