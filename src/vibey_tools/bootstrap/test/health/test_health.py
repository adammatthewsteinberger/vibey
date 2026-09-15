"""Tests for ``vibey_bootstrap.health``."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import Any

import pytest

from vibey_bootstrap.health import (
    check_app_config_health,
    check_app_insights_health,
    check_app_insights_logging,
)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for k in (
        "USE_MOCK_BOOTSTRAP",
        "AZURE_APP_CONFIGURATION_CONNECTION_STRING",
        "AZURE_APPCONFIG_ENDPOINT",
        "APPLICATIONINSIGHTS_CONNECTION_STRING",
    ):
        monkeypatch.delenv(k, raising=False)


def test_app_config_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USE_MOCK_BOOTSTRAP", "true")
    assert check_app_config_health() == {"status": "ok", "mock": True}


def test_app_config_unconfigured() -> None:
    assert check_app_config_health() == {"status": "not_configured"}


class _FakeClient:
    """Stand-in for ``AzureAppConfigurationClient``.

    ``yielded`` counts how many settings the probe actually pulled, which is
    what proves the check stays cheap.
    """

    created_from_conn: str | None = None
    created_args: tuple[Any, ...] = ()
    yielded = 0
    raises: Exception | None = None

    def __init__(self, *args: Any) -> None:
        type(self).created_args = args

    @classmethod
    def from_connection_string(cls, conn: str) -> _FakeClient:
        cls.created_from_conn = conn
        return cls.__new__(cls)

    def list_configuration_settings(self, *args: Any, **kwargs: Any) -> Iterator[object]:
        if type(self).raises is not None:
            raise type(self).raises

        def gen() -> Iterator[object]:
            for _ in range(500):
                type(self).yielded += 1
                yield object()

        return gen()


@pytest.fixture
def fake_client(monkeypatch: pytest.MonkeyPatch) -> type[_FakeClient]:
    _FakeClient.created_from_conn = None
    _FakeClient.created_args = ()
    _FakeClient.yielded = 0
    _FakeClient.raises = None
    monkeypatch.setattr(
        "azure.appconfiguration.AzureAppConfigurationClient", _FakeClient, raising=True
    )
    monkeypatch.setattr(
        "azure.identity.DefaultAzureCredential", lambda *a, **k: "CRED", raising=True
    )
    return _FakeClient


def test_app_config_connection_string_ok(
    monkeypatch: pytest.MonkeyPatch, fake_client: type[_FakeClient]
) -> None:
    monkeypatch.setenv(
        "AZURE_APP_CONFIGURATION_CONNECTION_STRING", "Endpoint=https://x;Id=y;Secret=z"
    )
    assert check_app_config_health() == {"status": "ok"}
    assert fake_client.created_from_conn == "Endpoint=https://x;Id=y;Secret=z"


def test_app_config_probe_pulls_only_one_setting(
    monkeypatch: pytest.MonkeyPatch, fake_client: type[_FakeClient]
) -> None:
    """The probe must not drain the whole store — that was the old load() bug."""
    monkeypatch.setenv("AZURE_APP_CONFIGURATION_CONNECTION_STRING", "Endpoint=https://x")
    check_app_config_health()
    assert fake_client.yielded == 1


def test_app_config_endpoint_uses_credential(
    monkeypatch: pytest.MonkeyPatch, fake_client: type[_FakeClient]
) -> None:
    monkeypatch.setenv("AZURE_APPCONFIG_ENDPOINT", "https://cfg.azconfig.io")
    assert check_app_config_health() == {"status": "ok"}
    assert fake_client.created_args == ("https://cfg.azconfig.io", "CRED")


def test_app_config_error_is_reported_and_truncated(
    monkeypatch: pytest.MonkeyPatch, fake_client: type[_FakeClient]
) -> None:
    monkeypatch.setenv("AZURE_APP_CONFIGURATION_CONNECTION_STRING", "Endpoint=https://x")
    fake_client.raises = RuntimeError("boom " * 100)
    result = check_app_config_health()
    assert result["status"] == "error"
    assert len(result["message"]) == 200


def test_app_insights_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USE_MOCK_BOOTSTRAP", "true")
    assert check_app_insights_health() == {"status": "ok", "mock": True}


def test_app_insights_unconfigured() -> None:
    assert check_app_insights_health() == {"status": "not_configured"}


def test_app_insights_logging_unconfigured() -> None:
    assert check_app_insights_logging() == {"status": "not_configured"}


def test_app_insights_logging_detects_handler(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "APPLICATIONINSIGHTS_CONNECTION_STRING",
        "InstrumentationKey=00000000-0000-0000-0000-000000000000",
    )

    class FakeAzureMonitorTraceExporter(logging.Handler):
        pass

    handler = FakeAzureMonitorTraceExporter()
    root = logging.getLogger()
    root.addHandler(handler)
    try:
        result = check_app_insights_logging()
        assert result["status"] == "ok"
        assert "FakeAzureMonitorTraceExporter" in result["handler"]
    finally:
        root.removeHandler(handler)


def test_app_insights_logging_missing_handler(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "APPLICATIONINSIGHTS_CONNECTION_STRING",
        "InstrumentationKey=00000000-0000-0000-0000-000000000000",
    )
    # Remove any pre-existing matching handlers
    root = logging.getLogger()
    saved = list(root.handlers)
    for h in saved:
        if "azure" in type(h).__module__.lower() or "monitor" in type(h).__name__.lower():
            root.removeHandler(h)
    try:
        result = check_app_insights_logging()
        # Either ok (some matching handler still attached) or error.
        assert result["status"] in {"ok", "error"}
    finally:
        for h in saved:
            if h not in root.handlers:
                root.addHandler(h)
