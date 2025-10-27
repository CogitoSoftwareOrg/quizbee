from fastapi import HTTPException, Request

from src.apps.v2.user_auth.di import AuthGuard
from src.apps.v2.user_auth.domain.errors import NoTokenError, ForbiddenError


async def http_guard_and_set_user(request: Request, auth_guard: AuthGuard):
    try:
        token = request.cookies.get("pb_token")
        user = await auth_guard(token)
        request.state.user = user
        return user
    except NoTokenError as e:
        raise HTTPException(status_code=401, detail=e.message)
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=e.message)
