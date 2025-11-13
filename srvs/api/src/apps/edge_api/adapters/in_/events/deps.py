import time
from pocketbase import PocketBase

from src.lib.settings import settings


async def ensure_admin_pb(ctx: dict):
    pb: PocketBase = ctx["pb"]
    lock = ctx["admin_auth_lock"]

    tok = pb._inners.auth._token
    if tok and not pb._inners.auth._is_token_expired():
        return pb

    async with lock:
        tok = pb._inners.auth._token
        if tok and not pb._inners.auth._is_token_expired():
            return pb

        pb._inners.auth.clean()
        try:
            a = await pb.collection("_superusers").auth.with_password(
                settings.pb_email, settings.pb_password
            )
        except Exception:
            pb._inners.auth.clean()
            a = await pb.collection("_superusers").auth.with_password(
                settings.pb_email, settings.pb_password
            )

        pb._inners.auth.set_user(
            {"token": a.get("token", ""), "record": a.get("record", {})}
        )
    return pb
