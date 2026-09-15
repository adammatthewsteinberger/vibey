"""
Secrets Repository implementation for Azure Key Vault integration.

Provides access to secrets from Azure Key Vault with fallback to environment variables.
"""

import logging
import os
from typing import Any

from .interfaces.secrets_repository_interface import SecretsRepositoryInterface

logger = logging.getLogger(__name__)


class SecretsRepository(SecretsRepositoryInterface):
    """
    Implementation of secrets repository for Azure Key Vault.

    This repository provides access to secrets from Azure Key Vault with
    graceful fallback to environment variables when Key Vault is not available.

    Features:
    - Azure Key Vault integration (when available)
    - Environment variable fallback for local development
    - Caching for performance
    - Comprehensive logging and error handling

    Usage:
        # With Key Vault
        secrets_repo = SecretsRepository(vault_url="https://myvault.vault.azure.net/")
        db_password = secrets_repo.get_secret("database-password")

        # Without Key Vault (environment variables only)
        secrets_repo = SecretsRepository()
        db_password = secrets_repo.get_secret("DATABASE_PASSWORD")
    """

    def __init__(self, vault_url: str | None = None) -> None:
        """
        Initialize the secrets repository.

        Args:
            vault_url: Optional Azure Key Vault URL (e.g., "https://myvault.vault.azure.net/")
                      If not provided, uses AZURE_KEY_VAULT_URL from environment
        """
        self.vault_url = vault_url or os.getenv("AZURE_KEY_VAULT_URL")
        self._cache: dict[str, str] = {}
        self._key_vault_available = False
        self._secret_client: Any = None

        # Try to initialize Key Vault client
        if self.vault_url:
            try:
                from azure.identity import DefaultAzureCredential
                from azure.keyvault.secrets import SecretClient

                self._secret_client = SecretClient(
                    vault_url=self.vault_url, credential=DefaultAzureCredential()
                )
                self._key_vault_available = True
                logger.info(
                    "Azure Key Vault client initialized successfully",
                    extra={"vault_url": self.vault_url, "operation": "secrets_init"},
                )
            except ImportError:
                logger.warning(
                    "Azure Key Vault SDK not available, using environment variables only",
                    extra={"operation": "secrets_init"},
                )
                self._secret_client = None
            except Exception as e:
                logger.warning(
                    f"Failed to initialize Key Vault client: {e}, using environment variables",
                    extra={"error": str(e), "operation": "secrets_init"},
                )
                self._secret_client = None
        else:
            logger.info(
                "No Key Vault URL provided, using environment variables only",
                extra={"operation": "secrets_init"},
            )
            self._secret_client = None

    def get_secret(self, secret_name: str) -> str | None:
        """
        Retrieve a secret value by name.

        Lookup order:
        1. Cache (if previously retrieved)
        2. Azure Key Vault (if available)
        3. Environment variables (fallback)

        Args:
            secret_name: Name of the secret to retrieve

        Returns:
            Optional[str]: Secret value if found, None otherwise
        """
        # Check cache first
        if secret_name in self._cache:
            logger.debug(f"Secret '{secret_name}' found in cache")
            return self._cache[secret_name]

        # Try Key Vault if available
        if self._secret_client:
            try:
                secret = self._secret_client.get_secret(secret_name)
                secret_value: str = secret.value
                self._cache[secret_name] = secret_value
                logger.info(
                    f"Secret '{secret_name}' retrieved from Key Vault",
                    extra={"secret_name": secret_name, "operation": "get_secret"},
                )
                return secret_value
            except Exception as e:
                logger.warning(
                    f"Failed to retrieve secret '{secret_name}' from Key Vault: {e}",
                    extra={"secret_name": secret_name, "error": str(e), "operation": "get_secret"},
                )

        # Fallback to environment variables
        # Try both the original name and with underscores replaced by hyphens
        env_value = os.getenv(secret_name) or os.getenv(secret_name.replace("-", "_"))
        if env_value:
            self._cache[secret_name] = env_value
            logger.debug(
                f"Secret '{secret_name}' retrieved from environment variables",
                extra={"secret_name": secret_name, "operation": "get_secret"},
            )
            return env_value

        logger.warning(
            f"Secret '{secret_name}' not found in Key Vault or environment",
            extra={"secret_name": secret_name, "operation": "get_secret"},
        )
        return None

    def set_secret(self, secret_name: str, secret_value: str) -> bool:
        """
        Store a secret value (Key Vault only, not environment).

        Args:
            secret_name: Name of the secret
            secret_value: Value to store

        Returns:
            bool: True if successful, False otherwise
        """
        if not self._secret_client:
            logger.warning(
                "Cannot set secret without Key Vault client",
                extra={"secret_name": secret_name, "operation": "set_secret"},
            )
            return False

        try:
            self._secret_client.set_secret(secret_name, secret_value)
            self._cache[secret_name] = secret_value  # Update cache
            logger.info(
                f"Secret '{secret_name}' stored in Key Vault",
                extra={"secret_name": secret_name, "operation": "set_secret"},
            )
            return True
        except Exception as e:
            logger.error(
                f"Failed to set secret '{secret_name}': {e}",
                extra={"secret_name": secret_name, "error": str(e), "operation": "set_secret"},
            )
            return False

    def delete_secret(self, secret_name: str) -> bool:
        """
        Delete a secret from Key Vault.

        Args:
            secret_name: Name of the secret to delete

        Returns:
            bool: True if successful, False otherwise
        """
        if not self._secret_client:
            logger.warning(
                "Cannot delete secret without Key Vault client",
                extra={"secret_name": secret_name, "operation": "delete_secret"},
            )
            return False

        try:
            self._secret_client.begin_delete_secret(secret_name).wait()
            self._cache.pop(secret_name, None)  # Remove from cache
            logger.info(
                f"Secret '{secret_name}' deleted from Key Vault",
                extra={"secret_name": secret_name, "operation": "delete_secret"},
            )
            return True
        except Exception as e:
            logger.error(
                f"Failed to delete secret '{secret_name}': {e}",
                extra={"secret_name": secret_name, "error": str(e), "operation": "delete_secret"},
            )
            return False

    def list_secrets(self) -> dict[str, str]:
        """
        List all available secrets (names only for security).

        Returns:
            Dict[str, str]: Dictionary mapping secret names to metadata (not values)
        """
        secrets_metadata: dict[str, str] = {}

        if self._secret_client:
            try:
                properties = self._secret_client.list_properties_of_secrets()
                for prop in properties:
                    if prop.name is not None:
                        secrets_metadata[prop.name] = f"Key Vault (enabled: {prop.enabled})"
                logger.info(
                    f"Listed {len(secrets_metadata)} secrets from Key Vault",
                    extra={"count": len(secrets_metadata), "operation": "list_secrets"},
                )
            except Exception as e:
                logger.error(
                    f"Failed to list secrets from Key Vault: {e}",
                    extra={"error": str(e), "operation": "list_secrets"},
                )

        return secrets_metadata

    def is_available(self) -> bool:
        """
        Check if secrets repository is available and accessible.

        Returns:
            bool: True if Key Vault client is available, False otherwise
        """
        return self._key_vault_available

    def clear_cache(self) -> None:
        """Clear the secrets cache."""
        self._cache.clear()
        logger.debug("Secrets cache cleared", extra={"operation": "clear_cache"})
