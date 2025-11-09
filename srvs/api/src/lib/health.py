"""Health check utilities for monitoring service health."""

import logging
from datetime import datetime, timedelta
from typing import Optional

import httpx
import redis.asyncio as redis
from meilisearch_python_sdk import AsyncClient as MeiliClient

logger = logging.getLogger(__name__)

# Redis key for worker heartbeat
WORKER_HEARTBEAT_KEY = "quizbee:worker:heartbeat"
WORKER_HEARTBEAT_TTL = 30  # seconds - heartbeat expires after 30 seconds
WORKER_HEARTBEAT_INTERVAL = 10  # seconds - update every 10 seconds


class HealthChecker:
    """Utility for checking service health."""

    def __init__(
        self,
        http: httpx.AsyncClient,
        redis_client: redis.Redis,
        meili_client: Optional[MeiliClient] = None,
        pb_url: Optional[str] = None,
    ):
        self.redis_client = redis_client
        self.meili_client = meili_client
        self.pb_url = pb_url
        self.http = http

    async def check_redis(self) -> bool:
        """Check if Redis is accessible."""
        try:
            await self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False

    async def check_meilisearch(self) -> bool:
        """Check if Meilisearch is accessible."""
        if not self.meili_client:
            logger.warning("Meilisearch client not configured")
            return True  # Skip if not configured

        try:
            await self.meili_client.health()
            return True
        except Exception as e:
            logger.error(f"Meilisearch health check failed: {e}")
            return False

    async def check_pocketbase(self) -> bool:
        """Check if PocketBase is accessible."""
        if not self.pb_url:
            logger.warning("PocketBase client not configured")
            return True  # Skip if not configured

        try:
            res = await self.http.get(f"{self.pb_url}_/")
            return res.status_code == 200
        except Exception as e:
            logger.error(f"PocketBase health check failed: {e}")
            return False

    async def check_worker_heartbeat(self) -> bool:
        """Check if ARQ worker is alive by checking heartbeat."""
        try:
            heartbeat = await self.redis_client.get(WORKER_HEARTBEAT_KEY)
            if not heartbeat:
                logger.error("Worker heartbeat not found in Redis")
                return False

            # Parse timestamp and check if it's recent
            timestamp = float(heartbeat)
            heartbeat_time = datetime.fromtimestamp(timestamp)
            now = datetime.now()
            age = (now - heartbeat_time).total_seconds()

            if age > WORKER_HEARTBEAT_TTL:
                logger.error(
                    f"Worker heartbeat is stale (age: {age}s, max: {WORKER_HEARTBEAT_TTL}s)"
                )
                return False

            return True
        except Exception as e:
            logger.error(f"Worker heartbeat check failed: {e}")
            return False

    async def check_all(self) -> dict[str, bool]:
        """Check all configured services."""
        results = {
            "redis": await self.check_redis(),
            "meilisearch": await self.check_meilisearch(),
            "pocketbase": await self.check_pocketbase(),
            "worker": await self.check_worker_heartbeat(),
        }
        return results

    async def is_ready(self) -> bool:
        """Check if all services are ready."""
        results = await self.check_all()
        return all(results.values())


async def update_worker_heartbeat(redis_client: redis.Redis) -> None:
    """Update worker heartbeat in Redis."""
    try:
        timestamp = datetime.now().timestamp()
        await redis_client.set(
            WORKER_HEARTBEAT_KEY, str(timestamp), ex=WORKER_HEARTBEAT_TTL
        )
        logger.debug(f"Worker heartbeat updated at {timestamp}")
    except Exception as e:
        logger.error(f"Failed to update worker heartbeat: {e}")
