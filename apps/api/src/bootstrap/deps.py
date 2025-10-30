from fastapi import Request

from src.lib.settings import settings


async def http_ensure_admin_pb(request: Request):
    pb = request.app.state.admin_pb
    token = pb._inners.auth._token

    if not token or pb._inners.auth._is_token_expired():
        a = await pb.collection("_superusers").auth.with_password(
            settings.pb_email, settings.pb_password
        )
        pb._inners.auth.set_user(
            {"token": a.get("token", ""), "record": a.get("record", {})}
        )
