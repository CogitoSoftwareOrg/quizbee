import logging
from datetime import datetime
from datetime import timezone

from pocketbase.models.dtos import Record

from lib.clients import AdminPB
from lib.config import STRIPE_TARIFS_MAP, STRIPE_MONTHLY_LIMITS_MAP


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
    admin_pb: AdminPB, sub: dict, user_id: str | None = None
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

    tariff = STRIPE_TARIFS_MAP.get(price_id) or "free"
    limits = STRIPE_MONTHLY_LIMITS_MAP.get(tariff)

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
        record.update(limits)

    await admin_pb.collection("subscriptions").update(existing.get("id", ""), record)
    return existing.get("id", "")
