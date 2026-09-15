"""Tests for adx and event_hubs transports."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

from vibey_bootstrap.transports._base import ShipResult
from vibey_bootstrap.transports.adx import AdxHandler, make_adx_handler
from vibey_bootstrap.transports.event_hubs import make_event_hubs_handler


def _record(msg: str = "hi") -> logging.LogRecord:
    return logging.LogRecord("svc", logging.INFO, __file__, 1, msg, None, None)


def test_adx_ship_calls_ingest() -> None:
    h = AdxHandler(cluster_uri="https://cluster", database="db", flush_interval=3600.0)
    client = MagicMock()
    with patch.object(h, "_get_client", return_value=client):
        with patch.object(h, "_ship", return_value=ShipResult(ok=True, count=1)) as ship:
            try:
                h.emit(_record())
                h.flush()
            finally:
                h.close()
            ship.assert_called()


def test_event_hubs_make_returns_none() -> None:
    assert make_event_hubs_handler() is None
    assert make_adx_handler() is None
