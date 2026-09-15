# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for the run-state bus helpers."""

from __future__ import annotations

from pathlib import Path

from codexloop.infrastructure.state_bus import read_state, watch_state


def test_read_state_missing(tmp_path: Path) -> None:
    assert read_state(tmp_path / "nope.json") == {}


def test_read_state_valid(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    path.write_text('{"phase":"waiting"}', encoding="utf-8")
    assert watch_state(path) == {"phase": "waiting"}


def test_read_state_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    path.write_text("{not-json", encoding="utf-8")
    assert read_state(path) == {}


def test_read_state_non_object(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    path.write_text("[1,2]", encoding="utf-8")
    assert read_state(path) == {}
