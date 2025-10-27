from pocketbase import PocketBase
from pocketbase.models.dtos import Record

from src.lib.settings import settings

from ...domain.ports import GuardUser
from ...domain.errors import NoTokenError, ForbiddenError
from ...domain.models import User, Subscription


class PBGuardUser(GuardUser):
    async def __call__(
        self, token: str | None = None, need_admin: bool = False
    ) -> tuple[User, Subscription]:
        if not token:
            raise NoTokenError()

        pb = PocketBase(settings.pb_url)
        pb._inners.auth.set_user({"token": token, "record": {}})

        try:
            user = (await pb.collection("users").auth.refresh()).get("record", {})
            if need_admin:
                raise Exception("Not implemented admin check")

            user_id = user.get("id")
            sub = await pb.collection("subscriptions").get_first(
                options={"params": {"filter": f"user = '{user_id}'"}},
            )
            if sub is None:
                raise ForbiddenError("No subscription found")

            return self._to_user(user), self._to_subscription(sub)

        except Exception as e:
            raise ForbiddenError(f"Unauthorized: {e}")

    def _to_user(self, user: Record) -> User:
        return User(id=user.get("id") or "")

    def _to_subscription(self, sub: Record) -> Subscription:
        return Subscription(
            id=sub.get("id") or "",
            quiz_items_limit=sub.get("quizItemsLimit") or 0,
            quiz_items_usage=sub.get("quizItemsUsage") or 0,
        )
