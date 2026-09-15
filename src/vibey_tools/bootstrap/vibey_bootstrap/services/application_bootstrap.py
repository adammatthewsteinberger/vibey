"""
Application bootstrap orchestrator that handles the complete startup flow.

This module orchestrates the proper bootstrap sequence to solve the circular dependency
between logging and configuration:

1. Start with console logging (always works)
2. Try App Insights from os.environ if available
3. Load enhanced configuration from App Config/Key Vault
4. Upgrade to App Insights if connection string is now available
5. Load all configs to os.environ for transparent access

This ensures logging works throughout the entire process and eliminates the
chicken-and-egg problem between configuration and telemetry.
"""

import os
from typing import Any

from vibey_bootstrap.repositories.enhanced_config_repository import (
    create_enhanced_config_repository,
)
from vibey_bootstrap.repositories.interfaces.enhanced_config_repository_interface import (
    EnhancedConfigRepositoryInterface,
)
from vibey_bootstrap.repositories.interfaces.secrets_repository_interface import (
    SecretsRepositoryInterface,
)
from vibey_bootstrap.services.bootstrap_logging import BootstrapLogger, get_bootstrap_logger
from vibey_bootstrap.services.interfaces.application_bootstrap_interface import (
    ApplicationBootstrapInterface,
)
from vibey_bootstrap.services.telemetry import telemetry_manager


