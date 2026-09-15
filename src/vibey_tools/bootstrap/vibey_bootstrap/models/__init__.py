# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""
Custom exceptions for bootstrap operations.

This module defines exceptions for configuration, secrets, and bootstrap operations.
"""

from vibey_bootstrap.models.exceptions import ConfigurationError, KeyVaultError, RepositoryError

__all__ = [
    "RepositoryError",
    "ConfigurationError",
    "KeyVaultError",
]
