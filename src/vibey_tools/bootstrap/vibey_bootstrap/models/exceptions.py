"""
Custom exceptions for Azure bootstrap operations.

This module defines exceptions for configuration and Key Vault error handling.
"""


class RepositoryError(Exception):
    """Base exception for repository errors."""

    pass


class ConfigurationError(RepositoryError):
    """
    Exception raised when configuration loading or access fails.

    This exception is raised when:
    - Azure App Configuration connection fails
    - Configuration values are missing or invalid
    - Configuration refresh operations fail
    - Configuration loading encounters critical errors
    """

    pass


class KeyVaultError(RepositoryError):
    """
    Exception raised when Key Vault operations fail.

    This exception is raised when:
    - Key Vault connection or authentication fails
    - Secret retrieval operations fail
    - Key Vault access is denied or unavailable
    """

    pass
