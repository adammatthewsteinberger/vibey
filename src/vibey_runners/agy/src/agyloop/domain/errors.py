# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Domain-level error hierarchy. Pure — carries no I/O state."""

from __future__ import annotations


class AgyloopError(Exception):
    """Base class for every error raised by agyloop's own logic."""


class InvalidPlanError(AgyloopError):
    """Raised when a work plan file cannot be parsed into work items."""


class InvalidSessionSelectorError(AgyloopError):
    """Raised when a session selector is malformed or ambiguous."""


class BudgetExceededError(AgyloopError):
    """Raised when a run exceeds its configured turn, token, or estimate budget."""


class AuthenticationFailedError(AgyloopError):
    """Raised when the agent gateway reports a terminal authentication failure.

    Never retryable — the run loop must abort rather than wait.
    """


class AgentConfigError(AgyloopError):
    """Invalid agent configuration — a bug in our options/policy builder.

    Wraps vendor ``AntigravityValidationError`` so the port never leaks
    ``google.antigravity`` types.
    """


class UnsafeSkipPermissionsError(AgyloopError):
    """Raised when ``--unsafe-skip-permissions`` is refused.

    The opt-in maps to ``agy --dangerously-skip-permissions``, which must
    never combine with ``--sandbox`` (antigravity-cli#36), never run as
    root, and never run outside a git repo unless allowlisted.
    """