class ApplicationBootstrap(ApplicationBootstrapInterface):
    """
    Orchestrates the complete application startup sequence with proper logging flow.

    This class handles the complex bootstrap process that requires careful ordering
    to avoid circular dependencies between logging, configuration, and secrets.

    Bootstrap Flow:
        1. Initialize console logging (safe fallback that always works)
        2. Try App Insights from environment variables if available
        3. Create and load enhanced configuration from App Config/Key Vault
        4. Attempt to upgrade logging to App Insights if connection string is now available
        5. Load all configuration to os.environ for transparent application access
        6. Log completion and provide access to configured components

    Key Features:
        - Eliminates circular dependencies between logging and configuration
        - Provides working logging throughout the entire bootstrap process
        - Graceful fallbacks at every step ensure robustness
        - Comprehensive logging of bootstrap progress and decisions
        - Transparent configuration access via os.environ after completion

    Usage Example:
        # Simple bootstrap
        bootstrap = ApplicationBootstrap()
        config_repo = bootstrap.initialize()

        # Bootstrap with secrets repository
        bootstrap = ApplicationBootstrap(secrets_repository=my_secrets_repo)
        config_repo = bootstrap.initialize()

        # After bootstrap, all configs are in os.environ
        app_insights_key = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")
        database_host = os.getenv("DATABASE_HOST")
    """

    def __init__(self, secrets_repository: SecretsRepositoryInterface | None = None) -> None:
        """
        Initialize the application bootstrap orchestrator.

        Args:
            secrets_repository: Optional secrets repository for Key Vault integration
        """
        # Start with bootstrap logging immediately
        BootstrapLogger.configure_bootstrap_logging()
        self.logger = get_bootstrap_logger(__name__)

        self.secrets_repository = secrets_repository
        self.config_repository: EnhancedConfigRepositoryInterface | None = None
        self._bootstrap_completed = False

        self.logger.info(
            "ApplicationBootstrap initialized",
            extra={
                "has_secrets_repository": bool(secrets_repository),
                "operation": "bootstrap_init",
                "component": "ApplicationBootstrap",
            },
        )

    def initialize(self) -> EnhancedConfigRepositoryInterface:
        """
        Execute the complete bootstrap sequence with proper logging flow.

        This method orchestrates the entire application startup process following
        the correct sequence to avoid circular dependencies while ensuring working
        logging throughout.

        Returns:
            Configured enhanced configuration repository with all configs loaded

        Raises:
            RuntimeError: If bootstrap fails in an unrecoverable way
        """
        if self._bootstrap_completed and self.config_repository is not None:
            self.logger.info("Bootstrap already completed, returning existing config repository")
            return self.config_repository

        self.logger.info(
            "Starting application bootstrap sequence",
            extra={
                "operation": "bootstrap_start",
                "component": "ApplicationBootstrap",
                "bootstrap_phase": "initialization",
            },
        )

        try:
            # Phase 1: Initial telemetry setup with environment variables only
            self._initialize_telemetry_from_environment()

            # Phase 2: Load enhanced configuration from App Config/Key Vault
            self._load_enhanced_configuration()

            # Phase 3: Upgrade telemetry if App Insights connection string is now available
            self._upgrade_telemetry_from_config()

            # Phase 4: Final configuration loading to os.environ
            self._finalize_configuration_loading()

            # Mark bootstrap as completed
            self._bootstrap_completed = True

            self.logger.info(
                "Application bootstrap completed successfully",
                extra={
                    "operation": "bootstrap_complete",
                    "component": "ApplicationBootstrap",
                    "bootstrap_phase": "completed",
                    "telemetry_enabled": bool(telemetry_manager.tracer),
                    "config_repository_type": type(self.config_repository).__name__,
                },
            )

            if self.config_repository is not None:
                return self.config_repository
            raise RuntimeError("Bootstrap completed but config repository is None")

        except Exception as e:
            self.logger.error(
                "Application bootstrap failed",
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "operation": "bootstrap_error",
                    "component": "ApplicationBootstrap",
                    "bootstrap_phase": "failed",
                },
                exc_info=True,
            )
            raise RuntimeError(f"Application bootstrap failed: {str(e)}") from e

    def _initialize_telemetry_from_environment(self) -> None:
        """
        Phase 1: Initialize telemetry using only environment variables.

        This phase attempts to configure App Insights using only what's available
        in os.environ. If the connection string isn't available, it falls back to
        console logging which ensures we have working logging for the rest of bootstrap.
        """
        self.logger.info(
            "Phase 1: Initializing telemetry from environment variables",
            extra={
                "operation": "telemetry_init_phase1",
                "component": "ApplicationBootstrap",
                "bootstrap_phase": "telemetry_environment",
                "app_insights_available": bool(
                    os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")
                ),
            },
        )

        # Configure telemetry - this will use console logging if App Insights not available
        telemetry_manager.configure()

        if telemetry_manager.tracer:
            self.logger.info("Application Insights configured from environment variables")
        else:
            self.logger.info("Using console logging, App Insights not available from environment")

    def _load_enhanced_configuration(self) -> None:
        """
        Phase 2: Create and load enhanced configuration repository.

        This phase creates the enhanced configuration repository which loads
        configuration from App Configuration and Key Vault. This may make
        additional configuration available including App Insights connection string.
        """
        self.logger.info(
            "Phase 2: Loading enhanced configuration from App Config/Key Vault",
            extra={
                "operation": "config_load_phase2",
                "component": "ApplicationBootstrap",
                "bootstrap_phase": "config_loading",
                "has_secrets_repository": bool(self.secrets_repository),
            },
        )

        # Create the enhanced config repository - this loads configs to os.environ by default
        app_config_connection_string = os.getenv("AZURE_APP_CONFIGURATION_CONNECTION_STRING")
        self.config_repository = create_enhanced_config_repository(
            app_config_connection_string=app_config_connection_string,
            secrets_repository=self.secrets_repository,
            auto_load_to_environ=True,  # Explicitly enable auto-loading
        )

        self.logger.info(
            "Enhanced configuration repository created and loaded",
            extra={
                "config_repository_type": type(self.config_repository).__name__,
                "operation": "config_load_phase2",
                "component": "ApplicationBootstrap",
                "bootstrap_phase": "config_loaded",
            },
        )

    def _upgrade_telemetry_from_config(self) -> None:
        """
        Phase 3: Attempt to upgrade telemetry using newly loaded configuration.

        This phase checks if an App Insights connection string is now available
        from the loaded configuration that wasn't available from environment variables.
        If found, it upgrades from console logging to App Insights.
        """
        self.logger.info(
            "Phase 3: Checking for telemetry upgrade from loaded configuration",
            extra={
                "operation": "telemetry_upgrade_phase3",
                "component": "ApplicationBootstrap",
                "bootstrap_phase": "telemetry_upgrade",
                "currently_has_app_insights": bool(telemetry_manager.tracer),
            },
        )

        # Attempt to upgrade telemetry using the loaded configuration
        if self.config_repository is None:
            self.logger.warning("Config repository not available, skipping telemetry upgrade")
            return

        upgrade_attempted = telemetry_manager.try_upgrade_from_config(self.config_repository)

        if upgrade_attempted:
            if telemetry_manager.tracer:
                self.logger.info(
                    "Successfully upgraded to Application Insights from loaded configuration"
                )
            else:
                self.logger.warning(
                    "Upgrade to Application Insights failed, continuing with console logging"
                )
        else:
            self.logger.debug("No telemetry upgrade needed or possible")

    def _finalize_configuration_loading(self) -> None:
        """
        Phase 4: Ensure all configuration is loaded to os.environ for application access.

        This phase ensures that all configuration values are available in os.environ
        so the rest of the application can use standard Python environment variable
        access patterns.
        """
        self.logger.info(
            "Phase 4: Finalizing configuration loading to os.environ",
            extra={
                "operation": "config_finalize_phase4",
                "component": "ApplicationBootstrap",
                "bootstrap_phase": "config_finalization",
            },
        )

        # The enhanced config repository should have already loaded to os.environ
        # during creation, but let's verify and get metrics
        if self.config_repository is not None:
            try:
                metrics = self.config_repository.get_repository_metrics()
                self.logger.info(
                    "Configuration repository metrics",
                    extra={
                        "total_env_vars": len(os.environ),
                        "repository_metrics": metrics,
                        "operation": "config_finalize_phase4",
                        "component": "ApplicationBootstrap",
                        "bootstrap_phase": "metrics_logged",
                    },
                )
            except Exception as e:
                self.logger.warning(f"Could not retrieve repository metrics: {str(e)}")

        # Log key configuration status without exposing sensitive values
        key_configs = [
            "APPLICATIONINSIGHTS_CONNECTION_STRING",
            "AZURE_APP_CONFIG_CONNECTION_STRING",
            "USE_LOCAL_SETTINGS_ONLY",
            "AUTO_LOAD_TO_ENVIRON",
            "FUNCTIONS_WORKER_RUNTIME",
        ]

        config_status = {}
        for key in key_configs:
            config_status[key] = key in os.environ

        self.logger.info(
            "Key configuration availability after bootstrap",
            extra={
                "config_availability": config_status,
                "operation": "config_finalize_phase4",
                "component": "ApplicationBootstrap",
                "bootstrap_phase": "config_status_logged",
            },
        )

        # All configs are now loaded to os.environ and ready to use
        # No reload needed - code uses os.getenv() directly for current values
        self.logger.info(
            "Configuration finalized - all configs available in os.environ",
            extra={
                "operation": "config_finalize_phase4",
                "component": "ApplicationBootstrap",
                "bootstrap_phase": "config_finalized",
            },
        )

    def get_config_repository(self) -> EnhancedConfigRepositoryInterface | None:
        """
        Get the configured repository after bootstrap.

        Returns:
            The enhanced configuration repository if bootstrap is complete, None otherwise
        """
        return self.config_repository if self._bootstrap_completed else None

    def is_bootstrap_completed(self) -> bool:
        """
        Check if bootstrap process has completed successfully.

        Returns:
            True if bootstrap completed successfully, False otherwise
        """
        return self._bootstrap_completed


