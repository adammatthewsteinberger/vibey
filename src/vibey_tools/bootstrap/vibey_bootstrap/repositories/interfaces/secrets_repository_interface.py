"""
Interface for Secrets Repository.

Defines contract for accessing secrets from Azure Key Vault or other secret stores.
"""

from abc import ABC, abstractmethod


class SecretsRepositoryInterface(ABC):
    """
    Abstract interface for secrets repository operations.

    This interface defines all secret access operations for integration with
    Azure Key Vault or other secret storage backends.

    Benefits:
    - Abstracts secret storage implementation details from business logic
    - Enables dependency injection and testing with mocks
    - Provides clear contract for secret access operations
    - Supports multiple backends (Key Vault, local files, environment, etc.)
    """

    @abstractmethod
    def get_secret(self, secret_name: str) -> str | None:
        """
        Retrieve a secret value by name.

        Args:
            secret_name: Name of the secret to retrieve

        Returns:
            Optional[str]: Secret value if found, None otherwise

        Raises:
            SecretAccessError: If secret retrieval fails
        """
        pass

    @abstractmethod
    def set_secret(self, secret_name: str, secret_value: str) -> bool:
        """
        Store a secret value (if backend supports writes).

        Args:
            secret_name: Name of the secret
            secret_value: Value to store

        Returns:
            bool: True if successful, False otherwise

        Raises:
            SecretAccessError: If secret storage fails
            NotImplementedError: If backend doesn't support writes
        """
        pass

    @abstractmethod
    def delete_secret(self, secret_name: str) -> bool:
        """
        Delete a secret (if backend supports deletion).

        Args:
            secret_name: Name of the secret to delete

        Returns:
            bool: True if successful, False otherwise

        Raises:
            SecretAccessError: If secret deletion fails
            NotImplementedError: If backend doesn't support deletion
        """
        pass

    @abstractmethod
    def list_secrets(self) -> dict[str, str]:
        """
        List all available secrets (names only for security).

        Returns:
            Dict[str, str]: Dictionary mapping secret names to metadata

        Raises:
            SecretAccessError: If listing fails
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if secrets repository is available and accessible.

        Returns:
            bool: True if repository is accessible, False otherwise
        """
        pass
