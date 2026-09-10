# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Notifier — run a configured command, or record a no-op when unset."""

from __future__ import annotations

import shlex
import subprocess  # nosec B404 — argv list from operator config, never shell=True
from collections.abc import Sequence

from codexloop.infrastructure.redact import redact_string


class CommandNotifier:
    def __init__(self, command: str | Sequence[str] | None = None) -> None:
        self._command = command
        self.noop_notifications: list[tuple[str, str]] = []

    def notify(self, title: str, body: str) -> None:
        safe_title = redact_string(title)
        safe_body = redact_string(body)
        if not self._command:
            self.noop_notifications.append((safe_title, safe_body))
            return
        argv = shlex.split(self._command) if isinstance(self._command, str) else list(self._command)
        subprocess.run(  # nosec B603 — no shell; operator-configured argv
            [*argv, safe_title, safe_body],
            check=False,
        )
