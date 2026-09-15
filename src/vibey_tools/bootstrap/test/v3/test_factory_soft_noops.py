"""Every v3 factory must soft no-op (return None) when misconfigured."""

from __future__ import annotations

import pytest

from vibey_bootstrap.transports.adx import make_adx_handler
from vibey_bootstrap.transports.blob import make_blob_handler
from vibey_bootstrap.transports.event_hubs import make_event_hubs_handler
from vibey_bootstrap.transports.file import make_file_handler
from vibey_bootstrap.transports.nosql import make_nosql_handler
from vibey_bootstrap.transports.panther import make_panther_handler, make_panther_search_client
from vibey_bootstrap.transports.sql import make_sql_handler


@pytest.mark.parametrize(
    "factory,env",
    [
        (make_panther_handler, {}),
        (make_panther_handler, {"PANTHER_API_HOST": "https://x"}),
        (make_sql_handler, {}),
        (make_nosql_handler, {}),
        (make_nosql_handler, {"NOSQL_LOG_URI": "mongodb://localhost"}),
        (make_blob_handler, {}),
        (make_blob_handler, {"BLOB_LOG_CONTAINER": "logs"}),
        (make_file_handler, {}),
        (make_adx_handler, {}),
        (make_adx_handler, {"ADX_CLUSTER_URI": "https://c"}),
        (make_event_hubs_handler, {}),
        (make_event_hubs_handler, {"EVENTHUB_FQNS": "ns.servicebus.windows.net"}),
        (make_panther_search_client, {}),
        (make_panther_search_client, {"PANTHER_API_HOST": "https://x"}),
    ],
)
def test_factory_returns_none_when_incomplete(monkeypatch, factory, env) -> None:
    for key in (
        "PANTHER_API_HOST",
        "PANTHER_LOG_SOURCE_ID",
        "PANTHER_LOG_SOURCE_TOKEN",
        "PANTHER_API_KEY",
        "SQL_LOG_DSN",
        "NOSQL_LOG_URI",
        "NOSQL_LOG_DATABASE",
        "BLOB_LOG_CONTAINER",
        "BLOB_LOG_ACCOUNT_URL",
        "BLOB_LOG_CONNECTION_STRING",
        "FILE_LOG_PATH",
        "ADX_CLUSTER_URI",
        "ADX_DATABASE",
        "EVENTHUB_FQNS",
        "EVENTHUB_NAME",
    ):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    assert factory() is None


def test_panther_factory_returns_none_without_requests(monkeypatch) -> None:
    monkeypatch.setenv("PANTHER_API_HOST", "https://x")
    monkeypatch.setenv("PANTHER_LOG_SOURCE_ID", "1")
    monkeypatch.setenv("PANTHER_LOG_SOURCE_TOKEN", "tok")

    def _boom() -> object:
        raise ImportError("no requests")

    monkeypatch.setattr("vibey_bootstrap.transports.panther._build_session", _boom)
    assert make_panther_handler() is None


def test_sql_factory_returns_none_without_sqlalchemy(monkeypatch) -> None:
    monkeypatch.setenv("SQL_LOG_DSN", "sqlite:///:memory:")

    def _boom(*a, **k) -> object:
        raise ImportError("no sqlalchemy")

    monkeypatch.setattr("vibey_bootstrap.transports.sql._build_engine", _boom)
    assert make_sql_handler() is None


def test_blob_factory_returns_none_without_sdk(monkeypatch) -> None:
    monkeypatch.setenv("BLOB_LOG_CONTAINER", "logs")
    monkeypatch.setenv("BLOB_LOG_CONNECTION_STRING", "UseDevelopmentStorage=true")

    def _boom(**k) -> object:
        raise ImportError("no azure.storage.blob")

    monkeypatch.setattr("vibey_bootstrap.transports.blob._build_container_client", _boom)
    assert make_blob_handler() is None
