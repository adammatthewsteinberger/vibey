"""Extended transport coverage tests."""

from __future__ import annotations

import logging

import pytest

from vibey_bootstrap.transports.nosql import make_nosql_handler
from vibey_bootstrap.transports.panther import make_panther_handler
from vibey_bootstrap.transports.sql import _validate_identifier, make_sql_handler


def test_validate_identifier_rejects_bad_names() -> None:
    with pytest.raises(ValueError):
        _validate_identifier("bad-name")


def test_make_panther_from_env(monkeypatch) -> None:
    monkeypatch.setenv("PANTHER_API_HOST", "https://p.test")
    monkeypatch.setenv("PANTHER_LOG_SOURCE_ID", "1")
    monkeypatch.setenv("PANTHER_LOG_SOURCE_TOKEN", "tok")
    h = make_panther_handler()
    assert h is not None
    h.close()


def test_make_sql_sqlite(monkeypatch) -> None:
    pytest.importorskip("sqlalchemy")
    monkeypatch.setenv("SQL_LOG_DSN", "sqlite:///:memory:")
    h = make_sql_handler()
    assert h is not None
    h.emit(logging.LogRecord("x", logging.INFO, __file__, 1, "m", None, None))
    h.flush()
    h.close()


def test_make_nosql_missing_database(monkeypatch) -> None:
    monkeypatch.setenv("NOSQL_LOG_URI", "mongodb://localhost")
    monkeypatch.delenv("NOSQL_LOG_DATABASE", raising=False)
    assert make_nosql_handler() is None
