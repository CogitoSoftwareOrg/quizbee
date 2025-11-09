"""
Unittesty для domain модели Quiz.

Эти тесты проверяют только логику domain layer, без зависимостей от портов.
"""

import pytest

from src.apps.quiz_owner.domain.models import (
    Quiz,
    QuizItem,
    QuizItemVariant,
    QuizStatus,
    QuizItemStatus,
    QuizDifficulty,
    QuizGenConfig,
)


class TestQuiz:
    """Unittesty для aggregate Quiz"""

    @pytest.fixture
    def sample_quiz(self) -> Quiz:
        """Создает базовый Quiz для тестов"""
        return Quiz.create(
            author_id="user_123",
            title="Python Basics",
            query="What is Python?",
            difficulty=QuizDifficulty.BEGINNER,
        )

    def test_quiz_creation(self, sample_quiz):
        """Тест создания Quiz через factory method"""
        assert sample_quiz.author_id == "user_123"
        assert sample_quiz.title == "Python Basics"
        assert sample_quiz.query == "What is Python?"
        assert sample_quiz.difficulty == QuizDifficulty.BEGINNER
        assert sample_quiz.status == QuizStatus.DRAFT
        assert sample_quiz.generation == 0
        assert len(sample_quiz.items) == 0

    def test_quiz_to_preparing_from_draft(self, sample_quiz):
        """Тест перехода Quiz из DRAFT в PREPARING"""
        # Act
        sample_quiz.to_preparing()

        # Assert
        assert sample_quiz.status == QuizStatus.PREPARING

    def test_quiz_to_preparing_fails_if_not_draft(self, sample_quiz):
        """Тест что to_preparing выбросит ошибку если статус не DRAFT"""
        # Arrange
        sample_quiz.status = QuizStatus.CREATING

        # Act & Assert
        with pytest.raises(ValueError, match="Quiz is not in draft status"):
            sample_quiz.to_preparing()

    def test_quiz_to_creating_from_preparing(self, sample_quiz):
        """Тест перехода Quiz из PREPARING в CREATING"""
        # Arrange
        sample_quiz.status = QuizStatus.PREPARING

        # Act
        sample_quiz.to_creating()

        # Assert
        assert sample_quiz.status == QuizStatus.CREATING

    def test_quiz_to_answered_success(self, sample_quiz):
        """Тест перехода Quiz в ANSWERED когда все items FINAL"""
        # Arrange
        sample_quiz.status = QuizStatus.CREATING
        sample_quiz.items = [
            QuizItem(
                id="item_1",
                question="Question 1",
                variants=[
                    QuizItemVariant(
                        content="Answer A", is_correct=True, explanation="Yes"
                    )
                ],
                order=0,
                status=QuizItemStatus.FINAL,
            ),
            QuizItem(
                id="item_2",
                question="Question 2",
                variants=[
                    QuizItemVariant(
                        content="Answer B", is_correct=False, explanation="No"
                    )
                ],
                order=1,
                status=QuizItemStatus.FINAL,
            ),
        ]

        # Act
        sample_quiz.to_answered()

        # Assert
        assert sample_quiz.status == QuizStatus.ANSWERED

    def test_quiz_to_answered_fails_if_items_not_final(self, sample_quiz):
        """Тест что to_answered выбросит ошибку если не все items FINAL"""
        # Arrange
        sample_quiz.status = QuizStatus.CREATING
        sample_quiz.items = [
            QuizItem(
                id="item_1",
                question="Question 1",
                variants=[],
                order=0,
                status=QuizItemStatus.BLANK,  # Не FINAL!
            ),
        ]

        # Act & Assert
        with pytest.raises(ValueError, match="some items are not final"):
            sample_quiz.to_answered()

    def test_quiz_to_final(self, sample_quiz):
        """Тест перехода Quiz в FINAL из ANSWERED"""
        # Arrange
        sample_quiz.status = QuizStatus.ANSWERED

        # Act
        sample_quiz.to_final()

        # Assert
        assert sample_quiz.status == QuizStatus.FINAL

    def test_quiz_set_material_content(self, sample_quiz):
        """Тест установки content материала и флага"""
        # Act
        sample_quiz.request_build_material_content()
        assert sample_quiz.need_build_material_content is True

        sample_quiz.set_material_content("Material content here")

        # Assert
        assert sample_quiz.material_content == "Material content here"
        assert sample_quiz.need_build_material_content is False

    def test_quiz_add_negative_questions(self, sample_quiz):
        """Тест добавления negative questions для избегания повторений"""
        # Act
        sample_quiz.add_negative_questions(["Bad question 1", "Bad question 2"])

        # Assert
        assert len(sample_quiz.gen_config.negative_questions) == 2
        assert "Bad question 1" in sample_quiz.gen_config.negative_questions

    def test_quiz_increment_generation(self, sample_quiz):
        """Тест инкремента generation и regenerate items"""
        # Arrange
        sample_quiz.items = [
            QuizItem(
                id="item_1",
                question="Q1",
                variants=[],
                order=0,
                status=QuizItemStatus.FINAL,
            ),
            QuizItem(
                id="item_2",
                question="Q2",
                variants=[],
                order=1,
                status=QuizItemStatus.GENERATED,
            ),
        ]

        # Act
        sample_quiz.increment_generation()

        # Assert
        assert sample_quiz.generation == 1
        assert sample_quiz.items[0].status == QuizItemStatus.FINAL
        assert sample_quiz.items[1].status == QuizItemStatus.BLANK

    def test_quiz_generate_patch(self, sample_quiz):
        """Тест генерации patch (PATCH_LIMIT items)"""
        # Arrange
        sample_quiz.items = [
            QuizItem(
                id=f"item_{i}",
                question=f"Q{i}",
                variants=[],
                order=i,
                status=QuizItemStatus.BLANK,
            )
            for i in range(10)
        ]

        # Act
        patch = sample_quiz.generate_patch()

        # Assert
        # PATCH_LIMIT = 5 (из constants)
        assert len(patch) == 5
        # Все items в patch должны быть в статусе GENERATING
        assert all(item.status == QuizItemStatus.GENERATING for item in patch)
        # Остальные items должны остаться BLANK
        remaining = [item for item in sample_quiz.items if item not in patch]
        assert all(item.status == QuizItemStatus.BLANK for item in remaining)

    def test_quiz_get_final_items(self, sample_quiz):
        """Тест получения всех FINAL items"""
        # Arrange
        sample_quiz.items = [
            QuizItem(
                id="item_1",
                question="Q1",
                variants=[],
                order=0,
                status=QuizItemStatus.FINAL,
            ),
            QuizItem(
                id="item_2",
                question="Q2",
                variants=[],
                order=1,
                status=QuizItemStatus.GENERATING,
            ),
            QuizItem(
                id="item_3",
                question="Q3",
                variants=[],
                order=2,
                status=QuizItemStatus.FINAL,
            ),
        ]

        # Act
        final_items = sample_quiz.get_final_items()

        # Assert
        assert len(final_items) == 2
        assert all(item.status == QuizItemStatus.FINAL for item in final_items)


