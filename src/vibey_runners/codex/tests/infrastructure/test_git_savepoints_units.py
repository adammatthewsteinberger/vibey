# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Two helpers on the save-point store, tested directly.

Both are reached through git in the integration tests, and both were covered on
Linux and not on macOS -- the runner's TMPDIR is a symlink there, so path work
takes different arms. Calling them directly removes the platform from the
question entirely.
"""

from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest

from codexloop.domain.savepoint import SavePointRef
from codexloop.infrastructure.git_savepoints import GitSavePointStore


def _store(tmp_path: Path) -> GitSavePointStore:
    return GitSavePointStore(cwd=tmp_path, index_path=tmp_path / "savepoints.jsonl")


def _completed(returncode: int, stdout: str) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=["git"], returncode=returncode, stdout=stdout)


def test_staged_paths_splits_the_nul_separated_list(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """git -z separates with NUL and leaves a trailing one, so a naive split
    yields a phantom empty path."""
    store = _store(tmp_path)
    monkeypatch.setattr(store, "_run", lambda argv, check=False: _completed(0, "a.py\0dir/b.py\0"))
    assert store._staged_paths() == ("a.py", "dir/b.py")


@pytest.mark.parametrize(
    ("returncode", "stdout"), [(1, "a.py\0"), (0, "")], ids=["git-failed", "nothing-staged"]
)
def test_staged_paths_is_empty_when_there_is_nothing_to_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, returncode: int, stdout: str
) -> None:
    store = _store(tmp_path)
    monkeypatch.setattr(store, "_run", lambda argv, check=False: _completed(returncode, stdout))
    assert store._staged_paths() == ()


def _point(n: int) -> SavePointRef:
    return SavePointRef(
        n=n,
        ref=f"refs/codexloop/r/{n}",
        sha=f"{n:040d}",
        label="turn",
        at=datetime(2026, 8, 15, 12, 0, tzinfo=UTC),
    )


def test_resolving_an_unknown_name_says_so_rather_than_guessing(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="no save point matching"):
        _store(tmp_path)._resolve_target([_point(1)], "no-such-label")


def test_resolving_an_unknown_number_reports_the_number(tmp_path: Path) -> None:
    """A digit is unambiguous, so the message names it rather than quoting a
    string the operator did not type."""
    with pytest.raises(ValueError, match="no save point numbered 7"):
        _store(tmp_path)._resolve_target([_point(1)], "7")
