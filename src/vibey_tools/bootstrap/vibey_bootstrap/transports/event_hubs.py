"""Azure Event Hubs logging transport — hot-path live tail producer."""

from __future__ import annotations

import logging
from typing import Any

from vibey_bootstrap.counters import bump_counter
from vibey_bootstrap.failclose import fail_open_env, optional_env
from vibey_bootstrap.logging.correlation import CorrelationFilter
from vibey_bootstrap.logging.jsonformatter import JsonLogFormatter
from vibey_bootstrap.transports._base import ShipResult, _BufferedShipper

_COUNTER_FLUSHES = "event_hubs.transport.flushes"


class EventHubsHandler(_BufferedShipper):
    """Buffered handler publishing log batches to Event Hubs."""

    _THREAD_NAME = "event-hubs-transport"

    def __init__(
        self,
        *,
        fully_qualified_namespace: str,
        eventhub_name: str,
        credential: Any = None,
        batch_size: int = 100,
        flush_interval: float = 5.0,
        max_buffer: int = 10_000,
    ) -> None:
        super().__init__(
            counter_prefix="event_hubs",
            batch_size=batch_size,
            flush_interval=flush_interval,
            max_buffer=max_buffer,
        )
        self._fqns = fully_qualified_namespace
        self._eventhub_name = eventhub_name
        self._credential = credential
        self._producer: Any = None

        self.setFormatter(JsonLogFormatter())
        self.addFilter(CorrelationFilter())

    def _get_producer(self) -> Any:
        if self._producer is None:
            from azure.eventhub import EventHubProducerClient

            cred = self._credential
            if cred is None:
                from vibey_bootstrap.identity import build_credential

                cred = build_credential()
            self._producer = EventHubProducerClient(
                fully_qualified_namespace=self._fqns,
                eventhub_name=self._eventhub_name,
                credential=cred,
            )
        return self._producer

    def _on_close(self) -> None:
        try:
            if self._producer is not None:
                self._producer.close()
        except Exception:
            pass

    def _ship(self, batch: list[str]) -> ShipResult:
        if not batch:
            return ShipResult(ok=True, count=0)
        bump_counter(_COUNTER_FLUSHES)
        try:
            from azure.eventhub import EventData

            producer = self._get_producer()
            event_batch = producer.create_batch()
            for line in batch:
                event_batch.add(EventData(line.encode("utf-8")))
            producer.send_batch(event_batch)
            return ShipResult(ok=True, count=len(batch))
        except Exception:
            return ShipResult(ok=False, count=0)


def make_event_hubs_handler() -> logging.Handler | None:
    fqns = fail_open_env("EVENTHUB_FQNS")
    name = fail_open_env("EVENTHUB_NAME")
    if not fqns or not name:
        return None
    try:
        return EventHubsHandler(
            fully_qualified_namespace=fqns,
            eventhub_name=name,
            batch_size=_int_env("EVENTHUB_BATCH_SIZE", 100),
            flush_interval=_float_env("EVENTHUB_FLUSH_INTERVAL", 5.0),
            max_buffer=_int_env("EVENTHUB_MAX_BUFFER", 10_000),
        )
    except ImportError:
        logging.getLogger(__name__).debug(
            "Event Hubs env set but [eventhubslog] extra not installed — disabled."
        )
        return None


def _int_env(name: str, default: int) -> int:
    raw = optional_env(name)
    try:
        return int(raw) if raw else default
    except ValueError:
        return default


def _float_env(name: str, default: float) -> float:
    raw = optional_env(name)
    try:
        return float(raw) if raw else default
    except ValueError:
        return default


__all__ = ["EventHubsHandler", "make_event_hubs_handler"]
