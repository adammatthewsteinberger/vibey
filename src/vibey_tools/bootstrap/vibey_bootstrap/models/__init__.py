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
