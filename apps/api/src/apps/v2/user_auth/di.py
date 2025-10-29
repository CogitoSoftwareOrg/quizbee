from fastapi import FastAPI, Request, Depends
from typing import Annotated

from .domain.models import User, Subscription
from .domain.ports import UserVerifier, UserRepository


from .app.contracts import AuthUserApp
from .app.usecases import AuthUserAppImpl


def get_user(request: Request) -> User:
    return request.state.user


UserDeps = Annotated[User, Depends(get_user)]


def get_subscription(request: Request) -> Subscription:
    return request.state.subscription


SubscriptionDeps = Annotated[Subscription, Depends(get_subscription)]


def set_auth_user_app(
    app: FastAPI, user_verifier: UserVerifier, user_repository: UserRepository
):
    app.state.auth_user_app = AuthUserAppImpl(user_verifier, user_repository)


def get_auth_user_app(request: Request):
    return request.app.state.auth_user_app


AuthUserAppDeps = Annotated[AuthUserApp, Depends(get_auth_user_app)]
