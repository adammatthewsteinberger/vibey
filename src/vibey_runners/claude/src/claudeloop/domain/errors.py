# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Domain-level error hierarchy. Pure — carries no I/O state."""

from __future__ import annotations


class AutoclaudeError(Exception):
    """Base class for every error raised by claudeloop's own logic."""


class InvalidPlanError(AutoclaudeError):
    """Raised when a work plan file cannot be parsed into work items."""


class InvalidSessionSelectorError(AutoclaudeError):
    """Raised when a session selector is malformed or ambiguous."""


class BudgetExceededError(AutoclaudeError):
    """Raised when a run exceeds its configured turn, dollar, or wall-clock budget."""


class AuthenticationFailedError(AutoclaudeError):
    """Raised when the agent gateway reports a terminal authentication failure.

    Never retryable — the run loop must abort rather than wait.
    """
