from typing import Protocol

from .models import Attempt


class AttemptRepository(Protocol):
    async def get(self, id: str) -> Attempt: ...
    async def save(self, attempt: Attempt) -> None: ...

