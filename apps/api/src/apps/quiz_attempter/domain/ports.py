from typing import Any, AsyncIterable, Protocol

from .models import Attempt
from .refs import MessageRef, QuizItemRef


class AttemptRepository(Protocol):
    async def get(self, id: str) -> Attempt: ...
    async def save(self, attempt: Attempt) -> None: ...


class AttemptFinalizer(Protocol):
    async def finalize(self, attempt: Attempt, cache_key: str) -> None: ...


class Explainer(Protocol):
    def explain(
        self,
        query: str,
        attempt: Attempt,
        item: QuizItemRef,
        ai_msg: MessageRef,
        cache_key: str,
    ) -> AsyncIterable[MessageRef]: ...
