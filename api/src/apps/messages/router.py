from fastapi import APIRouter, Request

from lib.clients import AdminPB


messages_router = APIRouter(prefix="/messages", tags=["messages"], dependencies=[])


@messages_router.get("/see")
async def see_messages(
    request: Request,
    admin_pb: AdminPB,
):
    return {"message": "Hello, World!"}
