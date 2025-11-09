"""
Shared fixtures for quiz_attempter tests
"""

import pytest
from unittest.mock import AsyncMock

from ..domain.models import Attempt, Feedback
from ..domain.refs import (
    QuizRef,
    QuizItemRef,
    Choice,
    MessageRef,
    MessageRole,
    MessageStatus,
    MessageMetadata,
)


@pytest.fixture
def sample_quiz_ref():
    """Фикстура для тестового QuizRef"""
    return QuizRef(
        id="test_quiz_123",
        query="What is Python?",
        items=[
            QuizItemRef(
                id="item_1",
                question="What is Python?",
                answers=["A programming language", "A snake"],
                choice=None,
            ),
            QuizItemRef(
                id="item_2",
                question="What is Java?",
                answers=["A programming language", "Coffee"],
                choice=Choice(idx=0, correct=True),
            ),
        ],
        material_content="Python is a programming language...",
    )


@pytest.fixture
def sample_attempt(sample_quiz_ref):
    """Фикстура для тестового Attempt"""
    return Attempt(
        id="test_attempt_123",
        user_id="test_user_123",
        quiz=sample_quiz_ref,
        choices=[Choice(idx=0, correct=True)],
        feedback=Feedback(overview="Good job!", problem_topics=["basics"]),
    )


@pytest.fixture
def sample_message_ref():
    """Фикстура для тестового MessageRef"""
    return MessageRef(
        id="msg_123",
        attempt_id="attempt_123",
        content="Test message",
        role=MessageRole.USER,
        status=MessageStatus.FINAL,
        metadata=MessageMetadata(),
    )


@pytest.fixture
def mock_attempt_repository():
    """Mock для AttemptRepository"""
    return AsyncMock()


@pytest.fixture
def mock_explainer():
    """Mock для Explainer"""
    return AsyncMock()


@pytest.fixture
def mock_user_auth():
    """Mock для AuthUserApp"""
    return AsyncMock()
