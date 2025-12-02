from dataclasses import dataclass
from typing import Protocol

from src.apps.user_owner.domain._in import Principal

from .models import Quiz, QuizItem


class QuizRepository(Protocol):
    async def get(self, id: str) -> Quiz: ...

    async def create(self, quiz: Quiz) -> None: ...
    async def update(self, quiz: Quiz, fresh_generated=False) -> None: ...

    async def save_item(self, item: QuizItem) -> None: ...


class QuizClusterer(Protocol):
    async def cluster(
        self, quiz: Quiz, user: Principal, chunks_per_question: int
    ) -> tuple[list[list[float]], list[float]]: ...


class QuizIndexer(Protocol):
    async def index(self, quiz: Quiz) -> None: ...

    async def search(
        self, user_id: str, query: str, limit: int, ratio: float, threshold: float
    ) -> list[Quiz]: ...


@dataclass(slots=True)
class PatchGeneratorDto:
    quiz: Quiz
    cache_key: str
    chunks: list[str] | None = None
    item_order: int | None = None
    used_chunk_indices: list[int] | None = None


class PatchGenerator(Protocol):
    async def generate(self, dto: PatchGeneratorDto) -> None: ...


class QuizFinalizer(Protocol):
    async def finalize(self, quiz: Quiz, cache_key: str) -> None: ...
