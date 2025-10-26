from typing import Any
from pocketbase import PocketBase

from src.lib.settings import settings

from ...domain.ports import GuardUser
from ...domain.errors import NoTokenError, ForbiddenError


class PBGuardUser(GuardUser):
    async def __call__(self, token: str | None = None, need_admin: bool = False) -> Any:
        if not token:
            raise NoTokenError()

        pb = PocketBase(settings.pb_url)
        pb._inners.auth.set_user({"token": token, "record": {}})

        try:
            user = (await pb.collection("users").auth.refresh()).get("record", {})
            if need_admin:
                raise Exception("Not implemented admin check")
            return user

        except Exception as e:
            raise ForbiddenError(f"Unauthorized: {e}")
