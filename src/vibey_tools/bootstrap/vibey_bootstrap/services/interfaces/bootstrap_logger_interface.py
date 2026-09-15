"""
Interface for bootstrap logging configuration.

This interface defines the contract for the BootstrapLogger class that provides
safe logging functionality during the application bootstrap phase.
"""

import logging
from abc import ABC, abstractmethod


class BootstrapLoggerInterface(ABC):
    """
    Interface for bootstrap logging manager.

    Defines the contract for providing safe logging before full configuration
    is loaded and App Insights is configured.
    """

    @classmethod
    @abstractmethod
    def configure_bootstrap_logging(cls, level: str = "INFO") -> None:
        """
        Configure basic logging that works before full configuration is loaded.

        This provides immediate, safe logging during application bootstrap.
        Later, telemetry_manager.configure() will enhance it with App Insights.

        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        pass

    @classmethod
    @abstractmethod
    def is_bootstrap_configured(cls) -> bool:
        """
        Check if bootstrap logging is configured.

        Returns:
            True if bootstrap logging is configured, False otherwise
        """
        pass

    @classmethod
    @abstractmethod
    def create_logger(cls, name: str) -> logging.Logger:
        """
        Create a logger with bootstrap configuration if not already done.

        Args:
            name: Logger name (typically __name__)

        Returns:
            Configured logger ready for use
        """
        pass
