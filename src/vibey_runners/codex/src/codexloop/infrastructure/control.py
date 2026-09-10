# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""File-based RunControl — operator commands land in inbox/*.json."""

from __future__ import annotations

import json
import time
from collections.abc import Sequence
from pathlib import Path

from codexloop.application.ports import Logger, RunControl
from codexloop.domain.control import ControlCommand, parse_control
from codexloop.domain.errors import ConfigurationError
from codexloop.infrastructure.logging import StructlogAppLogger


class FileRunControl:
    """Poll inbox JSON files; archive successes; quarantine malformed."""

    def __init__(self, inbox: Path, *, logger: Logger | None = None) -> None:
        self._inbox = inbox
        self._archive = inbox / "archive"
        self._quarantine = inbox / "quarantine"
        self._logger: Logger = logger if logger is not None else StructlogAppLogger()
        self._inbox.mkdir(parents=True, exist_ok=True)
        self._archive.mkdir(parents=True, exist_ok=True)
        self._quarantine.mkdir(parents=True, exist_ok=True)

    def enqueue(self, command: ControlCommand) -> Path:
        payload = command.to_dict()
        kind = str(payload.get("kind", "command"))
        name = f"{time.time_ns()}-{kind}.json"
        path = self._inbox / name
        path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
        return path

    def poll(self) -> Sequence[ControlCommand]:
        files = sorted(
            path
            for path in self._inbox.iterdir()
            if path.is_file() and path.suffix == ".json" and path.name.endswith(".json")
        )
        commands: list[ControlCommand] = []
        for path in files:
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(raw, dict):
                    raise ConfigurationError("control payload must be an object")
                command = parse_control(raw)
            except (
                OSError,
                json.JSONDecodeError,
                ConfigurationError,
                TypeError,
                ValueError,
            ) as exc:
                self._quarantine_file(path, exc)
                continue
            dest = self._archive / path.name
            path.replace(dest)
            commands.append(command)
        return commands

    def _quarantine_file(self, path: Path, exc: BaseException) -> None:
        dest = self._quarantine / path.name
        try:
            path.replace(dest)
        except OSError:  # pragma: no cover — leave in place if move fails
            dest = path
        self._logger.warning(
            "control.quarantined",
            path=str(dest),
            error=str(exc),
        )


class CompositeRunControl:
    """Merge polls from several RunControl adapters (drain + inbox)."""

    def __init__(self, *controls: RunControl) -> None:
        self._controls = controls

    def poll(self) -> Sequence[ControlCommand]:
        commands: list[ControlCommand] = []
        for control in self._controls:
            commands.extend(control.poll())
        return commands


__all__ = ["CompositeRunControl", "FileRunControl"]
