"""
Repository interfaces for Azure bootstrap library.

This module contains interface definitions for configuration and secrets repositories.
"""

from vibey_bootstrap.repositories.interfaces.enhanced_config_repository_interface import (
    EnhancedConfigRepositoryInterface,
)
from vibey_bootstrap.repositories.interfaces.secrets_repository_interface import (
    SecretsRepositoryInterface,
)

__all__ = [
    "EnhancedConfigRepositoryInterface",
    "SecretsRepositoryInterface",
]
