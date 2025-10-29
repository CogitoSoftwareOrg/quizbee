from ..domain.models import User, Subscription
from ..domain.ports import UserVerifier, UserRepository

from .contracts import AuthUserApp, Principal


class AuthUserAppImpl(AuthUserApp):
    def __init__(self, user_verifier: UserVerifier, user_repository: UserRepository):
        self.user_verifier = user_verifier
        self.user_repository = user_repository

    async def validate(self, token: str | None = None) -> Principal:
        user = await self.user_verifier.verify(token)
        return Principal(
            id=user.id,
            remaining=user.subscription.quiz_items_limit
            - user.subscription.quiz_items_usage,
            used=user.subscription.quiz_items_usage,
            limit=user.subscription.quiz_items_limit,
        )

    async def charge(self, user_id: str, cost: int) -> None:
        user = await self.user_repository.get(user_id)
        await self.user_repository.save(user, cost)
