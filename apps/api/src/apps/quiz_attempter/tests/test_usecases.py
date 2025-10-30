import pytest
from unittest.mock import AsyncMock, MagicMock
from dataclasses import dataclass

from ..app.usecases import QuizAttempterAppImpl
from ..app.contracts import FinalizeCmd, AskExplainerCmd
from ..domain.models import Attempt
from ..domain.refs import (
    QuizRef,
    MessageRef,
    QuizItemRef,
    Choice,
    MessageRole,
    MessageStatus,
    MessageMetadata,
)
from ..domain.errors import (
    NotAttemptOwnerError,
    AttemptAlreadyFinalizedError,
)


# Fixtures для создания тестовых данных
@pytest.fixture
def mock_attempt_repository():
    return AsyncMock()


@pytest.fixture
def mock_user_auth():
    return AsyncMock()


@pytest.fixture
def mock_explainer():
    return AsyncMock()


@pytest.fixture
def sample_quiz_ref():
    return QuizRef(
        id="quiz_123",
        query="Sample question",
        items=[
            QuizItemRef(
                id="item_1",
                question="What is Python?",
                answers=["A programming language", "A snake"],
                choice=None,
            )
        ],
        material_content="Sample material content",
    )


@pytest.fixture
def sample_attempt(sample_quiz_ref):
    return Attempt(
        id="attempt_123",
        user_id="user_123",
        quiz=sample_quiz_ref,
        choices=[Choice(idx=0, correct=True)],
    )


@pytest.fixture
def quiz_attempter_app(mock_attempt_repository, mock_user_auth, mock_explainer):
    return QuizAttempterAppImpl(
        attempt_repository=mock_attempt_repository,
        user_auth=mock_user_auth,
        explainer=mock_explainer,
    )


class TestQuizAttempterApp:
    """Unit-тесты для usecase QuizAttempterAppImpl"""

    @pytest.mark.asyncio
    async def test_finalize_success(
        self,
        quiz_attempter_app,
        mock_attempt_repository,
        mock_user_auth,
        sample_attempt,
    ):
        """Тест успешной финализации попытки"""
        # Arrange
        cmd = FinalizeCmd(
            quiz_id="quiz_123",
            cache_key="cache_123",
            attempt_id="attempt_123",
            token="valid_token",
        )

        mock_attempt_repository.get.return_value = sample_attempt
        mock_user_auth.validate.return_value = MagicMock(id="user_123")

        # Act
        await quiz_attempter_app.finalize(cmd)

        # Assert
        mock_attempt_repository.get.assert_called_once_with("attempt_123")
        mock_user_auth.validate.assert_called_once_with("valid_token")

    @pytest.mark.asyncio
    async def test_finalize_not_owner(
        self,
        quiz_attempter_app,
        mock_attempt_repository,
        mock_user_auth,
        sample_attempt,
    ):
        """Тест финализации попытки не владельцем"""
        # Arrange
        cmd = FinalizeCmd(
            quiz_id="quiz_123",
            cache_key="cache_123",
            attempt_id="attempt_123",
            token="valid_token",
        )

        mock_attempt_repository.get.return_value = sample_attempt
        mock_user_auth.validate.return_value = MagicMock(
            id="different_user"
        )  # другой пользователь

        # Act & Assert
        with pytest.raises(NotAttemptOwnerError):
            await quiz_attempter_app.finalize(cmd)

    @pytest.mark.asyncio
    async def test_finalize_already_finalized(
        self,
        quiz_attempter_app,
        mock_attempt_repository,
        mock_user_auth,
        sample_attempt,
    ):
        """Тест финализации уже завершенной попытки"""
        # Arrange
        sample_attempt.feedback = MagicMock()  # имитируем завершенную попытку
        cmd = FinalizeCmd(
            quiz_id="quiz_123",
            cache_key="cache_123",
            attempt_id="attempt_123",
            token="valid_token",
        )

        mock_attempt_repository.get.return_value = sample_attempt
        mock_user_auth.validate.return_value = MagicMock(id="user_123")

        # Act & Assert
        with pytest.raises(AttemptAlreadyFinalizedError):
            await quiz_attempter_app.finalize(cmd)

    @pytest.mark.asyncio
    async def test_ask_explainer_success(
        self,
        quiz_attempter_app,
        mock_attempt_repository,
        mock_user_auth,
        mock_explainer,
        sample_attempt,
    ):
        """Тест успешного запроса объяснения"""
        # Arrange
        cmd = AskExplainerCmd(
            query="Explain this",
            item_id="item_1",
            attempt_id="attempt_123",
            token="valid_token",
        )

        mock_attempt_repository.get.return_value = sample_attempt
        mock_user_auth.validate.return_value = MagicMock(id="user_123")

        # Мокаем streaming ответ от explainer
        async def mock_explain_generator():
            yield MessageRef(
                id="msg_1",
                attempt_id="attempt_123",
                metadata=MessageMetadata(),
                content="Explanation part 1",
                role=MessageRole.AI,
                status=MessageStatus.STREAMING,
            )
            yield MessageRef(
                id="msg_2",
                attempt_id="attempt_123",
                metadata=MessageMetadata(),
                content="Explanation part 2",
                role=MessageRole.AI,
                status=MessageStatus.FINAL,
            )

        mock_explainer.explain.return_value = mock_explain_generator()

        # Act
        results = []
        async for result in quiz_attempter_app.ask_explainer(cmd):
            results.append(result)

        # Assert
        assert len(results) == 2
        assert results[0].text == "Explanation part 1"
        assert results[0].status == "chunk"
        assert results[1].text == "Explanation part 2"
        assert results[1].status == "done"

        mock_explainer.explain.assert_called_once()
        call_args = mock_explainer.explain.call_args[0]
        assert call_args[0] == "Explain this"  # query
        assert call_args[1] == sample_attempt  # attempt
        assert call_args[2].id == "item_1"  # item

    @pytest.mark.asyncio
    async def test_ask_explainer_invalid_item(
        self,
        quiz_attempter_app,
        mock_attempt_repository,
        mock_user_auth,
        sample_attempt,
    ):
        """Тест запроса объяснения для несуществующего item"""
        # Arrange
        cmd = AskExplainerCmd(
            query="Explain this",
            item_id="nonexistent_item",
            attempt_id="attempt_123",
            token="valid_token",
        )

        mock_attempt_repository.get.return_value = sample_attempt
        mock_user_auth.validate.return_value = MagicMock(id="user_123")

        # Act & Assert
        with pytest.raises(ValueError, match="Item nonexistent_item not found"):
            async for _ in quiz_attempter_app.ask_explainer(cmd):
                pass
