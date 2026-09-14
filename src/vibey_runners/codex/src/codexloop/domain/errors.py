# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Domain exception hierarchy for codexloop."""

from __future__ import annotations


class CodexloopError(Exception):
    """Base error for all codexloop domain failures."""


class ConfigurationError(CodexloopError):
    """Invalid or incomplete configuration."""


class CapacityError(CodexloopError):
    """Capacity, quota, or rate-limit related failure."""


class AuthError(CodexloopError):
    """Authentication or credential failure."""


class CodexBinaryError(CodexloopError):
    """Codex CLI binary missing, broken, or unusable."""


class CodexProtocolError(CodexloopError):
    """Malformed or unexpected Codex protocol / event stream."""


class BudgetExceeded(CodexloopError):
    """Operator-configured budget or spend limit reached."""


class WaitDeadlineExceeded(CodexloopError):
    """Wait / probe loop hit the configured max-wait deadline."""
