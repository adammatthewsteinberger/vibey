# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""End-to-end against the fake `codex` shim: markdown plan drives to Done."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
from typer.testing import CliRunner

from codexloop.cli.app import app

JSONL = Path(__file__).resolve().parents[1] / "fixtures" / "jsonl"
_RUNNER = CliRunner()


def test_markdown_plan_drives_to_done_exit_0(
    fake_codex_on_path: Path,
    configure_fake_codex: Callable[..., None],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_fake_codex(script=JSONL / "done_with_marker.jsonl", mode="stream")
    monkeypatch.chdir(tmp_path)
    plan = tmp_path / "plan.md"
    plan.write_text("- [ ] Add login\n", encoding="utf-8")
    result = _RUNNER.invoke(app, ["run", str(plan), "--max-turns", "3"])
    assert result.exit_code == 0, result.output
    assert "done" in result.output.lower()


def test_clarifying_question_plan_still_completes(
    fake_codex_on_path: Path,
    configure_fake_codex: Callable[..., None],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_fake_codex(script=JSONL / "done_with_marker.jsonl", mode="stream")
    monkeypatch.chdir(tmp_path)
    plan = tmp_path / "plan.md"
    plan.write_text(
        "Ask a clarifying question about the preferred framework before implementing.\n"
        "- [ ] Add login\n",
        encoding="utf-8",
    )
    result = _RUNNER.invoke(app, ["run", str(plan), "--max-turns", "3"])
    assert result.exit_code == 0, result.output
    assert "done" in result.output.lower()
