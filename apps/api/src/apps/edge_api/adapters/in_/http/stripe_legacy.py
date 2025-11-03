from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from fastapi import HTTPException
from pocketbase import PocketBase
from pocketbase.models.dtos import Record

from src.lib.settings import settings
from src.lib.stripe import stripe_client

STRIPE_LOOKUPS = [
    "plus_early_monthly",
    "plus_early_yearly",
    "pro_early_monthly",
    "pro_early_yearly",
]


@dataclass(slots=True, kw_only=True)
class Limits:
    quizItemsLimit: int
    bytesLimit: int


@dataclass(slots=True, kw_only=True)
class Price:
    id: str
    lookup: str
    tariff: str
    limits: Limits


PRICES_MAP_BY_ID: dict[str, Price] = {}
PRICES_MAP_BY_LOOKUP: dict[str, Price] = {}
prices = stripe_client.Price.list(lookup_keys=STRIPE_LOOKUPS).data
for price in prices:
    if not price.lookup_key:
        continue
    tariff = price.lookup_key.split("_")[0]
    price_obj = Price(
        id=price.id,
        lookup=price.lookup_key,
        tariff=tariff,
        limits=Limits(
            quizItemsLimit=1000 if tariff == "plus" else 2000,
            bytesLimit=8_388_608 if tariff == "plus" else 83_886_080,  # 1GB
        ),
    )
    PRICES_MAP_BY_ID[price.id] = price_obj
    PRICES_MAP_BY_LOOKUP[price.lookup_key] = price_obj

# Backward compatibility
PRICES_MAP = PRICES_MAP_BY_LOOKUP


PB_DT_FMT = "%Y-%m-%d %H:%M:%S.%fZ"


def _ts_to_pb(ts: int | float | None) -> str | None:
    if not ts:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime(PB_DT_FMT)


def _pb_to_ts(pb_dt: str | None) -> int | None:
    if not pb_dt:
        return None
    return int(
        datetime.strptime(pb_dt, PB_DT_FMT).replace(tzinfo=timezone.utc).timestamp()
    )


def _maybe_reset_usage_on_period_change(sub: Record, new_cp_start_ts: int):
    patch = {}

    last_reset_pb = sub.get("lastUsageResetAt")
    last_reset_ts = _pb_to_ts(last_reset_pb) if last_reset_pb else None
    prev_cp_start_pb = sub.get("currentPeriodStart")
    prev_cp_start_ts = _pb_to_ts(prev_cp_start_pb) if prev_cp_start_pb else None

    need_reset = (prev_cp_start_ts is None) or (
        new_cp_start_ts and prev_cp_start_ts and new_cp_start_ts > prev_cp_start_ts
    )
    already_reset_for_new = (
        last_reset_ts is not None
        and new_cp_start_ts is not None
        and last_reset_ts >= new_cp_start_ts
    )

    if need_reset and not already_reset_for_new:
        patch["messagesUsage"] = 0
        patch["quizItemsUsage"] = 0
        patch["quizesUsage"] = 0
        patch["lastUsageResetAt"] = datetime.now(tz=timezone.utc).strftime(PB_DT_FMT)
    return patch


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

    price = PRICES_MAP_BY_ID.get(price_id)
    if not price:
        raise Exception(f"Stripe price not found for {price_id}")
    tariff = price.tariff
    limits = price.limits

    record = {
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
    }

    patch = _maybe_reset_usage_on_period_change(existing, cp_start_raw)
    record.update(patch)
    if limits:
        record.update(asdict(limits))

    await admin_pb.collection("subscriptions").update(existing.get("id", ""), record)
    return existing.get("id", "")


async def ensure_active_and_maybe_reset(admin_pb: PocketBase, sub: Record):
    allowed = {"active", "trialing", "past_due"}
    if sub.get("status") not in allowed:
        raise HTTPException(402, "Subscription inactive")
    current_period_start = _pb_to_ts(sub.get("currentPeriodStart", "")) or 0
    patch = _maybe_reset_usage_on_period_change(sub, current_period_start)

    if patch:
        await admin_pb.collection("subscriptions").update(sub.get("id", ""), patch)

    return sub


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
