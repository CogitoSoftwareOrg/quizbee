from pocketbase import PocketBase

from src.lib.settings import settings

from ...domain.out import UserVerifier, UserRepository
from ...domain.errors import NoTokenError, ForbiddenError
from ...domain.models import User


class PBUserVerifier(UserVerifier):
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def verify(self, token: str | None = None, need_admin: bool = False) -> User:
        if not token:
            raise NoTokenError()

        pb = PocketBase(settings.pb_url)
        pb._inners.auth.set_user({"token": token, "record": {}})

        try:
            user = (await pb.collection("users").auth.refresh()).get("record", {})
            if need_admin:
                raise Exception("Not implemented admin check")

            user = await self.user_repository.get(user.get("id") or "")
            return user

        except Exception as e:
            raise ForbiddenError(f"Unauthorized: {e}")
