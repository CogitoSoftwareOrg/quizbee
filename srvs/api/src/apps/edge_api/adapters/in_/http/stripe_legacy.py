from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from fastapi import HTTPException
from pocketbase import PocketBase
from pocketbase.models.dtos import Record
import logging

from src.lib.settings import settings
from src.lib.stripe import stripe_client

logger = logging.getLogger(__name__)

STRIPE_LOOKUPS = [
    "plus_early_monthly",
    "plus_early_yearly",
    "pro_early_monthly",
    "pro_early_yearly",
]

PB_DT_FMT = "%Y-%m-%d %H:%M:%S.%fZ"


@dataclass(slots=True, kw_only=True)
class Limits:
    quizItemsLimit: int
    storageLimit: int


@dataclass(slots=True, kw_only=True)
class Price:
    id: str
    lookup: str
    tariff: str
    limits: Limits


PRICES_MAP_BY_ID: dict[str, Price] = {}
PRICES_MAP_BY_LOOKUP: dict[str, Price] = {}
prices = stripe_client.Price.list(lookup_keys=STRIPE_LOOKUPS).data
logger.info(f"Loaded {len(prices)} prices from Stripe")
for price in prices:
    if not price.lookup_key:
        logger.warning(f"Price {price.id} has no lookup_key")
        continue
    logger.info(f"Processing price: {price.lookup_key} (ID: {price.id})")
    tariff = price.lookup_key.split("_")[0]
    price_obj = Price(
        id=price.id,
        lookup=price.lookup_key,
        tariff=tariff,
        limits=Limits(
            quizItemsLimit=1000 if tariff == "plus" else 2000,
            storageLimit=(
                10 * 1024 * 1024 * 1024
                if tariff == "plus"
                else 100 * 1024 * 1024 * 1024
            ),
        ),
    )
    PRICES_MAP_BY_ID[price.id] = price_obj
    PRICES_MAP_BY_LOOKUP[price.lookup_key] = price_obj

logger.info(f"Final PRICES_MAP_BY_LOOKUP keys: {list(PRICES_MAP_BY_LOOKUP.keys())}")

# Backward compatibility
PRICES_MAP = PRICES_MAP_BY_LOOKUP


def _ts_to_pb(ts: int | float | None) -> str | None:
    if not ts:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime(PB_DT_FMT)


async def stripe_subscription_to_pb(
    admin_pb: PocketBase, sub: dict, user_id: str | None = None
):
    stripe_subscription_id = sub["id"]
    status = sub.get("status")
    items = sub.get("items", {}).get("data", [])
    price = items[0]["price"] if items else {}
    price_id = price.get("id", "")
    product_id = price.get("product", "")
    interval = price.get("recurring", {}).get("interval")

    cp_start_raw = sub.get("current_period_start") or items[0].get(
        "current_period_start"
    )
    cp_end_raw = sub.get("current_period_end") or items[0].get("current_period_end")

    existing = await admin_pb.collection("subscriptions").get_first(
        options={
            "params": {
                "filter": f"user = '{user_id}' || stripeSubscription = '{stripe_subscription_id}'"
            }
        }
    )

    price_obj = PRICES_MAP_BY_ID.get(price_id)
    if not price_obj:
        raise Exception(f"Stripe price not found for {price_id}")

    tariff = price_obj.tariff
    limits = price_obj.limits

    record: dict = {
        "stripeSubscription": stripe_subscription_id,
        "stripeCustomer": sub.get("customer"),
        "status": status,
        "stripeProduct": product_id,
        "stripePrice": price_id,
        "tariff": tariff,
        "stripeInterval": interval,
        "currentPeriodStart": _ts_to_pb(cp_start_raw),
        "currentPeriodEnd": _ts_to_pb(cp_end_raw),
        "cancelAtPeriodEnd": bool(sub.get("cancel_at_period_end")),
        "metadata": sub.get("metadata") or {},
        "quizItemsLimit": limits.quizItemsLimit,
        "storageLimit": limits.storageLimit,
    }

    await admin_pb.collection("subscriptions").update(existing.get("id", ""), record)
    return existing.get("id", "")


async def verify(token: str):

    pb = PocketBase(settings.pb_url)
    pb._inners.auth.set_user({"token": token, "record": {}})

    try:
        user = (
            await pb.collection("users").auth.refresh(
                {"params": {"expand": "subscriptions_via_user"}}
            )
        ).get("record", {})
        sub = user.get("expand", {}).get("subscriptions_via_user", [])[0]
        return user, sub

    except Exception:
        raise HTTPException(401, "Unauthorized")
