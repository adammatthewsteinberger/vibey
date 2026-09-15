# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Loud operator notifications — never block waiting for a human reply."""

from __future__ import annotations

import sys
from typing import TextIO


class StderrNotifier:
    """Print a hard-to-miss banner to stderr. Credits exhaustion must not hide."""

    def __init__(self, stream: TextIO | None = None) -> None:
        self._stream = stream if stream is not None else sys.stderr

    def notify(self, message: str) -> None:
        banner = (
            "\n"
            "****************************************************************\n"
            "*** AGYLOOP ALERT ***\n"
            f"{message}\n"
            "****************************************************************\n"
        )
        self._stream.write(banner)
        self._stream.flush()
