# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""ProgressReporter — human-readable console output for an interactive
terminal watching a run."""

from __future__ import annotations

from datetime import datetime


class ConsoleProgressReporter:
    def turn_sent(self, *, attempt: int) -> None:
        print(f"=== attempt {attempt} ===", flush=True)

    def waiting(self, *, reason: str, until: datetime) -> None:
        print(f"Waiting ({reason}) until {until.isoformat()}...", flush=True)

    def finished(self, *, success: bool, reason: str) -> None:
        status = "Done" if success else "Failed"
        print(f"{status}: {reason}", flush=True)
