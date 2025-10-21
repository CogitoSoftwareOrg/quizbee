from typing import Annotated
from fastapi import Depends, Request, HTTPException
from pocketbase import PocketBase
from pocketbase.models.dtos import Record

from lib.settings import settings


def get_user(request: Request):
    return request.state.user


User = Annotated[Record, Depends(get_user)]


async def auth_user(request: Request):
    pb_token = request.cookies.get("pb_token")
    if not pb_token:
        raise HTTPException(status_code=401, detail=f"Unauthorized: no pb_token")
    try:
        pb = PocketBase(settings.pb_url)
        pb._inners.auth.set_user({"token": pb_token, "record": {}})
        user = (await pb.collection("users").auth.refresh()).get("record", {})
        request.state.user = user
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Unauthorized: {e}")
