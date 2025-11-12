"""
Утилиты для работы с PocketBase admin клиентом.

Обеспечивает корректную авторизацию и ревалидацию токена админа.
"""

import logging
from pocketbase import PocketBase

from src.lib.settings import settings

logger = logging.getLogger(__name__)


async def ensure_admin_auth(pb: PocketBase) -> None:
    """
    Обеспечивает валидную авторизацию админа в PocketBase клиенте.

    Проверяет наличие и валидность токена, при необходимости выполняет
    авторизацию заново.

    Args:
        pb: PocketBase клиент для проверки и обновления авторизации

    Raises:
        Exception: Если авторизация не удалась
    """
    try:
        # Проверяем наличие токена и его валидность
        # Используем приватные поля библиотеки, так как публичных методов нет
        token = pb._inners.auth._token

        # Если токена нет или он истек, выполняем авторизацию
        if not token or pb._inners.auth._is_token_expired():
            logger.info("Admin token expired or missing, re-authenticating...")

            auth_result = await pb.collection("_superusers").auth.with_password(
                settings.pb_email, settings.pb_password
            )

            if not auth_result or not auth_result.get("token"):
                raise Exception("Failed to authenticate admin: no token received")

            pb._inners.auth.set_user(
                {
                    "token": auth_result.get("token", ""),
                    "record": auth_result.get("record", {}),
                }
            )

            logger.info("Admin re-authenticated successfully")
        else:
            logger.debug("Admin token is valid")

    except Exception as e:
        logger.error(f"Failed to ensure admin auth: {e}", exc_info=True)
        raise


async def init_admin_pb() -> PocketBase:
    """
    Инициализирует PocketBase клиент с авторизацией админа.

    Returns:
        Авторизованный PocketBase клиент

    Raises:
        Exception: Если авторизация не удалась
    """
    pb = PocketBase(settings.pb_url)
    await ensure_admin_auth(pb)
    return pb
