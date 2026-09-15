"""NoSqlHandler tests."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

from vibey_bootstrap.transports.nosql import NoSqlHandler, make_nosql_handler


def _record(msg: str = "hi") -> logging.LogRecord:
    return logging.LogRecord("svc", logging.INFO, __file__, 1, msg, None, None)


def test_flush_insert_many() -> None:
    collection = MagicMock()
    client = MagicMock()
    with patch("vibey_bootstrap.transports.nosql._connect", return_value=(client, collection)):
        h = NoSqlHandler(
            uri="mongodb://localhost",
            database="logs",
            flush_interval=3600.0,
            batch_size=1000,
        )
        try:
            h.emit(_record())
            h.flush()
        finally:
            h.close()
    collection.insert_many.assert_called_once()


def test_make_factory_returns_none_without_uri() -> None:
    assert make_nosql_handler() is None
