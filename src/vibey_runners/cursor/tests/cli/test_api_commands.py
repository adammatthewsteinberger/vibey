# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from unittest.mock import patch

import httpx
from typer.testing import CliRunner

from cursorloop.cli.app import app

runner = CliRunner()


def test_cloud_help_marks_partial() -> None:
    result = runner.invoke(app, ["cloud", "--help"])
    assert result.exit_code == 0
    assert "PARTIAL" in result.stdout or "partial" in result.stdout.lower()


def test_cloud_status_explains_deferral() -> None:
    result = runner.invoke(app, ["cloud", "status"])
    assert result.exit_code == 0
    assert "ADR-0006" in result.stdout or "deferred" in result.stdout.lower()


def test_cloud_me_invokes_http(monkeypatch: object) -> None:
    monkeypatch.setenv("CURSOR_API_KEY", "test-key")  # type: ignore[attr-defined]

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer test-key"
        assert request.url.path == "/v1/me"
        return httpx.Response(200, json={"user_email": "a@b.c", "api_key": "secret"})

    transport = httpx.MockTransport(handler)
    client = httpx.Client(base_url="https://api.cursor.com", transport=transport)

    with patch("cursorloop.infrastructure.api.binder.CloudAgentsGateway") as gateway_cls:
        instance = gateway_cls.return_value.__enter__.return_value
        instance.invoke.return_value = {"user_email": "a@b.c", "api_key": "***"}
        result = runner.invoke(app, ["cloud", "me"])
    assert result.exit_code == 0
    assert "a@b.c" in result.stdout
    del client


def test_cloud_create_requires_body(monkeypatch: object) -> None:
    monkeypatch.setenv("CURSOR_API_KEY", "test-key")  # type: ignore[attr-defined]
    result = runner.invoke(app, ["cloud", "create"])
    assert result.exit_code == 2


def test_cloud_me_requires_api_key(monkeypatch: object) -> None:
    monkeypatch.delenv("CURSOR_API_KEY", raising=False)  # type: ignore[attr-defined]
    result = runner.invoke(app, ["cloud", "me"])
    assert result.exit_code == 1
