"""
Bootstrap logging configuration for handling initialization before full telemetry setup.

This module provides safe logging functionality that works during the application
bootstrap phase, before configuration is fully loaded and App Insights is configured.
It ensures logging works immediately and transitions smoothly to full telemetry.
"""

import json
import logging
import os

from vibey_bootstrap.services.interfaces.bootstrap_logger_interface import (
    BootstrapLoggerInterface,
)

# Standard LogRecord attributes that should not be included in extra fields output
_STANDARD_LOG_RECORD_ATTRS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "message",
    "module",
    "msecs",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "taskName",
    "thread",
    "threadName",
}


class ExtraFieldsFormatter(logging.Formatter):
    """
    Custom formatter that appends extra fields from log records to the message.

    This ensures that any extra={...} dict passed to logger calls is included
    in the output, making structured logging data visible in console output.
    """

    def format(self, record: logging.LogRecord) -> str:
        # Get the base formatted message
        base_message = super().format(record)

        # Extract extra fields (attributes not in standard LogRecord)
        extra_fields = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _STANDARD_LOG_RECORD_ATTRS
        }

        # Append extra fields if present
        if extra_fields:
            try:
                extra_str = json.dumps(extra_fields, default=str)
                return f"{base_message} | {extra_str}"
            except (TypeError, ValueError):
                # Fallback for non-serializable objects
                return f"{base_message} | {extra_fields}"

        return base_message


class BootstrapLogger(BootstrapLoggerInterface):
    """
    Bootstrap logging manager that provides safe logging before full configuration.

    This class handles the chicken-and-egg problem where:
    1. Configuration loading needs logging
    2. Logging (App Insights) needs configuration

    Solution: Start with basic logging, then upgrade to full telemetry later.
    """

    _configured = False
    _basic_formatter = None

    @classmethod
    def configure_bootstrap_logging(cls, level: str | None = None) -> None:
        """
        Configure basic logging that works before full configuration is loaded.

        This provides immediate, safe logging during application bootstrap.
        Later, telemetry_manager.configure() will enhance it with App Insights.

        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR). If not provided,
                   reads from LOG_LEVEL environment variable, defaulting to INFO.
        """
        if cls._configured:
            return

        # Determine logging level: parameter > env var > default (INFO)
        if level is None:
            level = os.environ.get("LOG_LEVEL", "INFO")

        # Validate the level - default to INFO if invalid
        numeric_level = getattr(logging, level.upper(), None)
        if not isinstance(numeric_level, int):
            numeric_level = logging.INFO
            level = "INFO"

        # Set up basic formatter for bootstrap phase with extra fields support
        cls._basic_formatter = ExtraFieldsFormatter(
            "%(asctime)s - [BOOTSTRAP] - %(name)s - %(levelname)s - %(message)s"
        )

        # Configure root logger with basic settings
        root_logger = logging.getLogger()
        root_logger.setLevel(numeric_level)

        # Ensure we have at least one handler
        if not root_logger.handlers:
            handler = logging.StreamHandler()
            if cls._basic_formatter is not None:
                handler.setFormatter(cls._basic_formatter)
            root_logger.addHandler(handler)
        else:
            # Update existing handlers with bootstrap formatter
            if cls._basic_formatter is not None:
                for handler in root_logger.handlers:  # type: ignore
                    if hasattr(handler, "setFormatter"):
                        handler.setFormatter(cls._basic_formatter)

        cls._configured = True

        # Log bootstrap completion
        bootstrap_logger = logging.getLogger(__name__)
        bootstrap_logger.info(
            "Bootstrap logging configured successfully",
            extra={"phase": "bootstrap", "level": level, "handlers": len(root_logger.handlers)},
        )

    @classmethod
    def is_bootstrap_configured(cls) -> bool:
        """Check if bootstrap logging is configured."""
        return cls._configured

    @classmethod
    def create_logger(cls, name: str) -> logging.Logger:
        """
        Create a logger with bootstrap configuration if not already done.

        Args:
            name: Logger name (typically __name__)

        Returns:
            Configured logger ready for use
        """
        if not cls._configured:
            cls.configure_bootstrap_logging()

        return logging.getLogger(name)


def ensure_bootstrap_logging() -> None:
    """
    Ensure bootstrap logging is configured.

    This is a convenience function that can be called safely multiple times.
    Call this early in your application startup before doing any logging.
    """
    BootstrapLogger.configure_bootstrap_logging()


def get_bootstrap_logger(name: str) -> logging.Logger:
    """
    Get a logger that works during bootstrap phase.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger configured for bootstrap use

    Example:
        from src.infrastructure.bootstrap_logging import get_bootstrap_logger

        logger = get_bootstrap_logger(__name__)
        logger.info("This works before full telemetry setup!")
    """
    return BootstrapLogger.create_logger(name)


# Auto-configure on import if running in Azure Functions
if os.environ.get("FUNCTIONS_WORKER_RUNTIME"):
    ensure_bootstrap_logging()
