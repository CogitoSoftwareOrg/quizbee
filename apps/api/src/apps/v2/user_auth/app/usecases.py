from ..domain.models import User, Subscription
from ..domain.ports import UserGuarder

from .contracts import TokenValidator


class AuthUserApp(TokenValidator):
    def __init__(self, guard_user: UserGuarder):
        self.guard_user = guard_user

    async def validate(self, token: str | None = None) -> tuple[User, Subscription]:
        return await self.guard_user.guard(token)
