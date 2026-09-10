# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Exercise generated Typer command callbacks via CliRunner."""

from __future__ import annotations

from typing import Any

import pytest
from typer.testing import CliRunner

from codexloop.infrastructure.api.binder import build_api_typer_app
from codexloop.infrastructure.api.gateway import OpenAIApiGateway


class _FakeGateway(OpenAIApiGateway):
    def invoke_and_print(self, method_path: str, **options: Any) -> str:
        del options
        return f"ok:{method_path}"


def test_generated_command_invokes_gateway() -> None:
    app = build_api_typer_app(gateway=_FakeGateway())
    runner = CliRunner()
    result = runner.invoke(app, ["models", "list"])
    assert result.exit_code == 0, result.output
    assert "ok:models.list" in result.output


def test_unknown_provider_rejected() -> None:
    app = build_api_typer_app(gateway=_FakeGateway())
    runner = CliRunner()
    result = runner.invoke(app, ["--provider", "nope", "models", "list"])
    assert result.exit_code != 0


def test_gateway_error_maps_to_exit_2(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Boom(OpenAIApiGateway):
        def invoke_and_print(self, method_path: str, **options: Any) -> str:
            del method_path, options
            raise ValueError("bad request body")

    app = build_api_typer_app(gateway=_Boom())
    runner = CliRunner()
    result = runner.invoke(app, ["models", "list", "--json", "{}"])
    assert result.exit_code == 2
    assert "bad request body" in result.output
