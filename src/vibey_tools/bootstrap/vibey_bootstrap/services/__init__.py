"""
Service implementations for Azure bootstrap library.

This module contains bootstrap services for application initialization.
"""

from vibey_bootstrap.repositories.enhanced_config_repository import (
    create_enhanced_config_repository as create_enhanced_config_repository,
)
from vibey_bootstrap.services.application_bootstrap import (
    ApplicationBootstrap as ApplicationBootstrap,
)
from vibey_bootstrap.services.application_bootstrap import (
    initialize_application as initialize_application,
)
from vibey_bootstrap.services.bootstrap_logging import BootstrapLogger as BootstrapLogger
from vibey_bootstrap.services.bootstrap_logging import get_bootstrap_logger as get_bootstrap_logger
from vibey_bootstrap.services.telemetry import TelemetryManager as TelemetryManager
from vibey_bootstrap.services.telemetry import telemetry_manager as telemetry_manager

__all__ = [
    "ApplicationBootstrap",
    "initialize_application",
    "create_enhanced_config_repository",
    "BootstrapLogger",
    "get_bootstrap_logger",
    "TelemetryManager",
    "telemetry_manager",
]
