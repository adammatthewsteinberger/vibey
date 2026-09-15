import logging
import os
from typing import Any

from vibey_bootstrap.repositories.interfaces.enhanced_config_repository_interface import (
    EnhancedConfigRepositoryInterface,
)
from vibey_bootstrap.services.bootstrap_logging import (
    BootstrapLogger,
    ExtraFieldsFormatter,
)
from vibey_bootstrap.services.interfaces.telemetry_manager_interface import (
    TelemetryManagerInterface,
)

# Optional imports for telemetry
try:
    from azure.monitor.opentelemetry import configure_azure_monitor
    from opentelemetry import trace

    TELEMETRY_AVAILABLE = True
except ImportError:
    TELEMETRY_AVAILABLE = False
    logging.warning("Azure Monitor OpenTelemetry not available, using basic logging")

# Optional Azure Functions instrumentation (not available as standalone package)
AZURE_FUNCTIONS_INSTRUMENTOR_AVAILABLE = False
AzureFunctionsInstrumentor = None
try:
    from opentelemetry.instrumentation.azure_functions import (
        AzureFunctionsInstrumentor as _AzureFunctionsInstrumentor,
    )

    AzureFunctionsInstrumentor = _AzureFunctionsInstrumentor
    AZURE_FUNCTIONS_INSTRUMENTOR_AVAILABLE = True
except ImportError:
    pass  # Azure Functions instrumentation not available - this is optional


