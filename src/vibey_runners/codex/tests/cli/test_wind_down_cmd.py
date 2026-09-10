# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for the wind-down CLI command."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from codexloop.cli.app import app
from codexloop.domain.errors import ConfigurationError
from codexloop.infrastructure.rundir import RunDirectory, runs_root_for

_RUNNER = CliRunner()


def _invoke(*args: str) -> object:
    return _RUNNER.invoke(app, list(args))


def _seed_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> RunDirectory:
    monkeypatch.chdir(tmp_path)
    return RunDirectory.create(runs_root_for(tmp_path))


def test_wind_down_with_default_reason(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """wind-down without --reason defaults to 'operator request'."""
    rundir = _seed_run(tmp_path, monkeypatch)
    result = _invoke("wind-down")
    assert result.exit_code == 0
    files = list(rundir.inbox.glob("*.json"))
    assert len(files) == 1
    payload = json.loads(files[0].read_text(encoding="utf-8"))
    assert payload == {"kind": "wind_down", "reason": "operator request"}
    assert "queued wind-down" in result.output


def test_wind_down_with_explicit_reason(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """wind-down with --reason uses the provided reason."""
    rundir = _seed_run(tmp_path, monkeypatch)
    result = _invoke("wind-down", "--reason", "capacity exhausted")
    assert result.exit_code == 0
    files = list(rundir.inbox.glob("*.json"))
    assert len(files) == 1
    payload = json.loads(files[0].read_text(encoding="utf-8"))
    assert payload == {"kind": "wind_down", "reason": "capacity exhausted"}


def test_wind_down_configuration_error_exits_2(monkeypatch: pytest.MonkeyPatch) -> None:
    """ConfigurationError from enqueue raises typer.Exit(2)."""

    def boom(*_a: object, **_k: object) -> object:
        raise ConfigurationError("no run directory")

    monkeypatch.setattr("codexloop.cli.commands.wind_down_cmd.enqueue_run_control", boom)
    result = _invoke("wind-down")
    assert result.exit_code == 2
    assert "no run directory" in result.output


def test_wind_down_value_error_exits_2(monkeypatch: pytest.MonkeyPatch) -> None:
    """ValueError from enqueue raises typer.Exit(2)."""

    def boom(*_a: object, **_k: object) -> object:
        raise ValueError("invalid run_id format")

    monkeypatch.setattr("codexloop.cli.commands.wind_down_cmd.enqueue_run_control", boom)
    result = _invoke("wind-down", "--run-id", "bad-id")
    assert result.exit_code == 2
    assert "invalid run_id format" in result.output
