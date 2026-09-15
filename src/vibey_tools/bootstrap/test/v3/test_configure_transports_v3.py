"""Configure transports integration for all v3 sinks."""

from __future__ import annotations

from unittest.mock import patch

import vibey_bootstrap.transports as transports
from vibey_bootstrap.transports import configure_transports, list_transports


def _reset() -> None:
    transports._reset_transports()


def test_configure_all_v3_transports_explicit_off() -> None:
    configure_transports(
        console=False,
        app_insights=False,
        sumo_logic=False,
        panther=False,
        file=False,
        blob=False,
        sql=False,
        nosql=False,
        adx=False,
        event_hubs=False,
    )
    status = list_transports()
    assert all(not v["enabled"] for v in status.values())


def test_configure_panther_env(monkeypatch) -> None:
    monkeypatch.setenv("PANTHER_API_HOST", "https://p.test")
    monkeypatch.setenv("PANTHER_LOG_SOURCE_ID", "1")
    monkeypatch.setenv("PANTHER_LOG_SOURCE_TOKEN", "tok")
    monkeypatch.setenv("PANTHER_LOGGING_ENABLED", "1")
    configure_transports()
    try:
        assert list_transports()["panther"]["enabled"] is True
    finally:
        configure_transports(panther=False)


def test_configure_sql_env(monkeypatch) -> None:
    pytest = __import__("pytest")
    pytest.importorskip("sqlalchemy")
    monkeypatch.setenv("SQL_LOG_DSN", "sqlite:///:memory:")
    monkeypatch.setenv("SQL_LOGGING_ENABLED", "1")
    configure_transports()
    try:
        assert list_transports()["sql"]["enabled"] is True
    finally:
        configure_transports(sql=False)


def test_configure_adx_env(monkeypatch) -> None:
    monkeypatch.setenv("ADX_CLUSTER_URI", "https://cluster")
    monkeypatch.setenv("ADX_DATABASE", "db")
    monkeypatch.setenv("ADX_LOGGING_ENABLED", "1")
    with patch("vibey_bootstrap.transports.adx.StreamingIngestClient", create=True):
        configure_transports()
    try:
        assert list_transports()["adx"]["enabled"] is True
    finally:
        configure_transports(adx=False)
