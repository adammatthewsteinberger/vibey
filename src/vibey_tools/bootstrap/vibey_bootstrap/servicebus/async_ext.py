"""Service Bus extensions — async consumer, replay guard, multi-queue router."""

from __future__ import annotations

import asyncio
import logging
import os
import threading
import time
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from typing import Any

_logger = logging.getLogger(__name__)

MessageHandler = Callable[[Any], Awaitable[None]]


def service_bus_transport_type() -> str:
    """Return ``amqp`` or ``websocket`` from ``SERVICE_BUS_TRANSPORT_TYPE``."""
    mode = os.environ.get("SERVICE_BUS_TRANSPORT_TYPE", "amqp").lower()
    return "websocket" if mode == "websocket" else "amqp"


class ReplayGuard:
    """Bounded idempotency cache for message deduplication."""

    def __init__(self, *, max_size: int = 10_000, ttl_seconds: float = 3600.0) -> None:
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._seen: OrderedDict[str, float] = OrderedDict()
        self._lock = threading.Lock()

    def seen(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            self._evict(now)
            if key in self._seen:
                return True
            self._seen[key] = now
            if len(self._seen) > self._max_size:
                self._seen.popitem(last=False)
            return False

    def _evict(self, now: float) -> None:
        expired = [k for k, ts in self._seen.items() if now - ts > self._ttl]
        for k in expired:
            del self._seen[k]


async def run_async_consumer(
    client: Any,
    queue_name: str,
    handler: MessageHandler,
    *,
    stop_event: asyncio.Event | None = None,
    max_wait: float = 5.0,
) -> None:
    """Async receive loop with graceful shutdown on *stop_event*."""
    receiver = client.get_queue_receiver(queue_name=queue_name)
    stop = stop_event or asyncio.Event()
    async with receiver:
        while not stop.is_set():
            messages = await receiver.receive_messages(max_wait_time=max_wait)
            for msg in messages:
                if stop.is_set():
                    await receiver.abandon_message(msg)
                    break
                try:
                    await handler(msg)
                    await receiver.complete_message(msg)
                except Exception:
                    _logger.exception("async consumer handler failed")
                    await receiver.abandon_message(msg)


class MultiQueueRouter:
    """Route sends to named queues."""

    def __init__(self, client: Any) -> None:
        self._client = client
        self._senders: dict[str, Any] = {}

    def send(self, queue: str, body: bytes | str, **kwargs: Any) -> None:
        if queue not in self._senders:
            self._senders[queue] = self._client.get_queue_sender(queue_name=queue)
        sender = self._senders[queue]
        from azure.servicebus import ServiceBusMessage  # type: ignore[import-untyped]

        message = ServiceBusMessage(body if isinstance(body, (bytes, str)) else str(body))
        sender.send_messages(message, **kwargs)


__all__ = [
    "MultiQueueRouter",
    "ReplayGuard",
    "run_async_consumer",
    "service_bus_transport_type",
]
