from pocketbase import PocketBase
from pocketbase.models.dtos import Record


from ...domain.models import Subscription, User
from ...domain.ports import UserRepository


class PBUserRepository(UserRepository):
    def __init__(self, pb: PocketBase):
        self.pb = pb

    async def get(self, user_id: str) -> User:
        rec = await self.pb.collection("users").get_one(
            user_id, options={"params": {"expand": "subscriptions_via_user"}}
        )
        return self._to_user(rec)

    async def save(self, user: User, cost: int) -> None:
        sub = user.subscription
        try:
            await self.pb.collection("subscriptions").update(
                sub.id,
                {
                    "quizItemsUsage+": cost,
                },
            )
        except Exception as e:
            raise Exception(f"Failed to update subscription {sub.id}: {e}")

    def _to_user(self, rec: Record) -> User:
        sub_rec = rec.get("expand", {}).get("subscriptions_via_user", [])[0]
        if not sub_rec:
            raise Exception("Subscription not found")

        return User(
            id=rec.get("id") or "",
            subscription=Subscription(
                id=sub_rec.get("id") or "",
                quiz_items_limit=sub_rec.get("quizItemsLimit") or 0,
                quiz_items_usage=sub_rec.get("quizItemsUsage") or 0,
            ),
        )
