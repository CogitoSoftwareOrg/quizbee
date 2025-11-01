from pocketbase import PocketBase

from src.lib.settings import settings


async def ensure_admin_pb(ctx: dict):
    pb: PocketBase = ctx["pb"]
    token = pb._inners.auth._token

    if not token or pb._inners.auth._is_token_expired():
        a = await pb.collection("_superusers").auth.with_password(
            settings.pb_email, settings.pb_password
        )
        pb._inners.auth.set_user(
            {"token": a.get("token", ""), "record": a.get("record", {})}
        )
