"""
Настоящие интеграционные тесты с реальными компонентами.

Эти тесты требуют:
- Реальную базу данных (PocketBase)
- Реальные внешние API
- Docker контейнеры или testcontainers
"""

import os
import pytest
from httpx import AsyncClient
from pocketbase import PocketBase
import asyncio
from unittest.mock import patch

from ..adapters.out.pb_attempt_repository import PBAttemptRepository
from ..domain.models import Attempt
from ..domain.refs import QuizRef, QuizItemRef


@pytest.mark.integration
class TestPBAttemptRepositoryRealIntegration:
    """
    Настоящие интеграционные тесты с реальной PocketBase.

    Требует запущенного PocketBase сервера.
    Запуск: docker run -p 8090:8090 your-pocketbase-image
    """

    @pytest.fixture
    async def real_pb_client(self):
        """Реальный PocketBase клиент"""
        # Предполагаем что PB запущен локально
        pb = PocketBase("http://localhost:8090")

        # Авторизация как admin (нужны реальные credentials)
        await pb.collection("_superusers").auth.with_password(
            "test@example.com", "test_password"
        )

        yield pb

        # Cleanup - удаляем тестовые данные
        try:
            await pb.collection("quizAttempts").delete("test_attempt_real")
        except:
            pass

    @pytest.fixture
    async def real_http_client(self):
        """Реальный HTTP клиент"""
        async with AsyncClient() as client:
            yield client

    @pytest.fixture
    async def repository(self, real_pb_client, real_http_client):
        return PBAttemptRepository(admin_pb=real_pb_client, http=real_http_client)

    @pytest.mark.asyncio
    async def test_save_and_get_real_attempt(self, repository):
        """Интеграционный тест: сохранить и получить attempt из реальной БД"""
        # Arrange
        attempt = Attempt(
            id="test_attempt_real",
            user_id="real_user_123",
            quiz=QuizRef(
                id="real_quiz_123",
                query="Integration test quiz",
                items=[
                    QuizItemRef(
                        id="real_item_1",
                        question="What is integration testing?",
                        answers=["Testing components together"],
                        choice=None,
                    )
                ],
                material_content="Integration testing content",
            ),
            choices=[],
        )

        # Act
        await repository.save(attempt)
        retrieved = await repository.get("test_attempt_real")

        # Assert
        assert retrieved.id == attempt.id
        assert retrieved.user_id == attempt.user_id
        assert retrieved.quiz.id == attempt.quiz.id


@pytest.mark.integration
class TestAIExplainerRealIntegration:
    """
    Интеграционные тесты с реальным AI (OpenAI/Langfuse).

    Требует:
    - Реальный API ключ OpenAI
    - Реальный Langfuse сервер (или mocks для внешних вызовов)
    """

    @pytest.fixture
    async def real_explainer(self):
        """Реальный explainer с настоящими API вызовами"""
        from ..adapters.out.explainers.ai_grok_explainer import AIGrokExplainer

        # Предполагаем что переменные окружения настроены
        # explainer = AIExplainer(
        #     langfuse=None,  # Или реальный клиент
        #     # другие реальные зависимости
        # )
        # return explainer

    @pytest.mark.asyncio
    async def test_real_ai_explanation(self, real_explainer):
        """Интеграционный тест с реальным AI API"""
        attempt = Attempt(
            id="real_ai_test",
            user_id="user_123",
            quiz=QuizRef(
                id="ai_quiz",
                query="AI test question",
                items=[],
                material_content="AI content",
            ),
            choices=[],
        )

        # Act - реальный API вызов к OpenAI
        messages = []
        async for msg in real_explainer.explain(
            query="Explain this concept",
            attempt=attempt,
            item=attempt.quiz.items[0] if attempt.quiz.items else None,
            ai_msg=None,
            cache_key="real_test",
        ):
            messages.append(msg)

        # Assert
        assert len(messages) > 0
        # Проверяем что AI вернул осмысленный ответ


@pytest.mark.integration
class TestFullStackIntegration:
    """
    Полностековые интеграционные тесты.

    Тестируют весь путь: HTTP -> Usecase -> Repository -> External APIs
    """

    @pytest.fixture
    async def real_app(self):
        """Реальное FastAPI приложение со всеми зависимостями"""
        from fastapi import FastAPI
        from bootstrap.app import create_app

        # Создаем приложение как в продакшене
        app = create_app()

        # Можно переопределить некоторые зависимости на test версии
        # app.dependency_overrides[some_dep] = test_version

        return app

    @pytest.fixture
    async def real_client(self, real_app):
        """HTTP клиент для реального приложения"""
        async with AsyncClient(base_url="http://localhost:8000") as client:
            yield client

    @pytest.mark.asyncio
    async def test_full_quiz_flow(self, real_client):
        """Полный интеграционный тест всего flow"""
        # Arrange - создать quiz и attempt в реальной БД

        # Act - сделать HTTP запросы через весь стек
        # response = await real_client.post("/api/quizes", json=quiz_data)
        # assert response.status_code == 201

        # response = await real_client.post("/api/attempts", json=attempt_data)
        # assert response.status_code == 201

        # response = await real_client.get("/api/attempts/{id}/explain")
        # assert response.status_code == 200

        pass  # Реализовать полный сценарий


# Конфигурация для запуска интеграционных тестов
@pytest.fixture(scope="session", autouse=True)
def setup_integration_test_env():
    """Настройка окружения для интеграционных тестов"""
    # Проверяем что необходимые сервисы доступны
    if not os.getenv("RUN_INTEGRATION_TESTS"):
        pytest.skip("Integration tests disabled. Set RUN_INTEGRATION_TESTS=1")

    # Проверяем доступность внешних сервисов
    # check_database_connection()
    # check_external_api_availability()

    yield

    # Cleanup после всех тестов


# Пример запуска:
# RUN_INTEGRATION_TESTS=1 pytest -m integration
# Или с Docker Compose:
# docker-compose up -d db external-api
# RUN_INTEGRATION_TESTS=1 pytest -m integration
