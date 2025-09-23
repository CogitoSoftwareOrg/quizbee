from fastapi import APIRouter, Depends, Request

from apps.auth.middleware import auth_user
from lib.clients import AdminPB


messages_router = APIRouter(
    prefix="/messages", tags=["messages"], dependencies=[Depends(auth_user)]
)


@messages_router.get("/see")
async def see_messages(
    request: Request,
    admin_pb: AdminPB,
):
    return {"message": "Hello, World!"}
