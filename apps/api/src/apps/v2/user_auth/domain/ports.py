from typing import Protocol, Any


class GuardUser(Protocol):
    async def __call__(self, request: Any) -> Any: ...
