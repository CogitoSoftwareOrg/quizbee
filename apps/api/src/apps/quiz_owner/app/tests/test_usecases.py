"""
Unit-тесты для usecase QuizGeneratorAppImpl.

Эти тесты мокируют ВСЕ зависимости (порты), проверяя только логику usecase.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.apps.quiz_owner.app.usecases import QuizGeneratorAppImpl
from src.apps.quiz_owner.domain._in import GenerateCmd, FinalizeQuizCmd, GenMode
from src.apps.quiz_owner.domain.models import (
    Quiz,
    QuizStatus,
    QuizDifficulty,
    QuizItemStatus,
    QuizItem,
    QuizItemVariant,
)
from src.apps.quiz_owner.domain.errors import NotQuizOwnerError
from src.apps.user_owner.domain._in import Principal


@pytest.fixture
def mock_quiz_repository():
    """Mock для QuizRepository"""
    return AsyncMock()


@pytest.fixture
def mock_quiz_indexer():
    """Mock для QuizIndexer"""
    return AsyncMock()


@pytest.fixture
def mock_llm_tools():
    """Mock для LLMToolsApp"""
    return AsyncMock()


@pytest.fixture
def mock_material():
    """Mock для MaterialSearchApp"""
    return AsyncMock()


@pytest.fixture
def mock_patch_generator():
    """Mock для PatchGenerator"""
    return AsyncMock()


@pytest.fixture
def mock_finalizer():
    """Mock для QuizFinalizer"""
    return AsyncMock()


@pytest.fixture
def sample_user():
    """Sample Principal user"""
    return MagicMock(spec=Principal, id="user_123")


@pytest.fixture
def sample_quiz():
    """Sample Quiz для тестов"""
    quiz = Quiz.create(
        author_id="user_123",
        title="Python Basics",
        query="What is Python?",
        difficulty=QuizDifficulty.BEGINNER,
    )
    quiz.id = "quiz_123"
    quiz.status = QuizStatus.DRAFT
    quiz.items = [
        QuizItem(
            id="item_1",
            question="Q1",
            variants=[
                QuizItemVariant(
                    content="Answer A",
                    is_correct=True,
                    explanation="Correct",
                )
            ],
            order=0,
            status=QuizItemStatus.BLANK,
        ),
    ]
    return quiz


@pytest.fixture
def quiz_generator_app(
    mock_quiz_repository,
    mock_quiz_indexer,
    mock_llm_tools,
    mock_material,
    mock_patch_generator,
    mock_finalizer,
):
    """Создает QuizGeneratorAppImpl со всеми мокированными зависимостями"""
    return QuizGeneratorAppImpl(
        quiz_repository=mock_quiz_repository,
        quiz_indexer=mock_quiz_indexer,
        llm_tools=mock_llm_tools,
        material=mock_material,
        patch_generator=mock_patch_generator,
        finalizer=mock_finalizer,
    )


class TestQuizGeneratorApp:
    """Unit-тесты для QuizGeneratorApp"""

    @pytest.mark.asyncio
    async def test_generate_success(
        self,
        quiz_generator_app,
        mock_quiz_repository,
        mock_patch_generator,
        sample_quiz,
        sample_user,
    ):
        """Тест успешной генерации quiz items в режиме continue"""
        # Arrange
        cmd = GenerateCmd(
            cache_key="cache_123",
            quiz_id="quiz_123",
            mode=GenMode.Continue,
            user=sample_user,
        )

        mock_quiz_repository.get.return_value = sample_quiz
        mock_quiz_repository.update.return_value = None
        mock_patch_generator.generate.return_value = None

        # Act
        await quiz_generator_app.generate(cmd)

        # Assert - проверяем что методы вызваны с правильными аргументами
        mock_quiz_repository.get.assert_called_once_with("quiz_123")
        # Должны вызвать update дважды: после generate_patch и после
        assert mock_quiz_repository.update.call_count >= 1
        mock_patch_generator.generate.assert_called_once()

        # Проверяем что items были переведены в статус GENERATING
        patch_items = mock_patch_generator.generate.call_args[0][0].generating_items()
        assert len(patch_items) > 0
        assert all(item.status == QuizItemStatus.GENERATING for item in patch_items)

    @pytest.mark.asyncio
    async def test_generate_regenerate_mode(
        self,
        quiz_generator_app,
        mock_quiz_repository,
        mock_patch_generator,
        sample_quiz,
        sample_user,
    ):
        """Тест генерации в режиме regenerate - должен инкрементировать generation"""
        # Arrange
        sample_quiz.status = QuizStatus.DRAFT
        sample_quiz.generation = 0

        cmd = GenerateCmd(
            cache_key="cache_456",
            quiz_id="quiz_123",
            mode=GenMode.Regenerate,
            user=sample_user,
        )

        mock_quiz_repository.get.return_value = sample_quiz
        mock_quiz_repository.update.return_value = None
        mock_patch_generator.generate.return_value = None

        # Act
        await quiz_generator_app.generate(cmd)

        # Assert
        assert sample_quiz.generation == 1
        mock_quiz_repository.update.assert_called()

    @pytest.mark.asyncio
    async def test_generate_not_owner_error(
        self,
        quiz_generator_app,
        mock_quiz_repository,
        sample_quiz,
    ):
        """Тест что generate выбросит ошибку если пользователь не владелец"""
        # Arrange
        different_user = MagicMock(spec=Principal, id="different_user_456")

        cmd = GenerateCmd(
            cache_key="cache_123",
            quiz_id="quiz_123",
            mode=GenMode.Continue,
            user=different_user,
        )

        mock_quiz_repository.get.return_value = sample_quiz

        # Act & Assert
        with pytest.raises(NotQuizOwnerError):
            await quiz_generator_app.generate(cmd)

    @pytest.mark.asyncio
    async def test_finalize_success(
        self,
        quiz_generator_app,
        mock_quiz_repository,
        mock_finalizer,
        mock_quiz_indexer,
        sample_quiz,
        sample_user,
    ):
        """Тест успешной финализации quiz"""
        # Arrange
        sample_quiz.status = QuizStatus.CREATING
        sample_quiz.items[0].status = QuizItemStatus.FINAL

        cmd = FinalizeQuizCmd(
            cache_key="cache_123",
            quiz_id="quiz_123",
            user=sample_user,
        )

        mock_quiz_repository.get.return_value = sample_quiz
        mock_quiz_repository.update.return_value = None
        mock_finalizer.finalize.return_value = None
        mock_quiz_indexer.index.return_value = None

        # Act
        await quiz_generator_app.finalize(cmd)

        # Assert
        assert sample_quiz.status == QuizStatus.ANSWERED
        mock_quiz_repository.update.assert_called()
        mock_finalizer.finalize.assert_called_once()
        mock_quiz_indexer.index.assert_called_once()

    @pytest.mark.asyncio
    async def test_finalize_not_owner_error(
        self,
        quiz_generator_app,
        mock_quiz_repository,
        sample_quiz,
    ):
        """Тест что finalize выбросит ошибку если пользователь не владелец"""
        # Arrange
        different_user = MagicMock(spec=Principal, id="different_user_456")

        cmd = FinalizeQuizCmd(
            cache_key="cache_123",
            quiz_id="quiz_123",
            user=different_user,
        )

        mock_quiz_repository.get.return_value = sample_quiz

        # Act & Assert
        with pytest.raises(NotQuizOwnerError):
            await quiz_generator_app.finalize(cmd)

    @pytest.mark.asyncio
    async def test_finalize_items_not_final_error(
        self,
        quiz_generator_app,
        mock_quiz_repository,
        sample_quiz,
        sample_user,
    ):
        """Тест что finalize выбросит ошибку если не все items в статусе FINAL"""
        # Arrange
        sample_quiz.status = QuizStatus.CREATING
        # item остается в статусе BLANK!

        cmd = FinalizeQuizCmd(
            cache_key="cache_123",
            quiz_id="quiz_123",
            user=sample_user,
        )

        mock_quiz_repository.get.return_value = sample_quiz

        # Act & Assert
        with pytest.raises(ValueError, match="some items are not final"):
            await quiz_generator_app.finalize(cmd)
