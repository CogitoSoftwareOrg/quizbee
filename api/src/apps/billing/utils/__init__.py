import logging
from datetime import datetime
from datetime import timezone

from lib.clients import AdminPB


PB_DT_FMT = "%Y-%m-%d %H:%M:%SZ"


def _ts_to_pb(ts: int | float | None) -> str | None:
    if not ts:
        return None
    # Преобразуем в UTC и даём "YYYY-MM-DD HH:MM:SSZ"
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime(PB_DT_FMT)


async def stripe_subscription_to_pb(
    admin_pb: AdminPB, sub: dict, user_id: str | None = None
):
    stripe_subscription_id = sub["id"]
    status = sub.get("status")
    items = sub.get("items", {}).get("data", [])
    price = items[0]["price"] if items else {}
    price_id = price.get("id")
    product_id = price.get("product")

    cp_start_raw = sub.get("current_period_start") or items[0].get(
        "current_period_start"
    )
    cp_end_raw = sub.get("current_period_end") or items[0].get("current_period_end")

    record = {
        "stripeSubscription": stripe_subscription_id,
        "stripeCustomer": sub.get("customer"),
        "status": status,
        "stripeProduct": product_id,
        "stripePrice": price_id,
        "currentPeriodStart": _ts_to_pb(cp_start_raw),
        "currentPeriodEnd": _ts_to_pb(cp_end_raw),
        "cancelAtPeriodEnd": bool(sub.get("cancel_at_period_end")),
        "metadata": sub.get("metadata") or {},
    }

    existing = await admin_pb.collection("subscriptions").get_first(
        options={
            "params": {
                "filter": f"user = '{user_id}' || stripeSubscription = '{stripe_subscription_id}'"
            }
        }
    )
    await admin_pb.collection("subscriptions").update(existing.get("id", ""), record)
    return existing.get("id", "")
