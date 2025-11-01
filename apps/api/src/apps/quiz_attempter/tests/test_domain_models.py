import pytest

from ..domain.models import Attempt, Feedback
from ..domain.refs import QuizRef, QuizItemRef, Choice


class TestFeedback:
    """Тесты для value object Feedback"""

    def test_feedback_creation(self):
        """Тест создания объекта Feedback"""
        feedback = Feedback(
            overview="Good job!",
            problem_topics=["topic1", "topic2"],
            uncovered_topics=["topic3"],
        )

        assert feedback.overview == "Good job!"
        assert feedback.problem_topics == ["topic1", "topic2"]
        assert feedback.uncovered_topics == ["topic3"]

    def test_feedback_defaults(self):
        """Тест значений по умолчанию"""
        feedback = Feedback()

        assert feedback.overview == ""
        assert feedback.problem_topics == []
        assert feedback.uncovered_topics == []


class TestAttempt:
    """Тесты для entity Attempt"""

    @pytest.fixture
    def sample_quiz_ref(self):
        return QuizRef(
            id="quiz_123",
            query="Sample question",
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
            material_content="Sample material content",
        )

    def test_attempt_creation(self, sample_quiz_ref):
        """Тест создания Attempt через create method"""
        attempt = Attempt.create(quiz=sample_quiz_ref, user_id="user_123")

        assert attempt.user_id == "user_123"
        assert attempt.quiz == sample_quiz_ref
        assert attempt.message_history == []
        assert attempt.feedback is None
        assert attempt.choices == []

    def test_attempt_custom_creation(self, sample_quiz_ref):
        """Тест создания Attempt с кастомными значениями"""
        attempt = Attempt(
            user_id="user_123",
            quiz=sample_quiz_ref,
            choices=[Choice(idx=0, correct=True)],
            feedback=Feedback(overview="Good!"),
        )

        assert attempt.user_id == "user_123"
        assert attempt.choices[0].correct is True
        assert attempt.feedback and attempt.feedback.overview == "Good!"

    def test_get_item_success(self, sample_quiz_ref):
        """Тест успешного получения item по id"""
        attempt = Attempt.create(quiz=sample_quiz_ref, user_id="user_123")

        item = attempt.get_item("item_1")
        assert item.id == "item_1"
        assert item.question == "What is Python?"

    def test_get_item_not_found(self, sample_quiz_ref):
        """Тест получения несуществующего item"""
        attempt = Attempt.create(quiz=sample_quiz_ref, user_id="user_123")

        with pytest.raises(ValueError, match="Item nonexistent not found"):
            attempt.get_item("nonexistent")

    def test_get_item_with_choice(self, sample_quiz_ref):
        """Тест получения item с выбором пользователя"""
        attempt = Attempt.create(quiz=sample_quiz_ref, user_id="user_123")

        item = attempt.get_item("item_2")
        assert item.id == "item_2"
        assert item.choice and item.choice.idx == 0
        assert item.choice.correct is True


class TestChoice:
    """Тесты для value object Choice"""

    def test_choice_creation(self):
        """Тест создания Choice"""
        choice = Choice(idx=1, correct=False)

        assert choice.idx == 1
        assert choice.correct is False

    def test_choice_equality(self):
        """Тест равенства Choice объектов"""
        choice1 = Choice(idx=0, correct=True)
        choice2 = Choice(idx=0, correct=True)
        choice3 = Choice(idx=1, correct=True)

        assert choice1 == choice2
        assert choice1 != choice3
