"""
Контрактные тесты для портов домена.

Эти тесты проверяют, что реализации портов соответствуют контракту интерфейса.
Любая реализация AttemptRepository или Explainer должна проходить эти тесты.
"""

import pytest
from abc import ABC, abstractmethod
from typing import AsyncIterable
from unittest.mock import AsyncMock

from ..domain.models import Attempt
from ..domain.ports import AttemptRepository, Explainer
from ..domain.refs import (
    MessageMetadata,
    QuizRef,
    QuizItemRef,
    MessageRef,
    MessageRole,
    MessageStatus,
)


class AttemptRepositoryContract(ABC):
    """Абстрактный класс для тестирования контракта AttemptRepository"""

    @abstractmethod
    def get_repository(self) -> AttemptRepository:
        """Должен возвращать экземпляр AttemptRepository для тестирования"""
        pass

    @pytest.fixture
    def repository(self, get_repository):
        return get_repository()

    @pytest.fixture
    def sample_attempt(self):
        return Attempt(
            id="test_attempt_123",
            user_id="test_user_123",
            quiz=QuizRef(
                id="test_quiz_123",
                query="Test question",
                items=[
                    QuizItemRef(
                        id="test_item_1",
                        question="What is test?",
                        answers=["A test", "Not a test"],
                        choice=None,
                    )
                ],
                material_content="Test content",
            ),
            choices=[],
        )

    @pytest.mark.asyncio
    async def test_get_returns_attempt(self, repository, sample_attempt):
        """Контракт: get должен возвращать Attempt объект"""
        # Arrange - реализация должна настроить возврат sample_attempt

        # Act
        result = await repository.get("test_attempt_123")

        # Assert
        assert isinstance(result, Attempt)
        assert result.id == "test_attempt_123"
        assert result.user_id == "test_user_123"
        assert isinstance(result.quiz, QuizRef)

    @pytest.mark.asyncio
    async def test_save_accepts_attempt(self, repository, sample_attempt):
        """Контракт: save должен принимать Attempt объект и не выбрасывать исключения"""
        # Act & Assert - не должно быть исключений
        await repository.save(sample_attempt)

    @pytest.mark.asyncio
    async def test_get_nonexistent_raises_exception(self, repository):
        """Контракт: get несуществующего attempt должен вызвать исключение"""
        with pytest.raises(Exception):  # Любое исключение приемлемо
            await repository.get("nonexistent_attempt")


class ExplainerContract(ABC):
    """Абстрактный класс для тестирования контракта Explainer"""

    @abstractmethod
    def get_explainer(self) -> Explainer:
        """Должен возвращать экземпляр Explainer для тестирования"""
        pass

    @pytest.fixture
    def explainer(self, get_explainer):
        return get_explainer()

    @pytest.fixture
    def sample_attempt(self):
        return Attempt(
            id="test_attempt_123",
            user_id="test_user_123",
            quiz=QuizRef(
                id="test_quiz_123",
                query="Test question",
                items=[
                    QuizItemRef(
                        id="test_item_1",
                        question="What is test?",
                        answers=["A test", "Not a test"],
                        choice=None,
                    )
                ],
                material_content="Test content",
            ),
            choices=[],
        )

    @pytest.fixture
    def sample_item(self, sample_attempt):
        return sample_attempt.quiz.items[0]

    @pytest.fixture
    def sample_ai_message(self):
        return MessageRef(
            id="ai_msg_123",
            attempt_id="test_attempt_123",
            metadata=MessageMetadata(),
            content="AI response content",
            role=MessageRole.AI,
            status=MessageStatus.FINAL,
        )

    @pytest.mark.asyncio
    async def test_explain_returns_async_iterable(
        self, explainer, sample_attempt, sample_item, sample_ai_message
    ):
        """Контракт: explain должен возвращать AsyncIterable[MessageRef]"""
        # Act
        result = explainer.explain(
            query="Explain this",
            attempt=sample_attempt,
            item=sample_item,
            ai_msg=sample_ai_message,
            cache_key="test_cache_key",
        )

        # Assert
        assert hasattr(result, "__aiter__")  # Это AsyncIterable

    @pytest.mark.asyncio
    async def test_explain_yields_message_refs(
        self, explainer, sample_attempt, sample_item, sample_ai_message
    ):
        """Контракт: explain должен yield'ить MessageRef объекты"""
        # Act
        messages = []
        async for message in explainer.explain(
            query="Explain this",
            attempt=sample_attempt,
            item=sample_item,
            ai_msg=sample_ai_message,
            cache_key="test_cache_key",
        ):
            messages.append(message)

        # Assert
        assert len(messages) > 0  # Должен вернуть хотя бы одно сообщение
        for message in messages:
            assert isinstance(message, MessageRef)
            assert message.content  # Содержимое не пустое
            assert isinstance(message.role, MessageRole)
            assert isinstance(message.status, MessageStatus)


# Примеры конкретных реализаций контрактов для тестирования


class TestAttemptRepositoryContractImpl(AttemptRepositoryContract):
    """Тест конкретной реализации AttemptRepository (здесь mock для примера)"""

    def get_repository(self):
        """Возвращает mock-реализацию для тестирования контракта"""
        mock_repo = AsyncMock(spec=AttemptRepository)

        # Настройка mock для прохождения тестов
        sample_attempt = Attempt(
            id="test_attempt_123",
            user_id="test_user_123",
            quiz=QuizRef(
                id="test_quiz_123",
                query="Test question",
                items=[
                    QuizItemRef(
                        id="test_item_1",
                        question="What is test?",
                        answers=["A test", "Not a test"],
                        choice=None,
                    )
                ],
                material_content="Test content",
            ),
            choices=[],
        )

        mock_repo.get.return_value = sample_attempt
        mock_repo.save.return_value = None

        # Настройка для теста несуществующего attempt
        mock_repo.get.side_effect = lambda attempt_id: (
            sample_attempt
            if attempt_id == "test_attempt_123"
            else Exception("Attempt not found")
        )

        return mock_repo


class TestExplainerContractImpl(ExplainerContract):
    """Тест конкретной реализации Explainer (здесь mock для примера)"""

    def get_explainer(self):
        """Возвращает mock-реализацию для тестирования контракта"""
        mock_explainer = AsyncMock(spec=Explainer)

        async def mock_explain_generator(*args, **kwargs):
            yield MessageRef(
                id="msg_1",
                attempt_id="test_attempt_123",
                metadata=MessageMetadata(),
                content="Explanation content",
                role=MessageRole.AI,
                status=MessageStatus.STREAMING,
            )
            yield MessageRef(
                id="msg_2",
                attempt_id="test_attempt_123",
                metadata=MessageMetadata(),
                content="Final explanation",
                role=MessageRole.AI,
                status=MessageStatus.FINAL,
            )

        mock_explainer.explain.return_value = mock_explain_generator()
        return mock_explainer
