# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Notifier — tells a human something needs attention. The default adapter
writes to stderr, deliberately loud, matching the legacy script's
print_auto_selected_session_warning() banner style — a message a human is
meant to actually notice, not a routine log line."""

from __future__ import annotations

import sys


class StderrNotifier:
    def notify(self, message: str) -> None:
        bar = "!" * min(78, max(20, len(message)))
        print(bar, file=sys.stderr)
        print(message, file=sys.stderr)
        print(bar, file=sys.stderr)
