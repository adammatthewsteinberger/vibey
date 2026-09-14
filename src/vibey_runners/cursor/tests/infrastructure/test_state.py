# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path

from cursorloop.infrastructure.state import FileRunStateStore


def test_save_and_load_round_trip(tmp_path: Path) -> None:
    store = FileRunStateStore(tmp_path / ".cursorloop")
    store.save("run-1", {"phase": "RUNNING", "hooks_existed": True})
    loaded = store.load("run-1")
    assert loaded == {"phase": "RUNNING", "hooks_existed": True}


def test_load_missing_returns_none(tmp_path: Path) -> None:
    store = FileRunStateStore(tmp_path / ".cursorloop")
    assert store.load("missing") is None


def test_save_is_atomic_write_then_rename(tmp_path: Path) -> None:
    store = FileRunStateStore(tmp_path / ".cursorloop")
    store.save("run-2", {"ok": True})
    path = tmp_path / ".cursorloop" / "run-2.json"
    assert path.is_file()
    assert not path.with_suffix(".json.tmp").exists()
