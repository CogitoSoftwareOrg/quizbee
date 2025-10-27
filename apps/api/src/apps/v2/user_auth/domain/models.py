from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    id: str


@dataclass(frozen=True)
class Subscription:
    id: str
    quiz_items_limit: int
    quiz_items_usage: int
