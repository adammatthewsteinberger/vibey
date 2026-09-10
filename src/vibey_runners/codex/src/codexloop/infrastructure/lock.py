# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""SessionLock — advisory file lock keyed by thread id, with stale-pid break."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from codexloop.application.ports import Logger

_LOG = logging.getLogger(__name__)


class AdvisoryFileLock:
    def __init__(self, directory: Path, *, logger: Logger | None = None) -> None:
        self._directory = directory
        self._directory.mkdir(parents=True, exist_ok=True)
        self._logger = logger

    def _path(self, thread_id: str) -> Path:
        return self._directory / f"{thread_id}.lock"

    def acquire(self, thread_id: str) -> bool:
        path = self._path(thread_id)
        if path.is_file():
            pid = _read_pid(path)
            if pid is None or _pid_alive(pid):
                # Empty/unreadable/unparseable lockfile, or live/unknown pid: held.
                return False
            self._log_stale(thread_id, pid, "process is dead")
            path.unlink(missing_ok=True)
        return _publish_lock(path)

    def release(self, thread_id: str) -> None:
        self._path(thread_id).unlink(missing_ok=True)

    def _log_stale(self, thread_id: str, pid: int | None, reason: str) -> None:
        if self._logger is not None:
            self._logger.warning(
                "stale_lock_broken",
                thread_id=thread_id,
                pid=pid,
                reason=reason,
            )
            return
        _LOG.warning(
            "stale lock broken for thread %s (pid=%s): %s",
            thread_id,
            pid,
            reason,
        )


def _publish_lock(path: Path) -> bool:
    """Atomically publish a non-empty lockfile (write pid, then link into place)."""
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        tmp.write_text(f"{os.getpid()}\n", encoding="utf-8")
        os.link(str(tmp), str(path))
    except FileExistsError:
        return False
    except OSError:
        return False
    finally:
        tmp.unlink(missing_ok=True)
    return True


def _read_pid(path: Path) -> int | None:
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        # Unknown errno: treat as alive so we never break a maybe-held lock.
        return True
    return True
