from fastapi import FastAPI, Request, Depends
from typing import Annotated

from .domain.ports import UserGuarder
from .domain.models import User, Subscription
from .adapters.out.pb_guard_user import PBGuardUser

from .app.usecases import AuthUserApp


def get_user(request: Request) -> User:
    return request.state.user


UserDeps = Annotated[User, Depends(get_user)]


def get_subscription(request: Request) -> Subscription:
    return request.state.subscription


SubscriptionDeps = Annotated[Subscription, Depends(get_subscription)]


def set_auth_user_app(app: FastAPI):
    guard_user = PBGuardUser()
    app.state.auth_user_app = AuthUserApp(guard_user)


def get_auth_user_app(request: Request):
    return request.app.state.auth_user_app


AuthUserAppDeps = Annotated[AuthUserApp, Depends(get_auth_user_app)]
