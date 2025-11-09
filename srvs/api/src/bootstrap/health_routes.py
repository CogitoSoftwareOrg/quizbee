"""Health check endpoints for service monitoring."""

import logging
from fastapi import APIRouter, Response, Request
from fastapi.responses import JSONResponse

from src.lib.health import HealthChecker
from src.lib.settings import settings

logger = logging.getLogger(__name__)

health_router = APIRouter(tags=["health"])


@health_router.get("/health")
async def health():
    """Basic liveness check - returns 200 if the service is running."""
    return {"status": "ok"}


@health_router.get("/readyz")
async def readiness(request: Request):
    """
    Comprehensive readiness check - returns 200 only if all dependencies are healthy.

    Checks:
    - Redis connectivity
    - Meilisearch availability
    - PocketBase availability
    - ARQ worker heartbeat (from Redis)
    """
    try:
        arq_pool = request.app.state.arq_pool
        meili_client = request.app.state.meili_client
        http = request.app.state.http

        checker = HealthChecker(
            http=http,
            redis_client=arq_pool,
            meili_client=meili_client,
            pb_url=settings.pb_url,
        )

        results = await checker.check_all()
        is_ready = all(results.values())

        status_code = 200 if is_ready else 503

        return JSONResponse(
            status_code=status_code,
            content={
                "ready": is_ready,
                "checks": results,
            },
        )

    except Exception as e:
        logger.error(f"Readiness check failed with exception: {e}", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={
                "ready": False,
                "error": str(e),
            },
        )
