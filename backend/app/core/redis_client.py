from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class InMemoryPubSub:
    """Fallback pub/sub when Redis is unavailable."""

    def __init__(self) -> None:
        self._channels: dict[str, list] = {}
        self._store: dict[str, str] = {}
        self._closed = False

    async def publish(self, channel: str, message: str) -> int:
        for queue in self._channels.get(channel, []):
            queue.append(message)
        return 1

    async def set(self, key: str, value: str) -> None:
        self._store[key] = value

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    def pubsub(self) -> InMemoryPubSubClient:
        return InMemoryPubSubClient(self)

    async def aclose(self) -> None:
        self._closed = True


class InMemoryPubSubClient:
    def __init__(self, parent: InMemoryPubSub) -> None:
        self._parent = parent
        self._subscribed: list[str] = []
        self._queue: list[dict[str, Any]] = []

    async def subscribe(self, channel: str) -> None:
        self._subscribed.append(channel)
        if channel not in self._parent._channels:
            self._parent._channels[channel] = []
        self._parent._channels[channel].append(self._queue)

    async def unsubscribe(self, channel: str) -> None:
        if channel in self._subscribed:
            self._subscribed.remove(channel)

    async def get_message(self, ignore_subscribe_messages: bool = True, timeout: float = 1.0) -> dict | None:
        if self._queue:
            data = self._queue.pop(0)
            return {"type": "message", "data": data}
        return None

    async def aclose(self) -> None:
        pass


_memory_redis: InMemoryPubSub | None = None


async def get_redis():
    """Return Redis client or in-memory fallback."""
    global _memory_redis
    try:
        import redis.asyncio as aioredis
        from app.core.config import settings
        client = aioredis.from_url(settings.redis_url, decode_responses=True)
        await client.ping()
        return client
    except Exception as e:
        logger.warning("Redis unavailable (%s), using in-memory fallback", e)
        if _memory_redis is None:
            _memory_redis = InMemoryPubSub()
        return _memory_redis
