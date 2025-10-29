# Testing Strategy for Hexagonal Architecture

## Что тестировать в гексагональной архитектуре

### 1. Domain Layer (Доменный слой) ✅

- **Domain Models (Модели домена)**: Value Objects, Entities, Aggregates
- **Domain Logic**: Бизнес-правила в моделях
- **Domain Errors**: Кастомные исключения домена

### 2. Application Layer (Слой приложения) ✅

- **Use Cases (Usecases)**: Бизнес-логика с моками портов
- **Application Contracts**: DTO, команды, интерфейсы приложения

### 3. Infrastructure Layer (Слой инфраструктуры)

- **Adapters**: Реализации портов (repositories, external services) - CONTRACT + INTEGRATION TESTS
- **HTTP Controllers**: End-to-end тесты HTTP endpoints - E2E TESTS

## Типы тестов

### Unit Tests (Модульные тесты)

```python
# Тестируем usecase с mocks портов
def test_usecase_success(mock_repository, mock_service):
    usecase = SomeUseCase(repository=mock_repository, service=mock_service)
    result = usecase.execute(cmd)
    assert result.success
```

### Contract Tests (Контрактные тесты)

```python
# Тестируем что реализации портов соответствуют интерфейсу
class RepositoryContract:
    def test_save_accepts_entity(self, repository):
        entity = create_test_entity()
        repository.save(entity)  # Не должно быть исключений
```

### Contract Tests (Контрактные тесты)

```python
# Тестируем что реализации портов соответствуют интерфейсу
class RepositoryContract:
    def test_save_accepts_entity(self, repository):
        entity = create_test_entity()
        repository.save(entity)  # Не должно быть исключений
```

### "Mock Integration" Tests (Мои текущие тесты адаптеров)

```python
# Тестируем адаптеры с mocks внешних зависимостей
def test_repository_with_mock_db(mock_db_client):
    repo = RealRepository(db_client=mock_db_client)
    entity = repo.get("id")
    assert isinstance(entity, DomainEntity)
```

### Real Integration Tests (Настоящие интеграционные тесты)

```python
# Тестируем с реальными БД, API, контейнерами
@pytest.mark.integration
def test_repository_with_real_db(real_postgres_container):
    repo = RealRepository(db_client=real_postgres_container)
    entity = repo.save_and_get(test_entity)
    assert entity.id is not None  # Реальная запись в БД
```

### E2E Tests (End-to-End тесты)

```python
# Тестируем HTTP endpoints
def test_http_endpoint(client):
    response = client.post("/api/endpoint", json=data)
    assert response.status_code == 200
```

## Важное уточнение: уровни тестирования

### Мои тесты адаптеров - это НЕ настоящие integration тесты!

**Что я назвал "integration tests"** - это тесты адаптеров с mocks (PocketBase client mock, HTTP client mock). Это на самом деле **unit tests для инфраструктурного слоя**.

**Настоящие integration tests** требуют:

- Реальные базы данных (PostgreSQL, PocketBase в Docker)
- Реальные внешние API (OpenAI, платежные системы)
- Docker контейнеры или testcontainers
- Медленные, хрупкие, запускаются отдельно

### Почему НЕ тестировать связи usecase + adapter как integration?

Потому что это **не integration testing**, а **contract testing**:

1. **Integration testing** - взаимодействие реальных компонентов (БД + код)
2. **Contract testing** - проверка что реализация соответствует интерфейсу (mocks)
3. **Unit testing** - компонент в изоляции (mocks для зависимостей)

В гексагональной архитектуре:

- ✅ Usecase с mocks портов = **unit test**
- ✅ Адаптер с mocks внешних сервисов = **unit test для инфраструктуры**
- ✅ Адаптер с реальными сервисами = **integration test** (дорого!)
- ✅ HTTP endpoint до БД = **E2E test**

## Запуск тестов

```bash
# Все тесты (кроме настоящих integration)
pytest

# Только мои unit тесты адаптеров (с mocks)
pytest -k "test_adapter_unit"

# Только настоящие integration тесты (с реальными сервисами)
RUN_INTEGRATION_TESTS=1 pytest -m integration test_integration_real.py

# E2E тесты
pytest -k "test_e2e"

# С покрытием
pytest --cov=src

# Пример запуска настоящих integration тестов:
# docker-compose up -d pocketbase openai-mock
# RUN_INTEGRATION_TESTS=1 pytest -m integration
```
