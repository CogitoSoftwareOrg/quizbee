from dataclasses import dataclass
from typing import Protocol

from ..domain.models import Tariff


@dataclass(slots=True, kw_only=True)
class Principal:
    id: str
    remaining: int
    used: int
    limit: int
    storage_usage: int
    storage_limit: int
    tariff: Tariff


class AuthUserApp(Protocol):
    async def validate(self, token: str) -> Principal: ...

    async def charge(self, user_id: str, cost: int) -> None: ...

    async def update_storage(self, user_id: str, delta: int) -> None: ...
