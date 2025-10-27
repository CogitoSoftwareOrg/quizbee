from typing import Protocol

from ..domain.models import User, Subscription


class TokenValidator(Protocol):
    async def validate(self, token: str) -> tuple[User, Subscription]: ...
