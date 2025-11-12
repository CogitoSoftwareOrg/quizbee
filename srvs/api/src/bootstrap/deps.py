from typing import Annotated
from fastapi import Request, Depends, HTTPException
from arq import ArqRedis

from src.lib.pb_admin import ensure_admin_auth


async def http_ensure_admin_pb(request: Request):
    """
    Зависимость FastAPI для обеспечения валидной авторизации админа.

    Вызывается перед каждым HTTP запросом благодаря глобальной зависимости
    в create_app().

    Пропускает проверку для health check эндпоинтов.
    """
    # Пропускаем health check эндпоинты
    if request.url.path in ["/health", "/readyz", "/livez"]:
        return

    pb = request.app.state.admin_pb
    try:
        await ensure_admin_auth(pb)
    except Exception as e:
        # Если авторизация не удалась, возвращаем 500 ошибку
        # Это критическая ошибка, так как без админа API не может работать
        raise HTTPException(
            status_code=500, detail=f"Failed to authenticate admin: {str(e)}"
        )


def get_arq_pool(request: Request) -> ArqRedis:
    """Получить ARQ Redis pool из app.state для отправки задач в очередь."""
    return request.app.state.arq_pool


ArqPoolDeps = Annotated[ArqRedis, Depends(get_arq_pool)]
