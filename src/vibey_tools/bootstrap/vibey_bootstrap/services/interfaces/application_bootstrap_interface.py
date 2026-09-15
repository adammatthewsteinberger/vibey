"""
Interface for application bootstrap orchestrator.

This interface defines the contract for the ApplicationBootstrap class that
handles the complete startup flow including logging, configuration, and telemetry.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.repositories.enhanced_config_repository import EnhancedConfigRepositoryInterface


class ApplicationBootstrapInterface(ABC):
    """
    Interface for application bootstrap orchestrator.

    Defines the contract for handling the complete application startup sequence
    with proper logging flow.
    """

    @abstractmethod
    def initialize(self) -> "EnhancedConfigRepositoryInterface":
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
        pass

    @abstractmethod
    def get_config_repository(self) -> Optional["EnhancedConfigRepositoryInterface"]:
        """
        Get the configured repository after bootstrap.

        Returns:
            The enhanced configuration repository if bootstrap is complete, None otherwise
        """
        pass

    @abstractmethod
    def is_bootstrap_completed(self) -> bool:
        """
        Check if bootstrap process has completed successfully.

        Returns:
            True if bootstrap completed successfully, False otherwise
        """
        pass
