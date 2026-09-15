"""BlobHandler tests."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock

from vibey_bootstrap.transports.blob import BlobHandler, make_blob_handler


def _record(msg: str = "hi") -> logging.LogRecord:
    return logging.LogRecord("svc", logging.INFO, __file__, 1, msg, None, None)


def test_ship_append_mode() -> None:
    container = MagicMock()
    blob_client = MagicMock()
    container.get_blob_client.return_value = blob_client
    h = BlobHandler(container_client=container, flush_interval=3600.0, batch_size=1000)
    try:
        h.emit(_record())
        h.flush()
    finally:
        h.close()
    blob_client.append_block.assert_called_once()


def test_make_factory_returns_none_without_container() -> None:
    assert make_blob_handler() is None
