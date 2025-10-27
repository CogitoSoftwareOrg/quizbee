from fastapi import FastAPI, Request, Depends
from typing import Annotated

from .domain.ports import GuardUser
from .domain.models import User, Subscription
from .adapters.out.pb_guard_user import PBGuardUser


def get_user(request: Request) -> User:
    return request.state.user


UserDeps = Annotated[User, Depends(get_user)]


def get_subscription(request: Request) -> Subscription:
    return request.state.subscription


SubscriptionDeps = Annotated[Subscription, Depends(get_subscription)]


def set_auth_guard(app: FastAPI):
    app.state.auth_guard = PBGuardUser()


def get_auth_guard(request: Request):
    return request.app.state.auth_guard


AuthGuardDeps = Annotated[GuardUser, Depends(get_auth_guard)]
