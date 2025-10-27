from typing import Protocol

from .models import User, Subscription


class GuardUser(Protocol):
    async def __call__(self, token: str | None = None) -> tuple[User, Subscription]: ...
