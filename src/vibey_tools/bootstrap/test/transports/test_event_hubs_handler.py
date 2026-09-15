"""Event Hubs handler tests."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

from vibey_bootstrap.transports._base import ShipResult
from vibey_bootstrap.transports.event_hubs import EventHubsHandler


def _record(msg: str = "hi") -> logging.LogRecord:
    return logging.LogRecord("svc", logging.INFO, __file__, 1, msg, None, None)


def test_event_hubs_handler_ship() -> None:
    h = EventHubsHandler(
        fully_qualified_namespace="ns.servicebus.windows.net",
        eventhub_name="logs",
        flush_interval=3600.0,
    )
    producer = MagicMock()
    batch = MagicMock()
    producer.create_batch.return_value = batch
    with patch.object(h, "_get_producer", return_value=producer):
        with patch.object(h, "_ship", return_value=ShipResult(ok=True, count=1)) as ship:
            try:
                h.emit(_record())
                h.flush()
            finally:
                h.close()
            ship.assert_called()
