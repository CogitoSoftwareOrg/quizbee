from dataclasses import dataclass
from enum import StrEnum


class Tariff(StrEnum):
    FREE = "free"
    PRO = "pro"
    PLUS = "plus"


@dataclass(slots=True, kw_only=True)
class Subscription:
    id: str
    quiz_items_limit: int
    quiz_items_usage: int
    tariff: Tariff


@dataclass(slots=True, kw_only=True)
class User:
    id: str
    subscription: Subscription
