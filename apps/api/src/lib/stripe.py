from typing import Annotated
from fastapi import Depends, FastAPI, Request
import stripe

from src.lib.settings import settings

stripe.api_key = settings.stripe_api_key


# def set_stripe(app: FastAPI):
#     import stripe
#     stripe.api_key = settings.stripe_api_key


# def get_stripe(request: Request) -> stripe.StripeClient:
#     return request.app.state.stripe


# StripeDeps = Annotated[stripe.StripeClient, Depends(get_stripe)]
