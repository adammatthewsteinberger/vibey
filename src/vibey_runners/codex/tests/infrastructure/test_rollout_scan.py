# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Scanning the Codex rollout directory for the newest session file.

These branches are covered by accident on a machine that has Codex installed
and a rollout directory to walk. A fresh runner has neither, so they are
exercised here against a tmp tree instead.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from codexloop.infrastructure.rollout import _newest_contained_jsonl


def _touch(path: Path, *, mtime: float) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}\n", encoding="utf-8")
    os.utime(path, (mtime, mtime))
    return path


def test_no_rollout_directory_yields_nothing(tmp_path: Path) -> None:
    assert _newest_contained_jsonl(tmp_path / "absent") is None


def test_non_jsonl_files_are_skipped(tmp_path: Path) -> None:
    """The directory holds more than session files; picking a README as the
    newest rollout would make the parse fail for a confusing reason."""
    _touch(tmp_path / "README.md", mtime=9_000)
    _touch(tmp_path / "notes.txt", mtime=9_000)
    assert _newest_contained_jsonl(tmp_path) is None


def test_the_newest_jsonl_wins_across_subdirectories(tmp_path: Path) -> None:
    _touch(tmp_path / "a" / "old.jsonl", mtime=1_000)
    newest = _touch(tmp_path / "b" / "c" / "new.jsonl", mtime=5_000)
    _touch(tmp_path / "ignored.md", mtime=9_000)

    assert _newest_contained_jsonl(tmp_path) == newest


def test_a_directory_symlink_is_not_descended(tmp_path: Path) -> None:
    """Following one would let a link out of the rollout directory decide which
    file is "newest", which is how a scanner reads something it should not."""
    outside = tmp_path / "outside"
    _touch(outside / "tempting.jsonl", mtime=9_000)
    root = tmp_path / "root"
    _touch(root / "real.jsonl", mtime=1_000)
    (root / "link").symlink_to(outside, target_is_directory=True)

    found = _newest_contained_jsonl(root)
    assert found is not None
    assert found.name == "real.jsonl"


def test_a_file_symlink_pointing_outside_is_refused(tmp_path: Path) -> None:
    outside = _touch(tmp_path / "outside" / "tempting.jsonl", mtime=9_000)
    root = tmp_path / "root"
    _touch(root / "real.jsonl", mtime=1_000)
    (root / "escape.jsonl").symlink_to(outside)

    found = _newest_contained_jsonl(root)
    assert found is not None
    assert found.name == "real.jsonl"


def test_an_older_sibling_does_not_displace_the_newest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The newest file is visited first, so every later one takes the "older,
    keep what we have" arm.

    os.walk is stubbed rather than trusted: it does not promise an order, so
    without pinning it this test would sometimes visit the newest file last and
    never exercise that arm at all.
    """
    newest = _touch(tmp_path / "newest.jsonl", mtime=5_000)
    older = _touch(tmp_path / "older.jsonl", mtime=2_000)
    oldest = _touch(tmp_path / "oldest.jsonl", mtime=1_000)

    monkeypatch.setattr(
        "codexloop.infrastructure.rollout.os.walk",
        lambda root, followlinks=False: iter(
            [(str(tmp_path), [], [newest.name, older.name, oldest.name])]
        ),
    )

    assert _newest_contained_jsonl(tmp_path) == newest
