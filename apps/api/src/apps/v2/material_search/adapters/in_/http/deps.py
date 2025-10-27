from fastapi import Request

from src.apps.v2.user_auth.di import AuthUserAppDeps


async def http_guard_and_set_user(request: Request, auth_user_app: AuthUserAppDeps):
    token = request.cookies.get("pb_token")
    user, sub = await auth_user_app.validate(token)
    request.state.user = user
    request.state.subscription = sub
