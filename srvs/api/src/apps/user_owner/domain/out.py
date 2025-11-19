from typing import Protocol

from .models import User


class UserVerifier(Protocol):
    async def verify(self, token: str | None = None) -> User: ...


class UserRepository(Protocol):
    async def get(self, user_id: str) -> User: ...
    async def save(self, user: User, cost: int = 0, storage_delta: int = 0) -> None: ...
