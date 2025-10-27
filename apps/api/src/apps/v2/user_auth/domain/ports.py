from typing import Protocol

from .models import User, Subscription


class UserGuarder(Protocol):
    async def guard(self, token: str | None = None) -> tuple[User, Subscription]: ...


class SubscriptionGuarder(Protocol): ...
