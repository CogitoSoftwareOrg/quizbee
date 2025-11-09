import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.lib.config.logging import request_id_context, user_id_context


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware для установки контекста запроса в логи"""

    async def dispatch(self, request: Request, call_next):
        # Генерируем request_id
        request_id = str(uuid.uuid4())[:8]

        # Устанавливаем контекст
        request_id_context.set(request_id)

        user_id = getattr(request.state, "user", {}).get("id", "")
        if user_id:
            user_id_context.set(str(user_id))
        else:
            user_id_context.set("")

        response = await call_next(request)
        return response
