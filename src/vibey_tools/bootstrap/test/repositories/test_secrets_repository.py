"""
Unit tests for SecretsRepository.

Tests Azure Key Vault integration for secure secrets management.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from vibey_bootstrap.repositories.secrets_repository import SecretsRepository


@pytest.mark.unit
class TestSecretsRepository:
    """Test suite for SecretsRepository."""

    def test_init_without_vault_url_uses_env_only(self):
        """Test initialization without vault URL uses environment variables only."""
        with patch.dict(os.environ, {}, clear=True):
            repo = SecretsRepository()

            assert repo.vault_url is None
            assert repo._key_vault_available is False
            assert repo._secret_client is None

    def test_init_with_vault_url(self):
        """Test initialization with vault URL."""
        vault_url = "https://test.vault.azure.net"
        mock_secret_client = MagicMock()

        with patch("azure.keyvault.secrets.SecretClient", return_value=mock_secret_client):
            with patch("azure.identity.DefaultAzureCredential"):
                repo = SecretsRepository(vault_url=vault_url)

                assert repo.vault_url == vault_url
                assert repo._key_vault_available is True
                assert repo._secret_client == mock_secret_client

    def test_get_secret_from_environment(self):
        """Test get_secret retrieves from environment when Key Vault unavailable."""
        repo = SecretsRepository()

        with patch.dict(os.environ, {"TEST_SECRET": "env-secret-value"}):
            result = repo.get_secret("TEST_SECRET")

            assert result == "env-secret-value"

    def test_get_secret_returns_none_when_not_found(self):
        """Test get_secret returns None when secret not found."""
        repo = SecretsRepository()

        with patch.dict(os.environ, {}, clear=True):
            result = repo.get_secret("MISSING_SECRET")

            assert result is None

    def test_get_secret_from_key_vault(self):
        """Test get_secret retrieves from Key Vault when available."""
        vault_url = "https://test.vault.azure.net"
        mock_secret_client = MagicMock()
        mock_secret = MagicMock()
        mock_secret.value = "vault-secret-value"
        mock_secret_client.get_secret.return_value = mock_secret

        with patch("azure.keyvault.secrets.SecretClient", return_value=mock_secret_client):
            with patch("azure.identity.DefaultAzureCredential"):
                repo = SecretsRepository(vault_url=vault_url)

                result = repo.get_secret("database-password")

                assert result == "vault-secret-value"
                mock_secret_client.get_secret.assert_called_once_with("database-password")

    def test_is_available_returns_true_when_key_vault_available(self):
        """Test is_available() returns True when Key Vault is available."""
        vault_url = "https://test.vault.azure.net"
        mock_secret_client = MagicMock()

        with patch("azure.keyvault.secrets.SecretClient", return_value=mock_secret_client):
            with patch("azure.identity.DefaultAzureCredential"):
                repo = SecretsRepository(vault_url=vault_url)

                result = repo.is_available()

                assert result is True

    def test_is_available_returns_false_when_no_key_vault(self):
        """Test is_available() returns False when Key Vault not available."""
        repo = SecretsRepository()

        result = repo.is_available()

        assert result is False

    def test_clear_cache_clears_cache(self):
        """Test clear_cache() clears the secrets cache."""
        repo = SecretsRepository()
        repo._cache = {"secret1": "value1"}

        repo.clear_cache()

        assert repo._cache == {}

    def test_init_with_import_error_falls_back_to_env(self):
        """Test initialization falls back to environment when Azure SDK import fails."""
        vault_url = "https://test.vault.azure.net"

        with patch(
            "azure.keyvault.secrets.SecretClient", side_effect=ImportError("Module not found")
        ):
            repo = SecretsRepository(vault_url=vault_url)

            assert repo.vault_url == vault_url
            assert repo._key_vault_available is False
            assert repo._secret_client is None

    def test_init_with_auth_error_falls_back_to_env(self):
        """Test initialization falls back to environment when Azure auth fails."""
        vault_url = "https://test.vault.azure.net"

        with patch("azure.identity.DefaultAzureCredential", side_effect=Exception("Auth failed")):
            repo = SecretsRepository(vault_url=vault_url)

            assert repo.vault_url == vault_url
            assert repo._key_vault_available is False
            assert repo._secret_client is None

    def test_get_secret_with_key_vault_error_falls_back_to_env(self):
        """Test get_secret falls back to environment when Key Vault call fails."""
        vault_url = "https://test.vault.azure.net"
        mock_secret_client = MagicMock()
        mock_secret_client.get_secret.side_effect = Exception("Key Vault error")

        with patch("azure.keyvault.secrets.SecretClient", return_value=mock_secret_client):
            with patch("azure.identity.DefaultAzureCredential"):
                with patch.dict(os.environ, {"TEST_SECRET": "fallback-value"}):
                    repo = SecretsRepository(vault_url=vault_url)
                    result = repo.get_secret("TEST_SECRET")

                    assert result == "fallback-value"

    def test_get_secret_uses_cache(self):
        """Test get_secret uses cached value when available."""
        vault_url = "https://test.vault.azure.net"
        mock_secret_client = MagicMock()

        with patch("azure.keyvault.secrets.SecretClient", return_value=mock_secret_client):
            with patch("azure.identity.DefaultAzureCredential"):
                repo = SecretsRepository(vault_url=vault_url)
                repo._cache["CACHED_SECRET"] = "cached-value"

                result = repo.get_secret("CACHED_SECRET")

                assert result == "cached-value"
                mock_secret_client.get_secret.assert_not_called()

    def test_get_secret_with_hyphen_tries_underscore_in_env(self):
        """Test get_secret tries underscore variant when looking in environment."""
        repo = SecretsRepository()

        # Secret name has hyphen, but env var uses underscore
        with patch.dict(os.environ, {"DATABASE_PASSWORD": "env-value"}):
            result = repo.get_secret("DATABASE-PASSWORD")

            assert result == "env-value"

    def test_get_secret_caches_value_from_key_vault(self):
        """Test get_secret caches values retrieved from Key Vault."""
        vault_url = "https://test.vault.azure.net"
        mock_secret_client = MagicMock()
        mock_secret = MagicMock()
        mock_secret.value = "vault-value"
        mock_secret_client.get_secret.return_value = mock_secret

        with patch("azure.keyvault.secrets.SecretClient", return_value=mock_secret_client):
            with patch("azure.identity.DefaultAzureCredential"):
                repo = SecretsRepository(vault_url=vault_url)

                # First call - should hit Key Vault
                result1 = repo.get_secret("MY_SECRET")
                assert result1 == "vault-value"
                assert mock_secret_client.get_secret.call_count == 1

                # Second call - should use cache
                result2 = repo.get_secret("MY_SECRET")
                assert result2 == "vault-value"
                assert mock_secret_client.get_secret.call_count == 1  # Not called again

    def test_get_secret_caches_value_from_environment(self):
        """Test get_secret caches values retrieved from environment."""
        repo = SecretsRepository()

        with patch.dict(os.environ, {"ENV_SECRET": "env-value"}):
            # First call
            result1 = repo.get_secret("ENV_SECRET")
            assert result1 == "env-value"
            assert "ENV_SECRET" in repo._cache

            # Second call should use cache
            result2 = repo.get_secret("ENV_SECRET")
            assert result2 == "env-value"

    def test_set_secret_without_key_vault_returns_false(self):
        """Test set_secret returns False when Key Vault not available."""
        repo = SecretsRepository()  # No vault URL

        result = repo.set_secret("MY_SECRET", "secret-value")

        assert result is False

    def test_set_secret_with_key_vault(self):
        """Test set_secret stores secret in Key Vault."""
        vault_url = "https://test.vault.azure.net"
        mock_secret_client = MagicMock()
        mock_secret_client.set_secret.return_value = MagicMock()

        with patch("azure.keyvault.secrets.SecretClient", return_value=mock_secret_client):
            with patch("azure.identity.DefaultAzureCredential"):
                repo = SecretsRepository(vault_url=vault_url)

                result = repo.set_secret("MY-SECRET", "secret-value")

                assert result is True
                mock_secret_client.set_secret.assert_called_once_with("MY-SECRET", "secret-value")

    def test_set_secret_with_error(self):
        """Test set_secret handles errors gracefully."""
        vault_url = "https://test.vault.azure.net"
        mock_secret_client = MagicMock()
        mock_secret_client.set_secret.side_effect = Exception("Set secret failed")

        with patch("azure.keyvault.secrets.SecretClient", return_value=mock_secret_client):
            with patch("azure.identity.DefaultAzureCredential"):
                repo = SecretsRepository(vault_url=vault_url)

                result = repo.set_secret("MY-SECRET", "secret-value")

                assert result is False

    def test_delete_secret_without_key_vault_returns_false(self):
        """Test delete_secret returns False when Key Vault not available."""
        repo = SecretsRepository()  # No vault URL

        result = repo.delete_secret("MY_SECRET")

        assert result is False

    def test_delete_secret_with_key_vault(self):
        """Test delete_secret removes secret from Key Vault."""
        vault_url = "https://test.vault.azure.net"
        mock_secret_client = MagicMock()
        mock_poller = MagicMock()
        mock_poller.wait.return_value = None
        mock_secret_client.begin_delete_secret.return_value = mock_poller

        with patch("azure.keyvault.secrets.SecretClient", return_value=mock_secret_client):
            with patch("azure.identity.DefaultAzureCredential"):
                repo = SecretsRepository(vault_url=vault_url)
                # Add to cache first
                repo._cache["MY-SECRET"] = "cached-value"

                result = repo.delete_secret("MY-SECRET")

                assert result is True
                mock_secret_client.begin_delete_secret.assert_called_once_with("MY-SECRET")
                assert "MY-SECRET" not in repo._cache

    def test_delete_secret_with_error(self):
        """Test delete_secret handles errors gracefully."""
        vault_url = "https://test.vault.azure.net"
        mock_secret_client = MagicMock()
        mock_secret_client.begin_delete_secret.side_effect = Exception("Delete failed")

        with patch("azure.keyvault.secrets.SecretClient", return_value=mock_secret_client):
            with patch("azure.identity.DefaultAzureCredential"):
                repo = SecretsRepository(vault_url=vault_url)

                result = repo.delete_secret("MY-SECRET")

                assert result is False

    def test_list_secrets_without_key_vault(self):
        """Test list_secrets returns empty dict when Key Vault not available."""
        repo = SecretsRepository()

        result = repo.list_secrets()

        assert result == {}

    def test_list_secrets_with_key_vault(self):
        """Test list_secrets retrieves secret metadata from Key Vault."""
        vault_url = "https://test.vault.azure.net"
        mock_secret_client = MagicMock()

        # Mock secret properties
        mock_prop1 = MagicMock()
        mock_prop1.name = "secret1"
        mock_prop1.enabled = True

        mock_prop2 = MagicMock()
        mock_prop2.name = "secret2"
        mock_prop2.enabled = False

        mock_secret_client.list_properties_of_secrets.return_value = [mock_prop1, mock_prop2]

        with patch("azure.keyvault.secrets.SecretClient", return_value=mock_secret_client):
            with patch("azure.identity.DefaultAzureCredential"):
                repo = SecretsRepository(vault_url=vault_url)

                result = repo.list_secrets()

                assert len(result) == 2
                assert "secret1" in result
                assert "Key Vault (enabled: True)" in result["secret1"]
                assert "secret2" in result
                assert "Key Vault (enabled: False)" in result["secret2"]

    def test_list_secrets_with_error(self):
        """Test list_secrets handles errors gracefully."""
        vault_url = "https://test.vault.azure.net"
        mock_secret_client = MagicMock()
        mock_secret_client.list_properties_of_secrets.side_effect = Exception("List failed")

        with patch("azure.keyvault.secrets.SecretClient", return_value=mock_secret_client):
            with patch("azure.identity.DefaultAzureCredential"):
                repo = SecretsRepository(vault_url=vault_url)

                result = repo.list_secrets()

                assert result == {}
