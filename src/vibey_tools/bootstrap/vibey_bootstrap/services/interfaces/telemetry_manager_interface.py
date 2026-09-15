"""
Interface for telemetry management.

This interface defines the contract for the TelemetryManager class that manages
Application Insights telemetry and structured logging.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from vibey_bootstrap.repositories.interfaces.enhanced_config_repository_interface import (
        EnhancedConfigRepositoryInterface,
    )


class TelemetryManagerInterface(ABC):
    """
    Interface for telemetry manager.

    Defines the contract for managing Application Insights telemetry and
    structured logging throughout the application.
    """

    @abstractmethod
    def configure(
        self, connection_string: str | None = None, allow_reconfigure: bool = False
    ) -> bool:
        """
        Configure Application Insights telemetry with support for bootstrap flow reconfiguration.

        Args:
            connection_string: App Insights connection string
            allow_reconfigure: If True, allows reconfiguration even if already configured

        Returns:
            True if configuration succeeded, False otherwise
        """
        pass

    @abstractmethod
    def try_upgrade_from_config(
        self, config_repository: "EnhancedConfigRepositoryInterface"
    ) -> bool:
        """
        Attempt to upgrade from basic logging to App Insights after config is loaded.

        This method is called after configuration loading to check if an App Insights
        connection string is now available from App Config/Key Vault that wasn't
        available during initial bootstrap.

        Args:
            config_repository: Enhanced config repository to check for connection string

        Returns:
            True if upgrade was attempted (success or failure), False if no upgrade needed
        """
        pass

    @abstractmethod
    def get_tracer(self) -> Any:
        """
        Get the configured tracer.

        Returns:
            The OpenTelemetry tracer instance if configured, None otherwise
        """
        pass

    @abstractmethod
    def create_span(self, name: str, attributes: dict[str, Any] | None = None) -> Any:
        """
        Create a new trace span.

        Args:
            name: Name of the span
            attributes: Optional attributes to attach to the span

        Returns:
            Span instance if telemetry is configured, None otherwise
        """
        pass

    @abstractmethod
    def log_email_processing_start(
        self, message_id: str | None = None, user_email: str | None = None
    ) -> None:
        """
        Log email processing start with structured data.

        Args:
            message_id: Email message ID
            user_email: User email address
        """
        pass

    @abstractmethod
    def log_email_processing_success(
        self, message_id: str, user_email: str, processing_time_ms: int
    ) -> None:
        """
        Log successful email processing.

        Args:
            message_id: Email message ID
            user_email: User email address
            processing_time_ms: Processing time in milliseconds
        """
        pass

    @abstractmethod
    def log_email_processing_error(
        self, error: str, message_id: str | None = None, user_email: str | None = None
    ) -> None:
        """
        Log email processing error.

        Args:
            error: Error message
            message_id: Email message ID (if available)
            user_email: User email address (if available)
        """
        pass

    @abstractmethod
    def log_queue_message_received(self, queue_name: str, message_id: str) -> None:
        """
        Log queue message processing.

        Args:
            queue_name: Name of the queue
            message_id: Message ID
        """
        pass

    @abstractmethod
    def log_storage_operation(
        self, operation: str, container: str, blob_name: str, success: bool
    ) -> None:
        """
        Log storage operations.

        Args:
            operation: Type of storage operation
            container: Storage container name
            blob_name: Blob name
            success: Whether the operation succeeded
        """
        pass
