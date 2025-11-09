import pytest
import pytest_asyncio

from src.apps.quiz_owner.domain.models import (
    Quiz,
    QuizItem,
    QuizItemVariant,
    QuizItemStatus,
    QuizDifficulty,
)
from src.apps.quiz_owner.domain.ports import QuizRepository
from src.apps.quiz_owner.adapters.out import PBQuizRepository


class QuizRepositoryContract:
    """
    Общий набор тестов для любого QuizRepository.
    Наследник обязан вернуть реальный репозиторий в фикстуре repository.
    """

    @pytest_asyncio.fixture
    async def repository(self) -> QuizRepository:  # type: ignore[override]
        raise NotImplementedError

    @pytest.mark.asyncio
    async def test_create_and_get(self, repository: QuizRepository):
        q = Quiz.create(
            author_id="user_123",
            title="Python Basics",
            query="What is Python?",
            difficulty=QuizDifficulty.BEGINNER,
        )
        await repository.create(q)
        got = await repository.get(q.id)
        assert isinstance(got, Quiz)
        assert got.id == q.id
        assert got.author_id == "user_123"
        assert got.title == "Python Basics"

    @pytest.mark.asyncio
    async def test_update(self, repository: QuizRepository):
        q = Quiz.create(
            author_id="u1", title="Old", query="Q", difficulty=QuizDifficulty.BEGINNER
        )
        await repository.create(q)
        q.title = "New"
        await repository.update(q)
        got = await repository.get(q.id)
        assert got.title == "New"

    @pytest.mark.asyncio
    async def test_save_item_and_list(self, repository: QuizRepository):
        q = Quiz.create(
            author_id="u2", title="T", query="Q", difficulty=QuizDifficulty.BEGINNER
        )
        await repository.create(q)

        item = QuizItem(
            id="item_1",
            question="What is a function?",
            variants=[
                QuizItemVariant(
                    content="A block of reusable code", is_correct=True, explanation=""
                ),
                QuizItemVariant(content="A variable", is_correct=False, explanation=""),
            ],
            order=0,
            status=QuizItemStatus.FINAL,
        )
        await repository.save_item(item)

    @pytest.mark.asyncio
    async def test_get_nonexistent_raises(self, repository: QuizRepository):
        with pytest.raises(Exception):
            await repository.get("nonexistent")


class TestPBQuizRepository(QuizRepositoryContract):

    @pytest_asyncio.fixture
    async def repository(self, admin_pb, http) -> QuizRepository:  # type: ignore[override]
        repo = PBQuizRepository(admin_pb=admin_pb, http=http)
        return repo
