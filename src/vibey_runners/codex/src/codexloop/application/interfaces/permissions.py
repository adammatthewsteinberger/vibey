# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Permission vocabulary shared across the seam, so vendor CLI flag strings
never leak up into the application layer."""

from __future__ import annotations

from enum import StrEnum


class PermissionMode(StrEnum):
    """Autonomy posture at the application boundary — not Codex CLI flag strings."""

    AUTONOMOUS = "autonomous"
    READ_ONLY = "read_only"
    FULL_ACCESS = "full_access"
