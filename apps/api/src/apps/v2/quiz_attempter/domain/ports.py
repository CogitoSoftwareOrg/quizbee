from typing import Any, AsyncIterable, Protocol

from .models import Attempt
from .refs import MessageRef, QuizItemRef


class AttemptRepository(Protocol):
    async def get(self, id: str) -> Attempt: ...
    async def save(self, attempt: Attempt) -> None: ...


# Порт для streaming объяснений - абстракция над LLM/AI
class Explainer(Protocol):
    def explain(
        self,
        query: str,
        attempt: Attempt,
        item: QuizItemRef,
        ai_msg: MessageRef,
        cache_key: str,
    ) -> AsyncIterable[MessageRef]: ...
