import os
import time
import httpx
from pocketbase import PocketBase
import pytest
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

from src.lib.settings import settings

POCKETBASE_IMAGE = os.getenv("PB_IMAGE", "quizbee-prod-test-pb:latest")
PB_PORT = 8090


@pytest.fixture(scope="session")
def pocketbase_container():
    """
    Поднимает чистый PocketBase, доступный на localhost:<mapped_port>,
    и останавливает его по завершении сессии тестов.
    """
    container = DockerContainer(POCKETBASE_IMAGE).with_exposed_ports(PB_PORT)
    container.start()

    # Определяем проброшенный порт
    host = container.get_container_host_ip()
    port = container.get_exposed_port(PB_PORT)
    base_url = f"http://{host}:{port}"

    def _ping():
        r = httpx.get(f"{base_url}_", timeout=2.0)
        r.raise_for_status()
        return True

    for _ in range(60):
        try:
            if _ping():
                break
        except Exception:
            time.sleep(0.5)
    else:
        raise RuntimeError("PocketBase не поднялся вовремя")

    yield {"base_url": base_url}
    container.stop()


@pytest.mark.asyncio
@pytest.fixture(scope="session")
async def admin_pb(pocketbase_container):
    """
    Создаёт первого админа и логинится. Возвращает admin token.
    """
    base_url = pocketbase_container["base_url"]
    pb = PocketBase(base_url)
    await pb.collection("_superusers").auth.with_password(
        settings.pb_email, settings.pb_password
    )
    return pb


@pytest.fixture(scope="session", autouse=True)
def pb_schema(admin_pb):
    """
    Создаёт минимальные коллекции для репозитория: quizzes и quiz_items.
    Можно расширять типы полей под ваши реальные модели.
    """
    base_url = admin_pb.base_url
    headers = {"Authorization": admin_pb._inners.auth._token}

    def ensure_collection(name: str, schema_fields: list):
        payload = {
            "name": name,
            "type": "base",
            "schema": schema_fields,
            "listRule": "",
            "viewRule": "",
            "createRule": "",
            "updateRule": "",
            "deleteRule": "",
        }
        rr = httpx.post(
            f"{base_url}/api/collections",
            headers=headers,
            json=payload,
            timeout=10.0,
        )
        rr.raise_for_status()

    # quizzes: author_id, title, query, difficulty, status
    ensure_collection(
        "quizzes",
        [
            {"name": "author_id", "type": "text", "required": True},
            {"name": "title", "type": "text", "required": True},
            {"name": "query", "type": "text", "required": True},
            {"name": "difficulty", "type": "text", "required": True},
            {"name": "status", "type": "text", "required": False},
        ],
    )

    ensure_collection(
        "quiz_items",
        [
            {
                "name": "quiz_id",
                "type": "relation",
                "required": True,
                "options": {
                    "collectionId": "quizzes",
                    "cascadeDelete": True,
                    "maxSelect": 1,
                },
            },
            {"name": "question", "type": "text", "required": True},
            {"name": "variants", "type": "json", "required": True},
            {"name": "order", "type": "number", "required": True},
            {"name": "status", "type": "text", "required": True},
        ],
    )

    return True
