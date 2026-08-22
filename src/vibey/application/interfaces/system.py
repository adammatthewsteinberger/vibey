# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Ambient effects the application needs faked -- currently just time."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable


@runtime_checkable
class Clock(Protocol):
    def now(self) -> datetime: ...
