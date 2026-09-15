# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Advisory file lock: exclusive acquire, release, and stale-pid break."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from codexloop.infrastructure.lock import AdvisoryFileLock
from tests.application.fakes import FakeLogger

_DEAD_PID = 2_147_483_647


def test_second_acquire_on_same_thread_id_fails(tmp_path: Path) -> None:
    lock = AdvisoryFileLock(tmp_path)
    assert lock.acquire("thread-a") is True
    assert lock.acquire("thread-a") is False


def test_release_allows_reacquire(tmp_path: Path) -> None:
    lock = AdvisoryFileLock(tmp_path)
    assert lock.acquire("thread-a") is True
    lock.release("thread-a")
    assert lock.acquire("thread-a") is True


def test_stale_lock_from_dead_pid_is_broken_with_logged_reason(tmp_path: Path) -> None:
    logger = FakeLogger()
    lock = AdvisoryFileLock(tmp_path, logger=logger)
    (tmp_path / "thread-a.lock").write_text(f"{_DEAD_PID}\n", encoding="utf-8")
    assert lock.acquire("thread-a") is True
    reasons = [event for _level, event, _detail in logger.events]
    assert "stale_lock_broken" in reasons
    detail = next(kwargs for _level, event, kwargs in logger.events if event == "stale_lock_broken")
    assert detail["pid"] == _DEAD_PID
    assert "dead" in str(detail["reason"]).lower() or "not running" in str(detail["reason"]).lower()


def test_empty_lockfile_is_not_stolen(tmp_path: Path) -> None:
    lock = AdvisoryFileLock(tmp_path)
    (tmp_path / "thread-a.lock").write_text("", encoding="utf-8")
    assert lock.acquire("thread-a") is False
    assert (tmp_path / "thread-a.lock").is_file()


def test_invalid_lockfile_contents_are_not_stolen(tmp_path: Path) -> None:
    lock = AdvisoryFileLock(tmp_path)
    (tmp_path / "thread-a.lock").write_text("not-a-pid\n", encoding="utf-8")
    assert lock.acquire("thread-a") is False
    assert (tmp_path / "thread-a.lock").is_file()


def test_only_known_dead_pid_lock_is_broken(tmp_path: Path) -> None:
    lock = AdvisoryFileLock(tmp_path)
    live_path = tmp_path / "live.lock"
    live_path.write_text(f"{os.getpid()}\n", encoding="utf-8")
    assert lock.acquire("live") is False
    assert live_path.is_file()

    dead_path = tmp_path / "dead.lock"
    dead_path.write_text(f"{_DEAD_PID}\n", encoding="utf-8")
    assert lock.acquire("dead") is True
    assert dead_path.read_text(encoding="utf-8").strip() == str(os.getpid())


def test_zero_pid_is_treated_as_dead_and_broken(tmp_path: Path) -> None:
    lock = AdvisoryFileLock(tmp_path)
    (tmp_path / "zero.lock").write_text("0\n", encoding="utf-8")
    assert lock.acquire("zero") is True


def test_permission_error_on_kill_treats_pid_as_alive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lock = AdvisoryFileLock(tmp_path)
    (tmp_path / "held.lock").write_text("12345\n", encoding="utf-8")

    def _deny(pid: int, sig: int) -> None:
        del pid, sig
        raise PermissionError

    monkeypatch.setattr("codexloop.infrastructure.lock.os.kill", _deny)
    assert lock.acquire("held") is False
    assert (tmp_path / "held.lock").is_file()


def test_unknown_oserror_on_kill_treats_pid_as_alive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lock = AdvisoryFileLock(tmp_path)
    (tmp_path / "held.lock").write_text("12345\n", encoding="utf-8")

    def _unknown(pid: int, sig: int) -> None:
        del pid, sig
        raise OSError("unknown errno")

    monkeypatch.setattr("codexloop.infrastructure.lock.os.kill", _unknown)
    assert lock.acquire("held") is False


def test_publish_file_exists_error_is_not_acquired(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lock = AdvisoryFileLock(tmp_path)

    def _exists(src: str, dst: str) -> None:
        del src, dst
        raise FileExistsError

    monkeypatch.setattr("codexloop.infrastructure.lock.os.link", _exists)
    assert lock.acquire("race") is False


def test_publish_oserror_is_not_acquired(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    lock = AdvisoryFileLock(tmp_path)

    def _fail(src: str, dst: str) -> None:
        del src, dst
        raise OSError("disk full")

    monkeypatch.setattr("codexloop.infrastructure.lock.os.link", _fail)
    assert lock.acquire("io") is False
