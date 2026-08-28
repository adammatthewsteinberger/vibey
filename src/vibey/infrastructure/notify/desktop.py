# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Desktop notification sender for interactive terminals."""

import asyncio
import sys
from collections.abc import Callable
from contextlib import suppress

from vibey.infrastructure.notify.events import NotificationEvent


class DesktopNotifier:
    def __init__(
        self,
        *,
        executor: Callable[[list[str]], bool] | None = None,
        platform_override: str | None = None,
    ) -> None:
        self._executor = executor
        self._platform = platform_override or sys.platform

    async def notify(self, event: NotificationEvent) -> bool:
        cmd = self._build_command(event)
        if not cmd:
            return False

        if self._executor is not None:
            return self._executor(cmd)

        with suppress(Exception):
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await asyncio.wait_for(proc.communicate(), timeout=5.0)
            return proc.returncode == 0
        return False

    def _build_command(self, event: NotificationEvent) -> list[str]:
        safe_msg = event.message.replace('"', '\\"')
        safe_title = f"vibey: {event.title}".replace('"', '\\"')

        if self._platform == "darwin":
            script = f'display notification "{safe_msg}" with title "{safe_title}"'
            return ["osascript", "-e", script]
        elif self._platform.startswith("linux"):
            return ["notify-send", safe_title, safe_msg]
        return []
