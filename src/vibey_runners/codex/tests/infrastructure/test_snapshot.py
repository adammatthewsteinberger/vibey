# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for workspace snapshot helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from codexloop.infrastructure.snapshot import create_snapshot, restore_snapshot


def test_create_and_restore_snapshot(tmp_path: Path) -> None:
    cwd = tmp_path / "ws"
    cwd.mkdir()
    (cwd / "a.txt").write_text("one", encoding="utf-8")
    nested = cwd / "pkg"
    nested.mkdir()
    (nested / "b.txt").write_text("two", encoding="utf-8")
    (cwd / ".codexloop").mkdir()
    (cwd / ".codexloop" / "secret").write_text("nope", encoding="utf-8")
    (cwd / ".git").mkdir()

    dest = tmp_path / "snap"
    create_snapshot(cwd=cwd, dest=dest)
    assert (dest / "a.txt").read_text(encoding="utf-8") == "one"
    assert (dest / "pkg" / "b.txt").read_text(encoding="utf-8") == "two"
    assert not (dest / ".codexloop").exists()
    assert not (dest / ".git").exists()

    other = tmp_path / "restore"
    other.mkdir()
    (other / "pkg").mkdir()
    (other / "pkg" / "old.txt").write_text("old", encoding="utf-8")
    restore_snapshot(snapshot=dest, cwd=other)
    assert (other / "a.txt").read_text(encoding="utf-8") == "one"
    assert (other / "pkg" / "b.txt").read_text(encoding="utf-8") == "two"


def test_restore_missing_snapshot(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="snapshot not found"):
        restore_snapshot(snapshot=tmp_path / "missing", cwd=tmp_path)
