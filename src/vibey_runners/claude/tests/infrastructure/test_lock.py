# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for infrastructure/lock.py — FileSessionLock adapter."""

from __future__ import annotations

import os
from pathlib import Path

from claudeloop.infrastructure.lock import FileSessionLock


def test_lock_acquire_success(tmp_path: Path) -> None:
    """acquire returns True when lock is successfully acquired."""
    lock_dir = tmp_path / "locks"
    lock = FileSessionLock(lock_dir)
    assert lock.acquire("sess-123") is True
    # Lock file should exist
    assert (lock_dir / "sess-123.lock").is_file()


def test_lock_acquire_creates_directory(tmp_path: Path) -> None:
    """FileSessionLock creates lock directory if it doesn't exist."""
    lock_dir = tmp_path / "nested" / "locks"
    FileSessionLock(lock_dir)
    assert lock_dir.is_dir()


def test_lock_acquire_fails_when_already_held(tmp_path: Path) -> None:
    """acquire returns False when lock is already held."""
    lock_dir = tmp_path / "locks"
    lock1 = FileSessionLock(lock_dir)
    lock2 = FileSessionLock(lock_dir)

    assert lock1.acquire("sess-abc") is True
    assert lock2.acquire("sess-abc") is False


def test_lock_release_removes_file(tmp_path: Path) -> None:
    """release removes the lock file."""
    lock_dir = tmp_path / "locks"
    lock = FileSessionLock(lock_dir)
    lock.acquire("sess-xyz")
    lock_path = lock_dir / "sess-xyz.lock"
    assert lock_path.is_file()

    lock.release("sess-xyz")
    assert not lock_path.exists()


def test_lock_release_without_acquire(tmp_path: Path) -> None:
    """release is safe to call even if lock wasn't acquired."""
    lock_dir = tmp_path / "locks"
    lock = FileSessionLock(lock_dir)
    # Should not raise an exception
    lock.release("sess-nonexistent")


def test_lock_multiple_sessions_independently(tmp_path: Path) -> None:
    """Different session IDs can be locked independently."""
    lock_dir = tmp_path / "locks"
    lock = FileSessionLock(lock_dir)

    assert lock.acquire("sess-1") is True
    assert lock.acquire("sess-2") is True
    assert lock.acquire("sess-3") is True

    # All three lock files should exist
    assert (lock_dir / "sess-1.lock").is_file()
    assert (lock_dir / "sess-2.lock").is_file()
    assert (lock_dir / "sess-3.lock").is_file()


def test_lock_writes_pid_to_file(tmp_path: Path) -> None:
    """Lock file contains the process ID."""
    lock_dir = tmp_path / "locks"
    lock = FileSessionLock(lock_dir)
    lock.acquire("sess-pid")

    lock_path = lock_dir / "sess-pid.lock"
    content = lock_path.read_bytes()
    assert str(os.getpid()).encode() in content


def test_lock_reacquire_after_release(tmp_path: Path) -> None:
    """Lock can be acquired again after being released."""
    lock_dir = tmp_path / "locks"
    lock1 = FileSessionLock(lock_dir)
    lock2 = FileSessionLock(lock_dir)

    assert lock1.acquire("sess-reuse") is True
    lock1.release("sess-reuse")
    assert lock2.acquire("sess-reuse") is True


def test_lock_acquire_different_sessions_same_lock_object(tmp_path: Path) -> None:
    """Same lock object can hold locks for multiple sessions."""
    lock_dir = tmp_path / "locks"
    lock = FileSessionLock(lock_dir)

    assert lock.acquire("sess-a") is True
    assert lock.acquire("sess-b") is True
    assert lock.acquire("sess-c") is True

    lock.release("sess-a")
    lock.release("sess-b")
    lock.release("sess-c")


def test_lock_release_closes_fd(tmp_path: Path) -> None:
    """release closes the file descriptor."""
    lock_dir = tmp_path / "locks"
    lock = FileSessionLock(lock_dir)
    lock.acquire("sess-fd")

    # After release, we should be able to acquire again
    lock.release("sess-fd")
    assert lock.acquire("sess-fd") is True


def test_lock_path_uses_session_id(tmp_path: Path) -> None:
    """Lock file path is based on session ID."""
    lock_dir = tmp_path / "locks"
    lock = FileSessionLock(lock_dir)

    session_id = "my-test-session"
    lock.acquire(session_id)
    expected_path = lock_dir / f"{session_id}.lock"
    assert expected_path.is_file()


def test_lock_release_handles_missing_file(tmp_path: Path) -> None:
    """release handles case where lock file was manually deleted."""
    lock_dir = tmp_path / "locks"
    lock = FileSessionLock(lock_dir)
    lock.acquire("sess-deleted")

    # Manually delete the file
    lock_path = lock_dir / "sess-deleted.lock"
    lock_path.unlink()

    # Should not raise an exception
    lock.release("sess-deleted")


def test_lock_multiple_instances_same_directory(tmp_path: Path) -> None:
    """Multiple lock instances using same directory respect each other's locks."""
    lock_dir = tmp_path / "locks"
    lock1 = FileSessionLock(lock_dir)
    lock2 = FileSessionLock(lock_dir)
    lock3 = FileSessionLock(lock_dir)

    assert lock1.acquire("shared-sess") is True
    assert lock2.acquire("shared-sess") is False
    assert lock3.acquire("shared-sess") is False

    lock1.release("shared-sess")

    assert lock2.acquire("shared-sess") is True
    assert lock3.acquire("shared-sess") is False
