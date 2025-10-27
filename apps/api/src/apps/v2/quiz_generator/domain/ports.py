from typing import Protocol

from .models import Attempt, Quiz


class AttemptRepository(Protocol):
    async def create(self, quiz_id: str, user_id: str) -> Attempt: ...


class QuizRepository(Protocol):
    async def get(self, ids: list[str]) -> list[Quiz]: ...


class UOW(Protocol):
    quizzes: QuizRepository
    attempts: AttemptRepository

    def __enter__(self) -> "UOW": ...
    def __exit__(self, exc_type, exc, tb) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...


class QuizIndexer(Protocol):
    async def index(self, quiz: Quiz) -> None: ...

    async def search(self, user_id: str, query: str, limit: int) -> list[Quiz]: ...
