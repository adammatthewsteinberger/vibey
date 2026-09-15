"""
Enhanced Config Repository for hierarchical configuration management.

Provides unified access to configuration from Azure App Configuration,
environment variables, and Key Vault secrets with automatic precedence handling.

This implementation uses Azure App Configuration's built-in Key Vault reference
resolution, eliminating the need for separate direct Key Vault access in most cases.
"""

import logging
import os
from typing import Any

from .interfaces.enhanced_config_repository_interface import EnhancedConfigRepositoryInterface
from .interfaces.secrets_repository_interface import SecretsRepositoryInterface

logger = logging.getLogger(__name__)


class EnhancedConfigRepository(EnhancedConfigRepositoryInterface):
    """
    Enhanced configuration repository with hierarchical lookup.

    This repository provides unified configuration access with automatic precedence:
    1. Environment variables (highest priority)
    2. Azure App Configuration with automatic Key Vault reference resolution
    3. Key Vault secrets (via secrets repository, fallback only)
    4. Default values (lowest priority)

    Features:
    - Hierarchical configuration lookup
    - Azure App Configuration integration with built-in Key Vault resolution
    - Automatic Key Vault reference resolution when secrets are stored as references
    - Fallback to direct Key Vault access for non-referenced secrets
    - Automatic loading to os.environ
    - Configuration caching for performance
    - Comprehensive logging

    Key Vault Integration:
    - When secrets are stored in App Config as Key Vault references (JSON format),
      they are automatically resolved by the Azure SDK
    - Reference format: {"uri": "https://vault.vault.azure.net/secrets/secretname"}
    - Requires Managed Identity with "App Configuration Data Reader" and
      "Key Vault Secrets User" RBAC roles

    Usage:
        # With App Config (Key Vault references auto-resolved)
        config_repo = EnhancedConfigRepository(
            app_config_connection_string="...",
            auto_load_to_environ=True
        )

        # Without App Config (environment only)
        config_repo = EnhancedConfigRepository()
        db_host = config_repo.get_value("DATABASE_HOST", "localhost")
    """

    def __init__(
        self,
        app_config_connection_string: str | None = None,
        secrets_repository: SecretsRepositoryInterface | None = None,
        auto_load_to_environ: bool = False,
    ) -> None:
        """
        Initialize the enhanced configuration repository.

        Args:
            app_config_connection_string: Azure App Configuration connection string
            secrets_repository: Optional secrets repository for direct Key Vault fallback
            auto_load_to_environ: If True, automatically load configs to os.environ on init
        """
        self.app_config_connection_string = app_config_connection_string or os.getenv(
            "AZURE_APP_CONFIGURATION_CONNECTION_STRING"
        )
        self.secrets_repository = secrets_repository
        self._cache: dict[str, str] = {}
        self._app_config_available = False
        self._config_provider = None

        # Try to initialize App Configuration provider with Key Vault resolution
        if self.app_config_connection_string:
            try:
                from azure.appconfiguration.provider import load
                from azure.identity import (
                    AzureCliCredential,
                    ChainedTokenCredential,
                    EnvironmentCredential,
                    ManagedIdentityCredential,
                )

                # Multi-environment credential chain for Key Vault reference resolution:
                # 1. EnvironmentCredential - Service principal for local dev (AZURE_CLIENT_ID, etc.)
                #    - additionally_allowed_tenants=["*"] allows cross-tenant authentication for Key Vault
                # 2. ManagedIdentityCredential - Azure Functions/App Service with managed identity (production)
                # 3. AzureCliCredential - Fallback for local development with `az login`
                # Order matters: EnvironmentCredential first ensures local dev works immediately
                credential = ChainedTokenCredential(
                    EnvironmentCredential(additionally_allowed_tenants=["*"]),
                    ManagedIdentityCredential(),
                    AzureCliCredential(),
                )

                logger.info(
                    "Created ChainedTokenCredential (Environment -> ManagedIdentity -> AzureCli)",
                    extra={"operation": "config_init"},
                )

                # Load App Configuration WITH Key Vault credential for resolving Key Vault references
                self._config_provider = load(
                    connection_string=self.app_config_connection_string,
                    keyvault_credential=credential,
                )
                self._app_config_available = True
                logger.info(
                    "Azure App Configuration provider initialized with Key Vault resolution",
                    extra={"operation": "config_init"},
                )
            except ImportError as e:
                import sys

                logger.warning(
                    f"Azure App Configuration SDK not available (ImportError: {e}), using environment variables only",
                    extra={
                        "operation": "config_init",
                        "python_version": sys.version,
                        "python_executable": sys.executable,
                        "import_error": str(e),
                    },
                )
            except Exception as e:
                logger.warning(
                    f"Failed to initialize App Configuration provider: {type(e).__name__}: {e}, using environment variables",
                    extra={
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "operation": "config_init",
                    },
                    exc_info=True,
                )
        else:
            logger.info(
                "No App Configuration connection string provided, using environment variables only",
                extra={"operation": "config_init"},
            )

        # Auto-load to environment if requested
        if auto_load_to_environ:
            self.load_to_environ()

    def get_value(self, key: str, default: str | None = None) -> str | None:
        """
        Get a configuration value with hierarchical lookup.

        Lookup order:
        1. Environment variables (highest priority)
        2. Cache (if previously retrieved)
        3. Azure App Configuration with automatic Key Vault reference resolution
        4. Key Vault secrets (via secrets repository, fallback)
        5. Default value (lowest priority)

        Note: If a value is stored in App Config as a Key Vault reference,
        it will be automatically resolved by the provider.

        Args:
            key: Configuration key name
            default: Default value if key not found

        Returns:
            Optional[str]: Configuration value or default
        """
        # 1. Check environment variables first (highest priority)
        env_value = os.getenv(key)
        if env_value is not None:
            logger.debug(f"Config '{key}' found in environment variables")
            return env_value

        # 2. Check cache
        if key in self._cache:
            logger.debug(f"Config '{key}' found in cache")
            return self._cache[key]

        # 3. Try App Configuration provider (with automatic Key Vault resolution)
        if self._config_provider:
            try:
                # The provider acts like a dictionary with automatic Key Vault resolution
                value = self._config_provider.get(key)
                if value is not None:
                    # Ensure value is a string (Azure SDK can return Mapping for complex types)
                    str_value = str(value) if not isinstance(value, str) else value
                    self._cache[key] = str_value
                    logger.info(
                        f"Config '{key}' retrieved from App Configuration (Key Vault references auto-resolved)",
                        extra={"key": key, "operation": "get_value"},
                    )
                    return str_value
            except Exception as e:
                logger.debug(
                    f"Config '{key}' not found in App Configuration: {e}",
                    extra={"key": key, "error": str(e), "operation": "get_value"},
                )

        # 4. Try secrets repository (fallback for direct Key Vault access)
        if self.secrets_repository:
            secret_value = self.secrets_repository.get_secret(key)
            if secret_value:
                self._cache[key] = secret_value
                logger.info(
                    f"Config '{key}' retrieved from direct Key Vault access (fallback)",
                    extra={"key": key, "operation": "get_value"},
                )
                return secret_value

        # 5. Return default
        logger.debug(
            f"Config '{key}' not found, using default",
            extra={"key": key, "default": default, "operation": "get_value"},
        )
        return default

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
        """
        if not self.secrets_repository:
            logger.warning(
                f"No secrets repository available for key '{key}'",
                extra={"key": key, "operation": "get_secret_value"},
            )
            return default

        secret_value = self.secrets_repository.get_secret(key)
        if secret_value:
            logger.info(
                f"Secret '{key}' retrieved successfully",
                extra={"key": key, "operation": "get_secret_value"},
            )
            return secret_value

        logger.debug(
            f"Secret '{key}' not found, using default",
            extra={"key": key, "default": default, "operation": "get_secret_value"},
        )
        return default

    def get_all_values(self) -> dict[str, str]:
        """
        Get all configuration values from all sources.

        Returns:
            Dict[str, str]: All configuration key-value pairs with Key Vault references resolved
        """
        all_configs: dict[str, str] = {}

        # Start with App Configuration provider (Key Vault references already resolved)
        if self._config_provider:
            try:
                # The provider has already loaded and resolved all configs and Key Vault references
                for key in self._config_provider:
                    value = self._config_provider.get(key)
                    if value is not None:
                        # Ensure value is a string (Azure SDK can return Mapping for complex types)
                        str_value = str(value) if not isinstance(value, str) else value
                        all_configs[key] = str_value
                logger.info(
                    f"Retrieved {len(all_configs)} configs from App Configuration (Key Vault refs resolved)",
                    extra={"count": len(all_configs), "operation": "get_all_values"},
                )
            except Exception as e:
                logger.error(
                    f"Failed to retrieve all configs from App Configuration: {e}",
                    extra={"error": str(e), "operation": "get_all_values"},
                )

        # Add cached values
        all_configs.update(self._cache)

        # Environment variables override everything
        for key, value in os.environ.items():
            all_configs[key] = value

        return all_configs

    def load_to_environ(self) -> int:
        """
        Load configuration values to os.environ.

        Precedence Logic:
        1. Values already in os.environ are PRESERVED (local.settings.json wins)
        2. Missing values are added from App Configuration (fill gaps)
        3. This allows local development overrides while providing defaults

        Example:
            # local.settings.json sets:
            os.environ["USE_MOCK_SHAREPOINT"] = "true"

            # App Config has:
            config["USE_MOCK_SHAREPOINT"] = "false"
            config["NEW_CONFIG"] = "value"

            # After load_to_environ():
            os.environ["USE_MOCK_SHAREPOINT"] = "true"  # ✅ Local preserved
            os.environ["NEW_CONFIG"] = "value"  # ✅ Remote added

        Returns:
            int: Number of NEW values added to os.environ (excludes skipped)
        """
        logger.info(
            "Loading all configuration to os.environ",
            extra={"operation": "load_to_environ"},
        )

        added_count = 0
        skipped_count = 0

        # Load from App Configuration provider (Key Vault references already resolved)
        if self._config_provider:
            try:
                for key in self._config_provider:
                    value = self._config_provider.get(key)
                    if value is None:
                        continue

                    # Check if key already exists in os.environ (from local.settings.json)
                    if key in os.environ:
                        skipped_count += 1
                        logger.debug(
                            "Skipping key already in os.environ (local override)",
                            extra={
                                "operation": "load_to_environ_skip",
                                "key": key,
                                "local_value": os.environ[key],
                                "remote_value": value,
                            },
                        )
                        continue  # ✅ Preserve local value

                    # Key not in os.environ - add from App Config
                    # Ensure value is a string (Azure SDK can return Mapping for complex types)
                    str_value = str(value) if not isinstance(value, str) else value
                    os.environ[key] = str_value
                    added_count += 1
                    logger.debug(
                        "Added config value to os.environ",
                        extra={
                            "operation": "load_to_environ_add",
                            "key": key,
                        },
                    )

                logger.info(
                    f"Loaded {added_count} configs from App Configuration to os.environ (Key Vault refs resolved)",
                    extra={
                        "count": added_count,
                        "skipped": skipped_count,
                        "operation": "load_to_environ",
                    },
                )
            except Exception as e:
                logger.error(
                    f"Failed to load configs to environment: {e}",
                    extra={"error": str(e), "operation": "load_to_environ"},
                )

        # Load from secrets repository (fallback for direct Key Vault access)
        if self.secrets_repository:
            try:
                secrets = self.secrets_repository.list_secrets()
                for key, value in secrets.items():
                    # Check if key already exists in os.environ (from local.settings.json)
                    if key in os.environ:
                        skipped_count += 1
                        logger.debug(
                            "Skipping secret already in os.environ (local override)",
                            extra={
                                "operation": "load_to_environ_skip",
                                "key": key,
                                "local_value": os.environ[key],
                            },
                        )
                        continue  # ✅ Preserve local value

                    # Key not in os.environ - add from Key Vault
                    os.environ[key] = value
                    added_count += 1

                logger.info(
                    f"Loaded {len(secrets)} secrets from direct Key Vault access (fallback)",
                    extra={"count": len(secrets), "operation": "load_to_environ"},
                )
            except Exception as e:
                logger.error(
                    f"Failed to load secrets to environment: {e}",
                    extra={"error": str(e), "operation": "load_to_environ"},
                )

        logger.info(
            f"Configuration loading complete: {added_count} values added, {skipped_count} local values preserved",
            extra={
                "added_count": added_count,
                "skipped_count": skipped_count,
                "operation": "load_to_environ",
            },
        )

        return added_count

    def refresh(self) -> None:
        """
        Refresh configuration from all sources.

        This method clears the cache and reloads configuration from
        App Configuration (with Key Vault references resolved) to pick up any changes.
        """
        logger.info("Refreshing configuration", extra={"operation": "refresh"})

        # Clear cache
        self._cache.clear()

        # Refresh the App Configuration provider (this will re-fetch and re-resolve Key Vault refs)
        if self._config_provider and hasattr(self._config_provider, "refresh"):
            try:
                self._config_provider.refresh()
                logger.info("App Configuration provider refreshed", extra={"operation": "refresh"})
            except Exception as e:
                logger.error(
                    f"Failed to refresh App Configuration provider: {e}",
                    extra={"error": str(e), "operation": "refresh"},
                )

        # Clear secrets cache if available
        if self.secrets_repository and hasattr(self.secrets_repository, "clear_cache"):
            self.secrets_repository.clear_cache()

        # Reload to environment
        self.load_to_environ()

        logger.info("Configuration refresh complete", extra={"operation": "refresh"})

    def get_repository_metrics(self) -> dict[str, Any]:
        """
        Get metrics about the configuration repository.

        Returns:
            Dict[str, Any]: Metrics including source counts, cache hits, etc.
        """
        metrics = {
            "app_config_available": self._app_config_available,
            "secrets_repository_available": self.secrets_repository is not None
            and self.secrets_repository.is_available(),
            "cached_keys_count": len(self._cache),
            "environment_variables_count": len(os.environ),
        }

        # Get App Config count if available (includes resolved Key Vault references)
        if self._config_provider:
            try:
                config_count = len(list(self._config_provider))
                metrics["app_config_count"] = config_count
            except Exception:
                metrics["app_config_count"] = 0
        else:
            metrics["app_config_count"] = 0

        # Get secrets count if available (fallback direct access)
        if self.secrets_repository:
            try:
                secrets = self.secrets_repository.list_secrets()
                metrics["secrets_count"] = len(secrets)
            except Exception:
                metrics["secrets_count"] = 0
        else:
            metrics["secrets_count"] = 0

        return metrics

    def clear_cache(self) -> None:
        """
        Clear the configuration cache.

        This method clears all cached configuration values, forcing
        the next get_value call to retrieve fresh data from sources.
        """
        logger.info("Clearing configuration cache", extra={"operation": "clear_cache"})
        self._cache.clear()

    def is_available(self) -> bool:
        """
        Check if the configuration repository is available.

        Returns:
            bool: True if at least one configuration source is available
        """
        return self._app_config_available or (
            self.secrets_repository is not None and self.secrets_repository.is_available()
        )

    def is_app_config_available(self) -> bool:
        """
        Check if Azure App Configuration is available and accessible.

        Returns:
            bool: True if App Config is accessible, False otherwise
        """
        return self._app_config_available

    def is_key_vault_available(self) -> bool:
        """
        Check if Azure Key Vault is available and accessible.

        Returns:
            bool: True if Key Vault is accessible, False otherwise
        """
        if self.secrets_repository:
            return self.secrets_repository.is_available()
        return False


def create_enhanced_config_repository(
    app_config_connection_string: str | None = None,
    secrets_repository: SecretsRepositoryInterface | None = None,
    auto_load_to_environ: bool = False,
) -> EnhancedConfigRepositoryInterface:
    """
    Factory function to create an enhanced configuration repository.

    This factory function provides a convenient way to create a properly
    configured EnhancedConfigRepository instance.

    Args:
        app_config_connection_string: Azure App Configuration connection string
        secrets_repository: Optional secrets repository for Key Vault integration
        auto_load_to_environ: If True, automatically load configs to os.environ on init

    Returns:
        EnhancedConfigRepositoryInterface: Configured repository instance

    Usage:
        # Simple usage with environment variables only
        config_repo = create_enhanced_config_repository()

        # With App Config
        config_repo = create_enhanced_config_repository(
            app_config_connection_string="Endpoint=...",
            auto_load_to_environ=True
        )

        # With App Config and Key Vault
        secrets_repo = SecretsRepository(vault_url="...")
        config_repo = create_enhanced_config_repository(
            app_config_connection_string="Endpoint=...",
            secrets_repository=secrets_repo,
            auto_load_to_environ=True
        )
    """
    logger.info(
        "Creating enhanced configuration repository",
        extra={
            "has_app_config": bool(app_config_connection_string),
            "has_secrets_repo": bool(secrets_repository),
            "auto_load": auto_load_to_environ,
            "operation": "create_repository",
        },
    )

    return EnhancedConfigRepository(
        app_config_connection_string=app_config_connection_string,
        secrets_repository=secrets_repository,
        auto_load_to_environ=auto_load_to_environ,
    )
