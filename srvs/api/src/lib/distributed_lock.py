"""Distributed lock utilities using Redis."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator
import uuid

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class DistributedLock:
    """Distributed lock implementation using Redis."""

    def __init__(self, redis_client: redis.Redis, lock_timeout: int = 300):
        """
        Initialize distributed lock.

        Args:
            redis_client: Redis client instance
            lock_timeout: Lock timeout in seconds (default 5 minutes)
        """
        self.redis = redis_client
        self.lock_timeout = lock_timeout

    @asynccontextmanager
    async def lock(
        self, key: str, wait_timeout: float = 60.0, retry_interval: float = 0.1
    ) -> AsyncIterator[bool]:
        """
        Acquire distributed lock with retries.

        Args:
            key: Lock key (e.g., "quiz:generate:quiz_id")
            wait_timeout: Maximum time to wait for lock acquisition in seconds
            retry_interval: Time between retry attempts in seconds

        Yields:
            True if lock was acquired

        Raises:
            TimeoutError: If lock cannot be acquired within wait_timeout
        """
        lock_key = f"lock:{key}"
        lock_value = str(
            uuid.uuid4()
        )  # Unique token to prevent unlocking by other processes

        # Try to acquire lock with retries
        start_time = asyncio.get_event_loop().time()
        acquired = False

        while not acquired:
            # Try to set lock with NX (only if not exists) and EX (expiration)
            acquired = await self.redis.set(
                lock_key, lock_value, nx=True, ex=self.lock_timeout
            )

            if acquired:
                logger.debug(f"Lock acquired: {lock_key}")
                break

            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= wait_timeout:
                logger.warning(
                    f"Failed to acquire lock {lock_key} within {wait_timeout}s"
                )
                raise TimeoutError(
                    f"Could not acquire lock {key} within {wait_timeout} seconds"
                )

            # Wait before retry
            await asyncio.sleep(retry_interval)
            logger.debug(
                f"Waiting for lock {lock_key} (elapsed: {elapsed:.1f}s/{wait_timeout}s)"
            )

        try:
            yield True
        finally:
            # Release lock only if we own it (check token)
            if acquired:
                await self._release_lock(lock_key, lock_value)

    async def _release_lock(self, lock_key: str, lock_value: str) -> None:
        """
        Release lock safely using Lua script to ensure we only delete our own lock.

        Args:
            lock_key: Redis key for the lock
            lock_value: Unique token that was used to acquire the lock
        """
        # Lua script to atomically check token and delete if it matches
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """

        try:
            result = await self.redis.eval(lua_script, 1, lock_key, lock_value)
            if result:
                logger.debug(f"Lock released: {lock_key}")
            else:
                logger.warning(
                    f"Lock {lock_key} was not released (already expired or owned by another process)"
                )
        except Exception as e:
            logger.error(f"Failed to release lock {lock_key}: {e}")