class TelemetryManager(TelemetryManagerInterface):
    """Manages Application Insights telemetry and structured logging"""

    def __init__(self) -> None:
        self.tracer: Any = None
        self._configured = False

    def configure(
        self, connection_string: str | None = None, allow_reconfigure: bool = False
    ) -> bool:
        """
        Configure Application Insights telemetry with support for bootstrap flow reconfiguration

        Args:
            connection_string: App Insights connection string
            allow_reconfigure: If True, allows reconfiguration even if already configured
        """
        if self._configured and not allow_reconfigure:
            return True

        try:
            # Get connection string from environment or parameter
            app_insights_connection_string = connection_string or os.environ.get(
                "APPLICATIONINSIGHTS_CONNECTION_STRING"
            )

            if not app_insights_connection_string:
                logging.warning(
                    "Application Insights connection string not found. Using basic logging."
                )
                self._configure_logging()
                self._configured = True
                return True

            if not TELEMETRY_AVAILABLE:
                logging.warning("Azure Monitor OpenTelemetry not available. Using basic logging.")
                self._configure_logging()
                self._configured = True
                return True

            # Configure Azure Monitor
            configure_azure_monitor(
                connection_string=app_insights_connection_string,
                enable_live_metrics=True,
            )

            # Instrument Azure Functions (if available)
            if AZURE_FUNCTIONS_INSTRUMENTOR_AVAILABLE and AzureFunctionsInstrumentor:
                AzureFunctionsInstrumentor().instrument()

            # Get tracer
            self.tracer = trace.get_tracer(__name__)

            # Configure structured logging
            self._configure_logging()

            self._configured = True
            logging.info("Application Insights telemetry configured successfully")
            return True

        except Exception as e:
            logging.error(f"Failed to configure Application Insights: {str(e)}")
            # Fallback to basic logging
            self._configure_logging()
            self._configured = True
            return True

    def try_upgrade_from_config(self, config_repository: EnhancedConfigRepositoryInterface) -> bool:
        """
        Attempt to upgrade from basic logging to App Insights after config is loaded

        This method is called after configuration loading to check if an App Insights
        connection string is now available from App Config/Key Vault that wasn't
        available during initial bootstrap.

        Args:
            config_repository: Enhanced config repository to check for connection string

        Returns:
            True if upgrade was attempted (success or failure), False if no upgrade needed
        """
        # Don't upgrade if already using App Insights
        if self.tracer is not None:
            logging.debug("Already using Application Insights, no upgrade needed")
            return False

        # Check if connection string is now available from config
        # First try get_value() which checks env vars, cache, App Config, then Key Vault fallback
        # If not found, try get_secret_value() for direct Key Vault access
        try:
            app_insights_connection_string = config_repository.get_value(
                "APPLICATIONINSIGHTS_CONNECTION_STRING"
            )

            # If not found via get_value, try direct Key Vault access as last resort
            if not app_insights_connection_string:
                app_insights_connection_string = config_repository.get_secret_value(
                    "APPLICATIONINSIGHTS_CONNECTION_STRING"
                )

            if app_insights_connection_string:
                logging.info(
                    "Found Application Insights connection string in config, upgrading from basic logging"
                )

                # Reconfigure with the new connection string
                success = self.configure(
                    connection_string=app_insights_connection_string, allow_reconfigure=True
                )

                if success and self.tracer:
                    logging.info("Successfully upgraded to Application Insights telemetry")
                    return True
                else:
                    logging.warning(
                        "Failed to upgrade to Application Insights, continuing with basic logging"
                    )
                    return True
            else:
                logging.debug("No Application Insights connection string found in config")
                return False

        except Exception as e:
            logging.warning(f"Error checking for Application Insights upgrade: {str(e)}")
            return False

    def _configure_logging(self) -> None:
        """Configure structured logging format, transitioning from bootstrap if needed"""
        # Enhanced formatter for production logging with extra fields support
        formatter = ExtraFieldsFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d"
        )

        # Configure root logger
        root_logger = logging.getLogger()

        # Ensure log level respects LOG_LEVEL env var
        log_level_str = os.environ.get("LOG_LEVEL", "INFO")
        numeric_level = getattr(logging, log_level_str.upper(), None)
        if isinstance(numeric_level, int):
            root_logger.setLevel(numeric_level)

        # Transition from bootstrap logging
        if BootstrapLogger.is_bootstrap_configured():
            logging.info("Transitioning from bootstrap to full telemetry logging")

        if root_logger.handlers:
            for handler in root_logger.handlers:
                handler.setFormatter(formatter)

        # Log the transition
        if BootstrapLogger.is_bootstrap_configured():
            if self.tracer is not None:
                logging.info(
                    "Successfully transitioned to full telemetry logging with App Insights"
                )
            else:
                logging.info(
                    "Successfully transitioned to structured logging (App Insights not available)"
                )

    def get_tracer(self) -> Any:
        """Get the configured tracer"""
        return self.tracer

    def create_span(self, name: str, attributes: dict[str, Any] | None = None) -> Any:
        """Create a new trace span"""
        # Check if telemetry is available and tracer is configured
        has_tracer = bool(getattr(self, "tracer", None))
        if TELEMETRY_AVAILABLE and has_tracer and self.tracer is not None:
            return self.tracer.start_span(name, attributes=attributes)
        return None

    def log_email_processing_start(
        self, message_id: str | None = None, user_email: str | None = None
    ) -> None:
        """Log email processing start with structured data"""
        log_data = {
            "event": "email_processing_start",
            "message_id": message_id,
            "user_email": user_email,
            "operation": "read_email",
        }
        logging.info("Email processing started", extra=log_data)

    def log_email_processing_success(
        self, message_id: str, user_email: str, processing_time_ms: int
    ) -> None:
        """Log successful email processing"""
        log_data = {
            "event": "email_processing_success",
            "message_id": message_id,
            "user_email": user_email,
            "processing_time_ms": processing_time_ms,
            "operation": "read_email",
        }
        logging.info("Email processing completed successfully", extra=log_data)

    def log_email_processing_error(
        self, error: str, message_id: str | None = None, user_email: str | None = None
    ) -> None:
        """Log email processing error"""
        log_data = {
            "event": "email_processing_error",
            "error": error,
            "message_id": message_id,
            "user_email": user_email,
            "operation": "read_email",
        }
        logging.error("Email processing failed", extra=log_data)

    def log_queue_message_received(self, queue_name: str, message_id: str) -> None:
        """Log queue message processing"""
        log_data = {
            "event": "queue_message_received",
            "queue_name": queue_name,
            "message_id": message_id,
            "operation": "queue_processing",
        }
        logging.info("Queue message received", extra=log_data)

    def log_storage_operation(
        self, operation: str, container: str, blob_name: str, success: bool
    ) -> None:
        """Log storage operations"""
        log_data = {
            "event": "storage_operation",
            "operation": operation,
            "container": container,
            "blob_name": blob_name,
            "success": success,
        }
        level = logging.INFO if success else logging.ERROR
        logging.log(level, f"Storage operation: {operation}", extra=log_data)


# Global telemetry manager instance
telemetry_manager = TelemetryManager()
