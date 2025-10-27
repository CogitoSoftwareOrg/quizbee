from fastapi import HTTPException, Request

from src.apps.v2.user_auth.di import AuthUserAppDeps
from src.apps.v2.user_auth.domain.errors import NoTokenError, ForbiddenError


async def http_guard_and_set_user(request: Request, auth_user_app: AuthUserAppDeps):
    try:
        token = request.cookies.get("pb_token")
        user, sub = await auth_user_app.validate(token)
        request.state.user = user
        request.state.subscription = sub
    except NoTokenError as e:
        raise HTTPException(status_code=401, detail=e.message)
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=e.message)
