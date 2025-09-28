import logging
from fastapi import APIRouter, Request
from starlette.responses import JSONResponse

billing_router = APIRouter(prefix="/billing", tags=["billing"])


@billing_router.post("/stripe/webhook", status_code=200)
async def stripe_webhook(request: Request):
    data = await request.json()
    logging.info(f"Stripe webhook received: {data}")
    return JSONResponse(content=data)
