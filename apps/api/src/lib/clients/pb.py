from pocketbase import PocketBase
from fastapi import FastAPI, Request, Depends
from typing import Annotated

from src.lib.settings import settings


def set_admin_pb(app: FastAPI) -> None:
    app.state.admin_pb = PocketBase(settings.pb_url)


def get_admin_pb(request: Request) -> PocketBase:
    return request.app.state.admin_pb


AdminPBDeps = Annotated[PocketBase, Depends(get_admin_pb)]
