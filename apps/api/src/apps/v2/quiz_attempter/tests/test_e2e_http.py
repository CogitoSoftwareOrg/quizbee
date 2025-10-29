"""
End-to-End тесты для HTTP адаптеров.

Эти тесты проверяют HTTP endpoints с использованием FastAPI TestClient,
имитируя реальные HTTP запросы.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
import json

from ..adapters.in_.http.router import quiz_attempter_router
from ..adapters.in_.http.deps import QuizAttempterAppDeps, get_quiz_attempter_app
from ..domain.models import Attempt
from ..domain.refs import (
    QuizRef,
    QuizItemRef,
    MessageRef,
    MessageRole,
    MessageStatus,
)
from ..app.contracts import AskExplainerOutput


class TestQuizAttempterHTTP:
    """E2E тесты для HTTP endpoints quiz attempter"""

    @pytest.fixture
    def mock_quiz_attempter_app(self):
        """Mock для QuizAttempterApp"""
        mock_app = AsyncMock()

        # Настройка для finalize
        mock_app.finalize.return_value = None

        # Настройка для ask_explainer (streaming)
        async def mock_ask_explainer_generator():
            yield AskExplainerOutput(
                text="First explanation part", msg_id="msg_1", i=0, status="chunk"
            )
            yield AskExplainerOutput(
                text="Second explanation part", msg_id="msg_2", i=1, status="done"
            )

        mock_app.ask_explainer.return_value = mock_ask_explainer_generator()
        return mock_app

    @pytest.fixture
    def test_app(self, mock_quiz_attempter_app):
        """Создает FastAPI приложение с mock зависимостями"""
        app = FastAPI()
        app.include_router(quiz_attempter_router)

        # Mock dependency
        async def mock_get_quiz_attempter_app():
            return mock_quiz_attempter_app

        # Переопределяем dependency для тестирования
        app.dependency_overrides[get_quiz_attempter_app] = mock_get_quiz_attempter_app

        return app

    @pytest.fixture
    def client(self, test_app):
        return TestClient(test_app)

    def test_finalize_attempt_success(self, client, mock_quiz_attempter_app):
        """Тест успешной финализации attempt через HTTP"""
        # Arrange
        quiz_id = "test_quiz_123"
        attempt_id = "test_attempt_123"
        token = "valid_pb_token"

        # Act
        response = client.put(
            f"/v2/quizes/{quiz_id}/attempts/{attempt_id}", cookies={"pb_token": token}
        )

        # Assert
        assert response.status_code == 202
        response_data = response.json()
        assert response_data["scheduled"] is True
        assert response_data["quiz_id"] == quiz_id
        assert response_data["attempt_id"] == attempt_id

        # Проверяем что usecase был вызван правильно
        mock_quiz_attempter_app.finalize.assert_called_once()
        call_args = mock_quiz_attempter_app.finalize.call_args[0][0]
        assert call_args.attempt_id == attempt_id
        assert call_args.quiz_id == quiz_id
        assert call_args.token == token

    def test_finalize_attempt_no_token(self, client, mock_quiz_attempter_app):
        """Тест финализации attempt без токена"""
        # Act
        response = client.put("/v2/quizes/test_quiz/attempts/test_attempt")

        # Assert
        assert response.status_code == 401
        assert "Unauthorized" in response.json()["detail"]

        # Usecase не должен быть вызван
        mock_quiz_attempter_app.finalize.assert_not_called()

    def test_ask_explainer_success(self, client, mock_quiz_attempter_app):
        """Тест успешного запроса объяснения через HTTP (streaming)"""
        # Arrange
        quiz_id = "test_quiz_123"
        attempt_id = "test_attempt_123"
        token = "valid_pb_token"
        query = "Explain this answer"
        item_id = "test_item_1"

        # Act
        with client.stream(
            "GET",
            f"/v2/quizes/{quiz_id}/attempts/{attempt_id}/messages/sse",
            params={"q": query, "item": item_id},
            cookies={"pb_token": token},
        ) as response:
            # Assert
            assert response.status_code == 201

            # Читаем SSE события
            events = []
            for line in response.iter_lines():
                if line.startswith("data: "):
                    event_data = line[6:]  # Убираем "data: " префикс
                    events.append(json.loads(event_data))

            # Проверяем события
            assert len(events) == 2
            assert events[0]["text"] == "First explanation part"
            assert events[0]["status"] == "chunk"
            assert events[1]["text"] == "Second explanation part"
            assert events[1]["status"] == "done"

        # Проверяем что usecase был вызван правильно
        mock_quiz_attempter_app.ask_explainer.assert_called_once()
        call_args = mock_quiz_attempter_app.ask_explainer.call_args[0][0]
        assert call_args.query == query
        assert call_args.item_id == item_id
        assert call_args.attempt_id == attempt_id
        assert call_args.token == token

    def test_ask_explainer_no_token(self, client, mock_quiz_attempter_app):
        """Тест запроса объяснения без токена"""
        # Act
        response = client.get("/v2/quizes/test_quiz/attempts/test_attempt/messages/sse")

        # Assert
        assert response.status_code == 401
        assert "Unauthorized" in response.json()["detail"]

        # Usecase не должен быть вызван
        mock_quiz_attempter_app.ask_explainer.assert_not_called()

    def test_ask_explainer_missing_params(self, client, mock_quiz_attempter_app):
        """Тест запроса объяснения с отсутствующими параметрами"""
        # Act
        response = client.get(
            "/v2/quizes/test_quiz/attempts/test_attempt/messages/sse",
            cookies={"pb_token": "valid_token"},
            # Отсутствует параметр "q" (query)
        )

        # Assert - FastAPI должен вернуть 422 для отсутствующих required параметров
        assert response.status_code == 422

        # Usecase не должен быть вызван
        mock_quiz_attempter_app.ask_explainer.assert_not_called()


class TestHTTPErrorHandling:
    """Тесты обработки ошибок на HTTP уровне"""

    @pytest.fixture
    def failing_quiz_attempter_app(self):
        """Mock app который выбрасывает исключения"""
        mock_app = AsyncMock()

        # Настройка для finalize с ошибкой
        mock_app.finalize.side_effect = Exception("Domain error")

        # Настройка для ask_explainer с ошибкой
        mock_app.ask_explainer.side_effect = Exception("Explainer error")

        return mock_app

    @pytest.fixture
    def test_app_with_errors(self, failing_quiz_attempter_app):
        """Создает FastAPI приложение с mock который выбрасывает ошибки"""
        app = FastAPI()
        app.include_router(quiz_attempter_router)

        async def mock_get_failing_app():
            return failing_quiz_attempter_app

        app.dependency_overrides[get_quiz_attempter_app] = mock_get_failing_app

        return app

    @pytest.fixture
    def error_client(self, test_app_with_errors):
        return TestClient(test_app_with_errors)

    def test_finalize_with_domain_error(self, error_client, failing_quiz_attempter_app):
        """Тест обработки ошибок домена при финализации"""
        # Act
        response = error_client.put(
            "/v2/quizes/test_quiz/attempts/test_attempt",
            cookies={"pb_token": "valid_token"},
        )

        # Assert - Ошибки домена должны быть обработаны и возвращены как HTTP ошибки
        # (предполагается что есть глобальный exception handler)
        assert response.status_code >= 400

    def test_ask_explainer_with_domain_error(
        self, error_client, failing_quiz_attempter_app
    ):
        """Тест обработки ошибок домена при запросе объяснения"""
        # Act
        response = error_client.get(
            "/v2/quizes/test_quiz/attempts/test_attempt/messages/sse",
            params={"q": "test query", "item": "test_item"},
            cookies={"pb_token": "valid_token"},
        )

        # Assert
        assert response.status_code >= 400
