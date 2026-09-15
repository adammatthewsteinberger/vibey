"""
Interface for Enhanced Config Repository.

Defines contract for accessing configuration from Azure App Configuration,
environment variables, and Key Vault secrets.
"""

from abc import ABC, abstractmethod
from typing import Any


class EnhancedConfigRepositoryInterface(ABC):
    """
    Abstract interface for enhanced configuration repository operations.

    This interface defines all configuration access operations for integration with
    Azure App Configuration, Key Vault, and environment variables following a
    hierarchical precedence model.

    Configuration Precedence (highest to lowest):
    1. Environment variables (os.environ)
    2. Azure App Configuration
    3. Key Vault secrets (via secrets repository)
    4. Default values

    Benefits:
    - Abstracts configuration storage implementation details
    - Enables dependency injection and testing with mocks
    - Provides clear contract for configuration access
    - Supports multiple backends with transparent fallback
    """

    @abstractmethod
    def get_value(self, key: str, default: str | None = None) -> str | None:
        """
        Get a configuration value with hierarchical lookup.

        Args:
            key: Configuration key name
            default: Default value if key not found

        Returns:
            Optional[str]: Configuration value or default

        Raises:
            ConfigurationError: If configuration access fails
        """
        pass

    @abstractmethod
    def get_secret_value(self, key: str, default: str | None = None) -> str | None:
        """
        Get a secret value from Key Vault.

        This method specifically targets secrets and bypasses the standard
        configuration hierarchy to directly access Key Vault.

        Args:
            key: Secret key name
            default: Default value if secret not found

        Returns:
            Optional[str]: Secret value or default

        Raises:
            SecretAccessError: If secret retrieval fails
        """
        pass

    @abstractmethod
    def get_all_values(self) -> dict[str, str]:
        """
        Get all configuration values from all sources.

        Returns:
            Dict[str, str]: All configuration key-value pairs

        Raises:
            ConfigurationError: If configuration access fails
        """
        pass

    @abstractmethod
    def load_to_environ(self) -> int:
        """
        Load all configuration values into os.environ.

        This method loads all configuration from App Config and Key Vault
        into environment variables for transparent application access.

        Returns:
            int: Number of new values added to os.environ (excludes skipped values)

        Raises:
            ConfigurationError: If loading fails
        """
        pass

    @abstractmethod
    def refresh(self) -> None:
        """
        Refresh configuration from all sources.

        This method reloads configuration from App Configuration and
        Key Vault to pick up any changes.

        Raises:
            ConfigurationError: If refresh fails
        """
        pass

    @abstractmethod
    def get_repository_metrics(self) -> dict[str, Any]:
        """
        Get metrics about the configuration repository.

        Returns:
            Dict[str, Any]: Metrics including source counts, cache hits, etc.
        """
        pass

    @abstractmethod
    def is_app_config_available(self) -> bool:
        """
        Check if Azure App Configuration is available and accessible.

        Returns:
            bool: True if App Config is accessible, False otherwise
        """
        pass

    @abstractmethod
    def is_key_vault_available(self) -> bool:
        """
        Check if Azure Key Vault is available and accessible.

        Returns:
            bool: True if Key Vault is accessible, False otherwise
        """
        pass
