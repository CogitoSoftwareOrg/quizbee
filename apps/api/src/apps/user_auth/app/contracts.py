from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True, kw_only=True)
class Principal:
    id: str
    remaining: int
    used: int
    limit: int


class AuthUserApp(Protocol):
    async def validate(self, token: str) -> Principal: ...

    async def charge(self, user_id: str, cost: int) -> None: ...
