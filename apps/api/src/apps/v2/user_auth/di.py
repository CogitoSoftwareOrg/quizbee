from fastapi import FastAPI, Request, Depends
from typing import Annotated
from pocketbase.models.dtos import Record

from .domain.ports import GuardUser
from .adapters.out.pb_auth_user import PBGuardUser


def get_user(request: Request):
    return request.state.user


User = Annotated[Record, Depends(get_user)]


def get_subscription(request: Request):
    return request.state.subscription


Subscription = Annotated[Record, Depends(get_subscription)]


def set_auth_guard(app: FastAPI):
    app.state.auth_guard = PBGuardUser()


def get_auth_guard(request: Request):
    return request.app.state.auth_guard


AuthGuard = Annotated[GuardUser, Depends(get_auth_guard)]
