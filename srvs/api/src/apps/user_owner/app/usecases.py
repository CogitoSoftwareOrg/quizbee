import logging

from ..domain.models import User, Subscription
from ..domain.out import UserVerifier, UserRepository

from ..domain._in import AuthUserApp, Principal

logger = logging.getLogger(__name__)


class AuthUserAppImpl(AuthUserApp):
    def __init__(self, user_verifier: UserVerifier, user_repository: UserRepository):
        self.user_verifier = user_verifier
        self.user_repository = user_repository

    async def validate(self, token: str | None = None) -> Principal:
        logger.info("AuthUserAppImpl.validate")
        user = await self.user_verifier.verify(token)
        return Principal(
            id=user.id,
            remaining=user.subscription.quiz_items_limit
            - user.subscription.quiz_items_usage,
            used=user.subscription.quiz_items_usage,
            limit=user.subscription.quiz_items_limit,
            storage_usage=user.subscription.storage_usage,
            storage_limit=user.subscription.storage_limit
            or (2 * 1024 * 1024 * 1024 if user.subscription.tariff == "free" else 0),
            tariff=user.subscription.tariff,
        )

    async def charge(self, user_id: str, cost: int) -> None:
        logger.info("AuthUserAppImpl.charge")
        user = await self.user_repository.get(user_id)
        await self.user_repository.save(user, cost=cost)

    async def update_storage(self, user_id: str, delta: int) -> None:
        logger.info("AuthUserAppImpl.update_storage")
        user = await self.user_repository.get(user_id)
        await self.user_repository.save(user, storage_delta=delta)
