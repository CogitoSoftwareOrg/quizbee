from typing import Any, AsyncIterable, Protocol

from src.apps.material_owner.domain.models import MaterialChunk
from src.apps.user_owner.domain._in import Principal

from .models import Attempt
from .refs import MessageRef, QuizItemRef


class AttemptRepository(Protocol):
    async def get(self, id: str) -> Attempt: ...
    async def create(self, attempt: Attempt) -> None: ...
    async def update(self, attempt: Attempt) -> None: ...


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
        material_ids: list[str],
        user: Principal,
    ) -> AsyncIterable[MessageRef]: ...