def initialize_application(
    secrets_repository: SecretsRepositoryInterface | None = None,
) -> EnhancedConfigRepositoryInterface:
    """
    Convenience function to perform complete application bootstrap.

    This is the main entry point for application initialization. It handles
    the complete bootstrap sequence and returns the configured repository.

    Args:
        secrets_repository: Optional secrets repository for Key Vault integration

    Returns:
        Configured enhanced configuration repository with all configs loaded

    Example:
        # Simple initialization
        config_repo = initialize_application()

        # With secrets repository
        from src.repositories.secrets_repository import create_secrets_repository
        secrets_repo = create_secrets_repository()
        config_repo = initialize_application(secrets_repository=secrets_repo)

        # After initialization, use standard os.environ access
        app_insights_key = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")
    """
    bootstrap = ApplicationBootstrap(secrets_repository=secrets_repository)
    repo = bootstrap.initialize()
    global _last_initialized_repo
    _last_initialized_repo = repo
    return repo


_last_initialized_repo: EnhancedConfigRepositoryInterface | None = None


def get_last_initialized_repo() -> EnhancedConfigRepositoryInterface | None:
    """Return the most recent config repo produced by ``initialize_application()``.

    Used by ``vibey_bootstrap.refresh_setting()`` to re-read named keys at
    runtime without re-running the full bootstrap. Returns None until
    ``initialize_application()`` has been called.
    """
    return _last_initialized_repo


