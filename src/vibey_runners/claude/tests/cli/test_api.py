# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""CLI tests for the generated ``claudeloop api`` namespace."""

from __future__ import annotations

import os
import subprocess
import sys


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "NO_COLOR": "1", "TERM": "dumb"}
    return subprocess.run(
        [sys.executable, "-m", "claudeloop.cli.app", *args],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_api_models_list_help_renders() -> None:
    result = _run("api", "models", "list", "--help")
    assert result.returncode == 0
    assert "--json" in result.stdout
    assert "models.list" in result.stdout or "SDK" in result.stdout