class TestQuizItem:
    """Unittesty для QuizItem"""

    @pytest.fixture
    def blank_item(self):
        """Создает item в статусе BLANK"""
        return QuizItem(
            id="item_1",
            question="What is X?",
            variants=[
                QuizItemVariant(content="Answer", is_correct=True, explanation="X")
            ],
            order=0,
            status=QuizItemStatus.BLANK,
        )

    def test_item_to_generating(self, blank_item):
        """Тест перехода item из BLANK в GENERATING"""
        # Act
        blank_item.to_generating()

        # Assert
        assert blank_item.status == QuizItemStatus.GENERATING

    def test_item_to_generating_fails_if_not_blank(self, blank_item):
        """Тест что to_generating выбросит ошибку если не BLANK"""
        # Arrange
        blank_item.status = QuizItemStatus.GENERATED

        # Act & Assert
        with pytest.raises(ValueError, match="not in blank status"):
            blank_item.to_generating()

    def test_item_regenerate_resets_to_blank_if_final(self):
        """Тест что regenerate не переводит FINAL item в BLANK"""
        # Arrange
        item = QuizItem(
            id="item_1",
            question="Q",
            variants=[],
            order=0,
            status=QuizItemStatus.FINAL,
        )

        # Act
        item.regenerate()

        # Assert
        assert item.status != QuizItemStatus.BLANK

    def test_item_to_failed_from_generating(self, blank_item):
        """Тест перехода item в FAILED из GENERATING"""
        # Arrange
        blank_item.status = QuizItemStatus.GENERATING

        # Act
        blank_item.to_failed()

        # Assert
        assert blank_item.status == QuizItemStatus.FAILED

    def test_item_to_failed_fails_if_not_generating(self, blank_item):
        """Тест что to_failed выбросит ошибку если не GENERATING"""
        # Act & Assert
        with pytest.raises(ValueError, match="not in generating status"):
            blank_item.to_failed()

    def test_item_update(self):
        """Тест обновления item данными"""
        # Arrange
        item1 = QuizItem(
            id="item_1",
            question="Old question",
            variants=[],
            order=0,
            status=QuizItemStatus.BLANK,
        )

        new_variant = QuizItemVariant(
            content="Correct", is_correct=True, explanation="Yes"
        )
        item2 = QuizItem(
            id="item_1",  # Same ID
            question="New question",
            variants=[new_variant],
            order=1,
            status=QuizItemStatus.FINAL,
        )

        # Act
        item1.update(item2)

        # Assert
        assert item1.question == "New question"
        assert item1.variants == [new_variant]
        assert item1.order == 1
        assert item1.status == QuizItemStatus.FINAL
