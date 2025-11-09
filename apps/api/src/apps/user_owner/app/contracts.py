from dataclasses import dataclass
from typing import Protocol

from ..domain.models import Tariff


@dataclass(slots=True, kw_only=True)
class Principal:
    id: str
    remaining: int
    used: int
    limit: int
    tariff: Tariff


class AuthUserApp(Protocol):
    async def validate(self, token: str) -> Principal: ...

    async def charge(self, user_id: str, cost: int) -> None: ...