def create_ai_processing_service() -> Any:  # pragma: no cover
    """
    Factory function to create fully initialized AIProcessingService with all dependencies.

    Legacy v1 factory — not part of the public API (not exported from
    vibey_bootstrap.__init__) and excluded from coverage. Will be removed in
    a future major.

    This function creates all required repositories and wires them into the service layer.
    It uses environment variables loaded during application bootstrap.

    This is the recommended way to create the service in production code.

    Returns:
        Fully initialized AIProcessingService instance

    Raises:
        ValueError: If required environment variables are missing

    Example:
        # After bootstrap completes, create the service
        config_repo = initialize_application()
        service = create_ai_processing_service()

        # Use in controller
        controller = AIProcessingController(service=service)
    """
    logger = get_bootstrap_logger(__name__)

    logger.info(
        "Creating AI Processing Service with all repository dependencies",
        extra={
            "operation": "create_ai_processing_service",
            "component": "ApplicationBootstrap",
        },
    )

    # Import repositories (delayed to avoid circular imports)
    from src.repositories.ai_service_repository import AIServiceRepository
    from src.repositories.blob_storage_repository import BlobStorageRepository
    from src.repositories.postgresql_repository import PostgreSQLRepository
    from src.repositories.service_bus_repository import ServiceBusRepository
    from src.repositories.sharepoint_repository import SharePointRepository
    from src.repositories.vector_store_repository import VectorStoreRepository
    from src.services.ai_processing_service import AIProcessingService

    # Create BlobStorageRepository
    blob_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if not blob_connection_string:
        raise ValueError("AZURE_STORAGE_CONNECTION_STRING environment variable is required")

    blob_repo = BlobStorageRepository(
        connection_string=blob_connection_string,
        container_name=os.getenv("AZURE_STORAGE_CONTAINER_NAME", "payroll-data"),
    )
    logger.debug("BlobStorageRepository created")

    # Create SharePointRepository (or mock for local dev)
    USE_MOCK_SHAREPOINT = os.getenv("USE_MOCK_SHAREPOINT", "false").lower() == "true"

    if USE_MOCK_SHAREPOINT:
        # Use mock SharePoint repository for local development
        from src.repositories.mock_sharepoint_repository import MockSharePointRepository

        sharepoint_repo = MockSharePointRepository()
        logger.warning(
            "Using MOCK SharePoint repository - LOCAL DEVELOPMENT ONLY",
            extra={
                "operation": "create_mock_sharepoint_repository",
                "component": "ApplicationBootstrap",
                "warning": "Mock data will be used instead of real SharePoint files",
            },
        )
    else:
        # Use real SharePoint repository
        AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
        AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
        AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
        SHAREPOINT_SITE_URL = os.getenv("SHAREPOINT_SITE_URL")

        if not all([AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID]):
            raise ValueError(
                "SharePoint credentials (CLIENT_ID, CLIENT_SECRET, TENANT_ID) are required"
            )

        if not SHAREPOINT_SITE_URL:
            raise ValueError("SHAREPOINT_SITE_URL environment variable is required")

        sharepoint_repo = SharePointRepository(
            client_id=AZURE_CLIENT_ID,
            client_secret=AZURE_CLIENT_SECRET,
            tenant_id=AZURE_TENANT_ID,
            site_url=SHAREPOINT_SITE_URL,
        )
        logger.debug("SharePointRepository created")

    # Create PostgreSQLRepository
    db_host = os.getenv("DATABASE_HOST")
    db_name = os.getenv("DATABASE_NAME")
    db_user = os.getenv("DATABASE_USER")
    db_password = os.getenv("DATABASE_PASSWORD")

    if not all([db_host, db_name, db_user, db_password]):
        raise ValueError("Database credentials (HOST, NAME, USER, PASSWORD) are required")

    db_repo = PostgreSQLRepository(
        host=db_host,
        database=db_name,
        user=db_user,
        password=db_password,
        port=int(os.getenv("DATABASE_PORT", "5432")),
    )
    logger.debug("PostgreSQLRepository created")

    # Create AIServiceRepository (needed before VectorStoreRepository)
    openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    openai_api_key = os.getenv("AZURE_OPENAI_KEY")

    if not all([openai_endpoint, openai_api_key]):
        raise ValueError("Azure OpenAI credentials (ENDPOINT, KEY) are required")

    ai_repo = AIServiceRepository(
        endpoint=openai_endpoint,
        api_key=openai_api_key,
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
    )
    logger.debug("AIServiceRepository created")

    # Create VectorStoreRepository (uses OpenAI for embeddings)
    search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    search_api_key = os.getenv("AZURE_SEARCH_KEY")
    embedding_model = os.getenv("AZURE_OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")

    if not all([search_endpoint, search_api_key]):
        raise ValueError("Azure AI Search credentials (ENDPOINT, KEY) are required")

    vector_repo = VectorStoreRepository(
        search_endpoint=search_endpoint,
        search_api_key=search_api_key,
        openai_endpoint=openai_endpoint,
        openai_api_key=openai_api_key,
        embedding_model=embedding_model,
    )
    logger.debug("VectorStoreRepository created")

    # Create ServiceBusRepository (or mock for local dev)
    USE_MOCK_SERVICE_BUS = os.getenv("USE_MOCK_SERVICE_BUS", "false").lower() == "true"

    if USE_MOCK_SERVICE_BUS:
        # Use mock Service Bus repository for local development
        from src.repositories.mock_service_bus_repository import MockServiceBusRepository

        sb_repo = MockServiceBusRepository()
        logger.warning(
            "Using MOCK Service Bus repository - LOCAL DEVELOPMENT ONLY",
            extra={
                "operation": "create_mock_service_bus_repository",
                "component": "ApplicationBootstrap",
                "warning": "Messages will be logged locally, NOT sent to Azure Service Bus",
            },
        )
    else:
        # Use real Service Bus repository
        sb_connection_string = os.getenv("SERVICE_BUS_CONNECTION_STRING")
        if not sb_connection_string:
            raise ValueError("SERVICE_BUS_CONNECTION_STRING environment variable is required")

        sb_repo = ServiceBusRepository(connection_string=sb_connection_string)
        logger.debug("ServiceBusRepository created")

    # Create AIProcessingService with all dependencies
    service = AIProcessingService(
        blob_repo=blob_repo,
        sharepoint_repo=sharepoint_repo,
        db_repo=db_repo,
        vector_repo=vector_repo,
        ai_repo=ai_repo,
        sb_repo=sb_repo,
    )

    logger.info(
        "AI Processing Service created successfully",
        extra={
            "operation": "create_ai_processing_service_complete",
            "component": "ApplicationBootstrap",
        },
    )

    return service
