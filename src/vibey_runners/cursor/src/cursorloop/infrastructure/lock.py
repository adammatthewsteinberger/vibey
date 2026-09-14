# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""AgentLock — advisory exclusive create under ``.cursorloop/locks/``."""

from __future__ import annotations

import errno
import os
from pathlib import Path


class FileAgentLock:
    """Advisory lock keyed by agent id. Protects against two runners, not UI."""

    def __init__(self, directory: Path) -> None:
        self._directory = Path(directory)
        self._directory.mkdir(parents=True, exist_ok=True)
        self._held: dict[str, int] = {}

    def _path(self, agent_id: str) -> Path:
        safe = agent_id.replace("/", "_")
        return self._directory / f"{safe}.lock"

    def acquire(self, agent_id: str) -> bool:
        path = self._path(agent_id)
        try:
            fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            return False
        except OSError as exc:  # pragma: no cover - platform-dependent
            if exc.errno != errno.EEXIST:
                raise
            return False
        os.write(fd, str(os.getpid()).encode())
        self._held[agent_id] = fd
        return True

    def release(self, agent_id: str) -> None:
        fd = self._held.pop(agent_id, None)
        if fd is not None:
            os.close(fd)
        path = self._path(agent_id)
        if path.is_file():
            path.unlink()
