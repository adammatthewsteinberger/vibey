"""SqlHandler tests."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

from vibey_bootstrap.transports.sql import SqlHandler, make_sql_handler


def _record(msg: str = "hi") -> logging.LogRecord:
    return logging.LogRecord("svc", logging.INFO, __file__, 1, msg, None, None)


def test_flush_inserts_rows() -> None:
    engine = MagicMock()
    conn = MagicMock()
    engine.begin.return_value.__enter__ = MagicMock(return_value=conn)
    engine.begin.return_value.__exit__ = MagicMock(return_value=False)
    insert_stmt = MagicMock()

    with patch(
        "vibey_bootstrap.transports.sql._build_engine", return_value=(engine, insert_stmt, "DDL")
    ):
        h = SqlHandler(dsn="sqlite:///:memory:", flush_interval=3600.0, batch_size=1000)
        try:
            h.emit(_record())
            h.flush()
        finally:
            h.close()
    conn.execute.assert_called_once()


def test_make_factory_returns_none_without_dsn() -> None:
    assert make_sql_handler() is None
