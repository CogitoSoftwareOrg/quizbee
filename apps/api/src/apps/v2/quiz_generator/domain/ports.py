from typing import Protocol

from .models import QuizAttempt, Quiz


class QuizRepository(Protocol):
    async def create_attempt(self, quiz_id: str, user_id: str) -> QuizAttempt: ...


class QuizIndexer(Protocol):
    async def index(self, quiz: Quiz) -> None: ...

    async def search(self, user_id: str, query: str, limit: int) -> list[Quiz]: ...
