from dataclasses import dataclass


@dataclass(slots=True, kw_only=True)
class Subscription:
    id: str
    quiz_items_limit: int
    quiz_items_usage: int


@dataclass(slots=True, kw_only=True)
class User:
    id: str
    subscription: Subscription


