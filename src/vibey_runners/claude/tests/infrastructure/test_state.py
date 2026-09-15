# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for infrastructure/state.py — FileRunStateStore."""

from __future__ import annotations

from pathlib import Path

from claudeloop.infrastructure.state import FileRunStateStore


def test_creates_directory(tmp_path: Path) -> None:
    directory = tmp_path / "state"
    FileRunStateStore(directory)
    assert directory.is_dir()


def test_save_and_load(tmp_path: Path) -> None:
    store = FileRunStateStore(tmp_path / "state")
    store.save("run-1", {"phase": "running", "attempt": 1})
    loaded = store.load("run-1")
    assert loaded is not None
    assert loaded["phase"] == "running"
    assert loaded["attempt"] == 1


def test_load_missing_returns_none(tmp_path: Path) -> None:
    store = FileRunStateStore(tmp_path / "state")
    assert store.load("nonexistent") is None


def test_save_overwrites(tmp_path: Path) -> None:
    store = FileRunStateStore(tmp_path / "state")
    store.save("run-1", {"phase": "running"})
    store.save("run-1", {"phase": "done"})
    loaded = store.load("run-1")
    assert loaded is not None
    assert loaded["phase"] == "done"


def test_multiple_runs(tmp_path: Path) -> None:
    store = FileRunStateStore(tmp_path / "state")
    store.save("run-a", {"name": "a"})
    store.save("run-b", {"name": "b"})
    assert store.load("run-a")["name"] == "a"
    assert store.load("run-b")["name"] == "b"


def test_save_with_non_serializable_uses_default_str(tmp_path: Path) -> None:
    from datetime import datetime, timezone

    store = FileRunStateStore(tmp_path / "state")
    store.save("run-1", {"ts": datetime.now(timezone.utc)})
    loaded = store.load("run-1")
    assert loaded is not None
    assert isinstance(loaded["ts"], str)
