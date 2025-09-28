import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from starlette.responses import JSONResponse

from apps.auth import auth_user, User
from lib.clients import AdminPB, stripe_client
from lib.settings import settings

from .utils import stripe_subscription_to_pb
from .middleware import load_subscription, Subscription

billing_router = APIRouter(prefix="/billing", tags=["billing"])

stripe_prices_map = {
    "plus_monthly": "price_1SCFmCPuRQMxFFQtHOEmHUWv",
    "pro_monthly": "price_1SCG2hPuRQMxFFQtaYLDDgDp",
    "plus_yearly": "price_1SCFnmPuRQMxFFQtwZF7VUHz",
    "pro_yearly": "price_1SCG4pPuRQMxFFQtMZ0bhmYW",
}


@billing_router.post("/stripe/webhook", status_code=200)
async def stripe_webhook(request: Request, admin_pb: AdminPB):
    # Verify the signature
    raw = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe_client.Webhook.construct_event(
            payload=raw,
            sig_header=sig_header,
            secret=settings.stripe_webhook_secret,
        )
    except (
        stripe_client.error.SignatureVerificationError  # pyright: ignore[reportAttributeAccessIssue]
    ) as e:
        raise HTTPException(status_code=400, detail=f"Invalid signature: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook error: {str(e)}")

    event_id = event.id
    data = event.data

    # Check if the event has already been processed
    try:
        ev = await admin_pb.collection("stripeEvents").get_first(
            options={"params": {"filter": f"stripe = '{event_id}'"}}
        )
        return JSONResponse(content=f"Already processed: {event_id}")
    except Exception as e:
        await admin_pb.collection("stripeEvents").create(
            {"stripe": event_id, "type": event.type}
        )

    # Handle the event
    obj = data.object

    if event.type == "checkout.session.completed":
        user_id = (obj.get("metadata") or {}).get("user_id") or obj.get(
            "client_reference_id"
        )
        subscription_id = obj.get("subscription")
        if subscription_id:
            sub = stripe_client.Subscription.retrieve(
                subscription_id, expand=["items.data.price"]
            )
            await stripe_subscription_to_pb(admin_pb, sub, user_id)

    elif event.type in (
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
    ):
        sub = obj
        if sub.get("items", {}).get("data") and "price" not in sub["items"]["data"][0]:
            sub = stripe_client.Subscription.retrieve(
                sub["id"], expand=["items.data.price"]
            )
        await stripe_subscription_to_pb(admin_pb, sub)
    elif event.type in ("invoice.payment_succeeded", "invoice.payment_failed"):
        sub_id = obj.get("subscription")
        if sub_id:
            sub = stripe_client.Subscription.retrieve(
                sub_id, expand=["items.data.price"]
            )
            await stripe_subscription_to_pb(admin_pb, sub)


class CreateStripeCheckoutDto(BaseModel):
    price: str
    return_url: str = ""
    idempotency_key: str | None = None


@billing_router.post(
    "/stripe/checkout",
    dependencies=[Depends(auth_user), Depends(load_subscription)],
)
async def create_stripe_checkout(
    dto: CreateStripeCheckoutDto,
    user: User,
    subscription: Subscription,
):
    sub_status = subscription.get("status")
    cpe = subscription.get("currentPeriodEnd")
    stripeCustomer = subscription.get("stripeCustomer")
    logging.info(
        f"Sub status: {sub_status}, CPE: {cpe}, Stripe customer: {stripeCustomer}"
    )
    if sub_status in {"active", "trialing", "past_due"} and cpe and stripeCustomer:
        portal = stripe_client.billing_portal.Session.create(
            customer=stripeCustomer,
            return_url=f"{settings.app_url}{dto.return_url}",
        )
        return JSONResponse(content={"url": portal.url})

    price_id = stripe_prices_map.get(dto.price)
    if not price_id:
        raise HTTPException(status_code=400, detail="Invalid price label")

    kwargs = dict(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{settings.app_url}{dto.return_url}?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.app_url}{dto.return_url}",
        client_reference_id=user.get("id"),
        metadata={"user_id": user.get("id")},
        allow_promotion_codes=True,
        billing_address_collection="auto",
        payment_method_collection="if_required",
        # automatic_tax={"enabled": True},
    )

    stripeCustomer = subscription.get("stripeCustomer")
    if stripeCustomer:
        kwargs["customer"] = stripeCustomer
    else:
        kwargs["customer_email"] = user.get("email")

    try:
        # extra = {}
        # if idempotency_key:
        #     extra["idempotency_key"] = idempotency_key
        session = stripe_client.checkout.Session.create(
            **kwargs,  # pyright: ignore[reportArgumentType]
            # **extra,
        )
    except Exception as e:
        raise HTTPException(400, f"Stripe error: {e}")
    return JSONResponse(content={"url": session.url})


class CreateBillingPortalSessionDto(BaseModel):
    return_url: str = ""


@billing_router.post(
    "/portal",
    status_code=200,
    dependencies=[Depends(auth_user), Depends(load_subscription)],
)
async def create_billing_portal_session(
    user: User,
    subscription: Subscription,
    dto: CreateBillingPortalSessionDto,
):
    customer = subscription.get("stripeCustomer")
    if not customer:
        raise HTTPException(400, "No Stripe customer for this user")

    try:
        portal = stripe_client.billing_portal.Session.create(
            customer=customer,
            return_url=f"{settings.app_url}{dto.return_url}",
        )
    except Exception as e:
        raise HTTPException(400, f"Stripe error: {e}")

    return JSONResponse(content={"url": portal.url})
