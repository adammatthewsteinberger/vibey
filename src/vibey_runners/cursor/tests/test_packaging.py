# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

import subprocess  # nosec B404 - fixed argv, no shell, test-only gate check
import sys
from pathlib import Path

import pytest

import cursorloop
import cursorloop.application
import cursorloop.cli
import cursorloop.domain
import cursorloop.infrastructure
from cursorloop.cli.app import main

SRC = Path(__file__).resolve().parents[1] / "src" / "cursorloop"


def test_version_is_exposed() -> None:
    assert cursorloop.__version__


def test_layer_packages_are_importable() -> None:
    assert cursorloop.domain.__name__ == "cursorloop.domain"
    assert cursorloop.application.__name__ == "cursorloop.application"
    assert cursorloop.infrastructure.__name__ == "cursorloop.infrastructure"
    assert cursorloop.cli.__name__ == "cursorloop.cli"


def test_no_anthropic_token_anywhere_in_src() -> None:
    """The 'no Anthropic dependency, ever' non-negotiable, checked as text as
    well as by import-linter: a string reference in a comment or an env-var
    lookup would slip past an import contract."""
    offenders: list[str] = []
    for path in SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for needle in ("anthropic", "ANTHROPIC_", "claude_agent_sdk", "CLAUDELOOP_"):
            if needle in text:
                offenders.append(f"{path.relative_to(SRC)}: {needle}")
    assert offenders == [], f"forbidden vendor references in src/: {offenders}"


def test_import_linter_contracts_pass() -> None:
    # import-linter 2.x registers `lint-imports` as a console script on
    # `importlinter.cli:lint_imports_command`. `python -m importlinter.cli`
    # has no `__main__` and would exit 0 without checking contracts.
    result = subprocess.run(  # nosec B603 - fixed argv, no shell
        [
            sys.executable,
            "-c",
            "from importlinter.cli import lint_imports; raise SystemExit(lint_imports())",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_cli_main_returns_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["cursorloop", "--version"])
    assert main() == 0
