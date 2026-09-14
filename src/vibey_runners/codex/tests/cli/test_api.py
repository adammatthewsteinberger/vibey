# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""CLI tests for the generated ``codexloop api`` namespace."""

from __future__ import annotations

import os
import subprocess
import sys


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "NO_COLOR": "1", "TERM": "dumb"}
    env.pop("OPENAI_API_KEY", None)
    return subprocess.run(
        [sys.executable, "-m", "codexloop.cli.app", *args],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_api_help_renders_without_credentials() -> None:
    result = _run("api", "--help")
    assert result.returncode == 0
    assert "provider" in result.stdout.lower() or "Generated" in result.stdout


def test_api_models_list_help_renders() -> None:
    result = _run("api", "models", "list", "--help")
    assert result.returncode == 0
    assert "--json" in result.stdout
    assert "models.list" in result.stdout or "SDK" in result.stdout


def test_api_chat_completions_create_help_renders() -> None:
    result = _run("api", "chat", "completions", "create", "--help")
    assert result.returncode == 0
    assert "--json" in result.stdout
