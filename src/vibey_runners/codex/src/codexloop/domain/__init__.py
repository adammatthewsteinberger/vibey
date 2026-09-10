# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Pure domain layer — stdlib only."""

from codexloop.domain.error_codes import ErrorClass, classify_code
from codexloop.domain.errors import (
    AuthError,
    BudgetExceeded,
    CapacityError,
    CodexBinaryError,
    CodexloopError,
    CodexProtocolError,
    ConfigurationError,
    WaitDeadlineExceeded,
)

__all__ = [
    "AuthError",
    "BudgetExceeded",
    "CapacityError",
    "CodexBinaryError",
    "CodexloopError",
    "CodexProtocolError",
    "ConfigurationError",
    "ErrorClass",
    "WaitDeadlineExceeded",
    "classify_code",
]
