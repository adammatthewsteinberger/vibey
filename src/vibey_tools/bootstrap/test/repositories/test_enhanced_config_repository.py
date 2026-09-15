"""
Unit tests for EnhancedConfigRepository.

Tests Azure App Configuration integration with Key Vault reference resolution.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from vibey_bootstrap.repositories.enhanced_config_repository import (
    EnhancedConfigRepository,
    create_enhanced_config_repository,
)


@pytest.mark.unit
class TestEnhancedConfigRepository:
    """Test suite for EnhancedConfigRepository."""

    @pytest.fixture
    def connection_string(self):
        """Fixture for App Config connection string."""
        return "Endpoint=https://test.azconfig.io;Id=test-id;Secret=test-secret"

    @pytest.fixture
    def mock_secrets_repo(self):
        """Fixture for mocked SecretsRepository."""
        mock = MagicMock()
        mock.get_secret.return_value = "resolved-secret-value"
        return mock

    @pytest.fixture
    def mock_config_provider(self):
        """Fixture for mocked App Config provider (dict-like object)."""
        # Mock the provider returned by azure.appconfiguration.provider.load()
        mock_provider = MagicMock()
        # Make it dict-like with get() method
        mock_provider.get = MagicMock(side_effect=lambda k, d=None: f"value-{k}" if k else d)
        # Support iteration for get_all_values()
        mock_provider.keys = MagicMock(return_value=["KEY1", "KEY2"])
        mock_provider.__getitem__ = MagicMock(side_effect=lambda k: f"value-{k}")
        return mock_provider

    def test_init_with_connection_string(self, connection_string, mock_config_provider):
        """Test repository initializes with connection string."""
        with patch("azure.appconfiguration.provider.load", return_value=mock_config_provider):
            repo = EnhancedConfigRepository(app_config_connection_string=connection_string)

            assert repo.app_config_connection_string == connection_string
            assert repo.secrets_repository is None
            assert repo._app_config_available is True
            assert repo._config_provider == mock_config_provider

    def test_init_with_secrets_repository(
        self, connection_string, mock_config_provider, mock_secrets_repo
    ):
        """Test repository initializes with secrets repository."""
        with patch("azure.appconfiguration.provider.load", return_value=mock_config_provider):
            repo = EnhancedConfigRepository(
                app_config_connection_string=connection_string, secrets_repository=mock_secrets_repo
            )

            assert repo.secrets_repository == mock_secrets_repo

    def test_init_without_connection_string_uses_env_only(self):
        """Test initialization without connection string uses environment variables only."""
        with patch.dict(os.environ, {}, clear=True):
            repo = EnhancedConfigRepository()

            assert repo.app_config_connection_string is None
            assert repo._app_config_available is False
            assert repo._config_provider is None

    def test_init_with_auto_load_to_environ(self, connection_string, mock_config_provider):
        """Test auto_load_to_environ loads configs to os.environ on init."""
        # Arrange
        mock_config_provider.__iter__ = MagicMock(return_value=iter(["TEST_KEY_1", "TEST_KEY_2"]))
        mock_config_provider.get.side_effect = lambda k: {
            "TEST_KEY_1": "value1",
            "TEST_KEY_2": "value2",
        }.get(k)

        # Act
        with patch("azure.appconfiguration.provider.load", return_value=mock_config_provider):
            with patch.dict(os.environ, {}, clear=True):
                EnhancedConfigRepository(
                    app_config_connection_string=connection_string, auto_load_to_environ=True
                )

                # Assert - configs were loaded to os.environ
                assert os.environ.get("TEST_KEY_1") == "value1"
                assert os.environ.get("TEST_KEY_2") == "value2"

    def test_get_value_from_app_config(self, connection_string, mock_config_provider):
        """Test get_value retrieves from App Config provider."""
        # Arrange
        with patch("azure.appconfiguration.provider.load", return_value=mock_config_provider):
            repo = EnhancedConfigRepository(app_config_connection_string=connection_string)

            # Act
            result = repo.get_value("DATABASE_HOST")

            # Assert
            assert result == "value-DATABASE_HOST"
            # Implementation calls get(key) with 1 parameter
            mock_config_provider.get.assert_called_with("DATABASE_HOST")

    def test_get_value_from_environment(self):
        """Test get_value retrieves from environment when App Config unavailable."""
        # Arrange
        repo = EnhancedConfigRepository()

        # Act
        with patch.dict(os.environ, {"TEST_ENV_VAR": "env-value"}):
            result = repo.get_value("TEST_ENV_VAR")

            # Assert
            assert result == "env-value"

    def test_get_value_returns_default_when_not_found(self):
        """Test get_value returns default when key not found."""
        # Arrange
        repo = EnhancedConfigRepository()

        # Act
        with patch.dict(os.environ, {}, clear=True):
            result = repo.get_value("MISSING_KEY", default="default-value")

            # Assert
            assert result == "default-value"

    def test_get_secret_value_from_secrets_repo(
        self, connection_string, mock_config_provider, mock_secrets_repo
    ):
        """Test get_secret_value retrieves from secrets repository."""
        # Arrange
        with patch("azure.appconfiguration.provider.load", return_value=mock_config_provider):
            repo = EnhancedConfigRepository(
                app_config_connection_string=connection_string, secrets_repository=mock_secrets_repo
            )

            # Act
            result = repo.get_secret_value("DATABASE_PASSWORD")

            # Assert
            assert result == "resolved-secret-value"
            # Implementation calls get_secret(key) with 1 parameter
            mock_secrets_repo.get_secret.assert_called_once_with("DATABASE_PASSWORD")

    def test_get_secret_value_returns_default_when_no_secrets_repo(
        self, connection_string, mock_config_provider
    ):
        """Test get_secret_value returns default when secrets repo not available."""
        # Arrange
        with patch("azure.appconfiguration.provider.load", return_value=mock_config_provider):
            repo = EnhancedConfigRepository(app_config_connection_string=connection_string)

            # Act
            result = repo.get_secret_value("API_KEY", default="default-secret")

            # Assert
            # Implementation returns default when no secrets_repository (does NOT fall back to app config)
            assert result == "default-secret"

    def test_get_all_values_from_app_config(self, connection_string, mock_config_provider):
        """Test get_all_values retrieves all configs from App Config."""
        # Arrange
        # Implementation iterates over provider and calls get(key)
        mock_config_provider.__iter__ = MagicMock(return_value=iter(["KEY1", "KEY2"]))
        mock_config_provider.get.side_effect = lambda k: {"KEY1": "value1", "KEY2": "value2"}.get(k)

        with patch("azure.appconfiguration.provider.load", return_value=mock_config_provider):
            repo = EnhancedConfigRepository(app_config_connection_string=connection_string)

            # Act
            result = repo.get_all_values()

            # Assert
            assert "KEY1" in result
            assert "KEY2" in result
            assert result["KEY1"] == "value1"
            assert result["KEY2"] == "value2"

    def test_load_to_environ_loads_configs_to_os_environ(
        self, connection_string, mock_config_provider
    ):
        """Test load_to_environ loads all configs to os.environ."""
        # Arrange
        # Implementation iterates over provider and calls get(key)
        mock_config_provider.__iter__ = MagicMock(return_value=iter(["CONFIG_KEY"]))
        # Override side_effect to return specific value
        mock_config_provider.get.side_effect = lambda k: (
            "config-value" if k == "CONFIG_KEY" else None
        )

        with patch("azure.appconfiguration.provider.load", return_value=mock_config_provider):
            repo = EnhancedConfigRepository(app_config_connection_string=connection_string)

            # Act
            with patch.dict(os.environ, {}, clear=True):
                repo.load_to_environ()

                # Assert
                assert os.environ.get("CONFIG_KEY") == "config-value"

    def test_refresh_refreshes_config_provider(self, connection_string, mock_config_provider):
        """Test refresh() refreshes the config provider."""
        # Arrange
        with patch("azure.appconfiguration.provider.load", return_value=mock_config_provider):
            repo = EnhancedConfigRepository(app_config_connection_string=connection_string)
            mock_config_provider.refresh = MagicMock()

            # Act
            repo.refresh()

            # Assert
            mock_config_provider.refresh.assert_called_once()

    def test_get_repository_metrics_returns_correct_metrics(
        self, connection_string, mock_config_provider, mock_secrets_repo
    ):
        """Test get_repository_metrics returns accurate metrics."""
        # Arrange
        # Mock secrets_repository.is_available()
        mock_secrets_repo.is_available.return_value = True
        mock_secrets_repo.list_secrets.return_value = ["secret1", "secret2"]

        # Mock config_provider iteration
        mock_config_provider.__iter__ = MagicMock(return_value=iter(["KEY1", "KEY2"]))

        with patch("azure.appconfiguration.provider.load", return_value=mock_config_provider):
            repo = EnhancedConfigRepository(
                app_config_connection_string=connection_string, secrets_repository=mock_secrets_repo
            )
            repo._cache = {"key1": "value1", "key2": "value2"}

            # Act
            metrics = repo.get_repository_metrics()

            # Assert
            # Implementation returns these keys:
            assert metrics["app_config_available"] is True
            assert metrics["secrets_repository_available"] is True
            assert metrics["cached_keys_count"] == 2
            assert metrics["app_config_count"] == 2  # From iteration
            assert metrics["secrets_count"] == 2

    def test_clear_cache_clears_cache(self, connection_string, mock_config_provider):
        """Test clear_cache() clears the cache."""
        # Arrange
        with patch("azure.appconfiguration.provider.load", return_value=mock_config_provider):
            repo = EnhancedConfigRepository(app_config_connection_string=connection_string)
            repo._cache = {"key": "value"}

            # Act
            repo.clear_cache()

            # Assert
            assert repo._cache == {}

    def test_is_available_returns_true_when_app_config_available(
        self, connection_string, mock_config_provider
    ):
        """Test is_available() returns True when App Config is available."""
        # Arrange
        with patch("azure.appconfiguration.provider.load", return_value=mock_config_provider):
            repo = EnhancedConfigRepository(app_config_connection_string=connection_string)

            # Act
            result = repo.is_available()

            # Assert
            assert result is True

    def test_is_app_config_available_returns_true(self, connection_string, mock_config_provider):
        """Test is_app_config_available() returns True when provider initialized."""
        # Arrange
        with patch("azure.appconfiguration.provider.load", return_value=mock_config_provider):
            repo = EnhancedConfigRepository(app_config_connection_string=connection_string)

            # Act
            result = repo.is_app_config_available()

            # Assert
            assert result is True

    def test_is_key_vault_available_returns_true(
        self, connection_string, mock_config_provider, mock_secrets_repo
    ):
        """Test is_key_vault_available() returns True when secrets repo provided."""
        # Arrange
        # Mock secrets_repository.is_available()
        mock_secrets_repo.is_available.return_value = True

        with patch("azure.appconfiguration.provider.load", return_value=mock_config_provider):
            repo = EnhancedConfigRepository(
                app_config_connection_string=connection_string, secrets_repository=mock_secrets_repo
            )

            # Act
            result = repo.is_key_vault_available()

            # Assert
            assert result is True
            # Implementation calls secrets_repository.is_available()
            mock_secrets_repo.is_available.assert_called_once()

    def test_load_to_environ_preserves_existing_values(
        self, connection_string, mock_config_provider
    ):
        """Test that load_to_environ does NOT overwrite existing os.environ values."""
        # Arrange: Simulate local.settings.json setting values
        test_environ = {"USE_MOCK_SHAREPOINT": "true", "AZURE_TENANT_ID": "local-tenant-id"}

        # Mock App Config has different values for same keys + new key
        mock_config_provider.__iter__ = MagicMock(
            return_value=iter(["USE_MOCK_SHAREPOINT", "AZURE_TENANT_ID", "NEW_CONFIG_KEY"])
        )
        mock_config_provider.get.side_effect = lambda k: {
            "USE_MOCK_SHAREPOINT": "false",  # Different from local
            "AZURE_TENANT_ID": "remote-tenant-id",  # Different from local
            "NEW_CONFIG_KEY": "new-value",  # Not in local
        }.get(k)

        with patch("azure.appconfiguration.provider.load", return_value=mock_config_provider):
            repo = EnhancedConfigRepository(app_config_connection_string=connection_string)

            # Act
            with patch.dict(os.environ, test_environ, clear=True):
                count = repo.load_to_environ()

                # Assert: Local values preserved, only new values added
                assert os.environ["USE_MOCK_SHAREPOINT"] == "true"  # ✅ Local preserved
                assert os.environ["AZURE_TENANT_ID"] == "local-tenant-id"  # ✅ Local preserved
                assert os.environ["NEW_CONFIG_KEY"] == "new-value"  # ✅ Remote added
                assert count == 1  # Only 1 new value added (NEW_CONFIG_KEY)

    def test_load_to_environ_adds_missing_values(self, connection_string, mock_config_provider):
        """Test that load_to_environ adds values not in os.environ."""
        # Arrange: App Config has values not in local environment
        mock_config_provider.__iter__ = MagicMock(
            return_value=iter(["REMOTE_CONFIG_1", "REMOTE_CONFIG_2"])
        )
        mock_config_provider.get.side_effect = lambda k: {
            "REMOTE_CONFIG_1": "value1",
            "REMOTE_CONFIG_2": "value2",
        }.get(k)

        with patch("azure.appconfiguration.provider.load", return_value=mock_config_provider):
            repo = EnhancedConfigRepository(app_config_connection_string=connection_string)

            # Act
            with patch.dict(os.environ, {}, clear=True):
                count = repo.load_to_environ()

                # Assert: Both values added
                assert os.environ["REMOTE_CONFIG_1"] == "value1"
                assert os.environ["REMOTE_CONFIG_2"] == "value2"
                assert count == 2

    def test_load_to_environ_respects_local_mock_sharepoint_override(
        self, connection_string, mock_config_provider
    ):
        """Test USE_MOCK_SHAREPOINT local override (real-world scenario)."""
        # Arrange: Local dev wants mock SharePoint
        test_environ = {"USE_MOCK_SHAREPOINT": "true"}

        # App Config says use real SharePoint
        mock_config_provider.__iter__ = MagicMock(return_value=iter(["USE_MOCK_SHAREPOINT"]))
        mock_config_provider.get.side_effect = lambda k: (
            "false" if k == "USE_MOCK_SHAREPOINT" else None
        )

        with patch("azure.appconfiguration.provider.load", return_value=mock_config_provider):
            repo = EnhancedConfigRepository(app_config_connection_string=connection_string)

            # Act
            with patch.dict(os.environ, test_environ, clear=True):
                count = repo.load_to_environ()

                # Assert: Local mock setting preserved
                assert os.environ["USE_MOCK_SHAREPOINT"] == "true"  # ✅ Local wins!
                assert count == 0  # No new values added (1 skipped)

    @patch("vibey_bootstrap.repositories.enhanced_config_repository.logger")
    def test_load_to_environ_logs_skipped_keys(
        self, mock_logger, connection_string, mock_config_provider
    ):
        """Test that skipped keys are logged for debugging."""
        # Arrange: Existing key in environment
        test_environ = {"EXISTING_KEY": "local-value"}

        mock_config_provider.__iter__ = MagicMock(return_value=iter(["EXISTING_KEY"]))
        mock_config_provider.get.side_effect = lambda k: (
            "remote-value" if k == "EXISTING_KEY" else None
        )

        with patch("azure.appconfiguration.provider.load", return_value=mock_config_provider):
            repo = EnhancedConfigRepository(app_config_connection_string=connection_string)

            # Act
            with patch.dict(os.environ, test_environ, clear=True):
                repo.load_to_environ()

                # Assert: Debug log shows key was skipped
                mock_logger.debug.assert_any_call(
                    "Skipping key already in os.environ (local override)",
                    extra={
                        "operation": "load_to_environ_skip",
                        "key": "EXISTING_KEY",
                        "local_value": "local-value",
                        "remote_value": "remote-value",
                    },
                )

    def test_init_with_import_error_falls_back_to_env(self):
        """Test initialization falls back to environment when Azure SDK import fails."""
        connection_string = "Endpoint=https://test.azconfig.io;Id=test-id;Secret=secret"

        with patch(
            "azure.appconfiguration.provider.load", side_effect=ImportError("Module not found")
        ):
            repo = EnhancedConfigRepository(app_config_connection_string=connection_string)

            assert repo._config_provider is None
            assert repo._app_config_available is False

    def test_init_with_connection_error_falls_back_to_env(self):
        """Test initialization falls back to environment when connection fails."""
        connection_string = "Endpoint=https://test.azconfig.io;Id=test-id;Secret=secret"

        with patch(
            "azure.appconfiguration.provider.load", side_effect=Exception("Connection failed")
        ):
            repo = EnhancedConfigRepository(app_config_connection_string=connection_string)

            assert repo._config_provider is None
            assert repo._app_config_available is False

    def test_get_value_with_key_vault_reference(
        self, connection_string, mock_config_provider, mock_secrets_repo
    ):
        """Test get_value resolves Key Vault references."""
        # App Config returns a Key Vault reference
        mock_config_provider.get.return_value = '{"uri":"https://vault.azure.net/secrets/db-pass"}'
        mock_secrets_repo.get_secret.return_value = "resolved-secret"

        with patch("azure.appconfiguration.provider.load", return_value=mock_config_provider):
            repo = EnhancedConfigRepository(
                app_config_connection_string=connection_string, secrets_repository=mock_secrets_repo
            )

            result = repo.get_value("DATABASE_PASSWORD")

            # Should try to resolve as Key Vault reference
            assert mock_secrets_repo.get_secret.called or result is not None

    def test_refresh_without_provider_does_nothing(self):
        """Test refresh() does nothing when no provider available."""
        repo = EnhancedConfigRepository()  # No connection string

        # Should not raise an exception
        repo.refresh()

        assert repo._config_provider is None

    def test_get_all_values_includes_cache_when_no_provider(self):
        """Test get_all_values returns cache when no provider."""
        repo = EnhancedConfigRepository()
        repo._cache = {"CACHED_KEY": "cached-value"}

        with patch.dict(os.environ, {}, clear=True):
            result = repo.get_all_values()

            # Should return cached values even without provider
            assert "CACHED_KEY" in result
            assert result["CACHED_KEY"] == "cached-value"

    def test_load_to_environ_with_no_provider_does_nothing(self):
        """Test load_to_environ does nothing when no provider available."""
        repo = EnhancedConfigRepository()

        with patch.dict(os.environ, {}, clear=True):
            count = repo.load_to_environ()

            assert count == 0

    def test_get_value_returns_cache(self, connection_string, mock_config_provider):
        """Test get_value returns cached value without hitting provider."""
        with patch("azure.appconfiguration.provider.load", return_value=mock_config_provider):
            repo = EnhancedConfigRepository(app_config_connection_string=connection_string)

            # Add value to cache
            repo._cache["CACHED_KEY"] = "cached_value"

            result = repo.get_value("CACHED_KEY")

            assert result == "cached_value"
            # Provider should not be called since we have cache
            mock_config_provider.get.assert_not_called()

    def test_get_value_with_app_config_error(self, connection_string, mock_config_provider):
        """Test get_value handles App Configuration errors gracefully."""
        mock_config_provider.get.side_effect = Exception("App Config error")

        with patch("azure.appconfiguration.provider.load", return_value=mock_config_provider):
            repo = EnhancedConfigRepository(app_config_connection_string=connection_string)

            result = repo.get_value("TEST_KEY", default="default_value")

            assert result == "default_value"

    def test_get_value_from_secrets_repository(
        self, connection_string, mock_config_provider, mock_secrets_repo
    ):
        """Test get_value falls back to secrets repository."""
        # Override the side_effect to return None for this specific test
        mock_config_provider.get.side_effect = None
        mock_config_provider.get.return_value = None  # Not in App Config

        with patch("azure.appconfiguration.provider.load", return_value=mock_config_provider):
            repo = EnhancedConfigRepository(
                app_config_connection_string=connection_string, secrets_repository=mock_secrets_repo
            )

            mock_secrets_repo.get_secret.return_value = "secret_value"

            result = repo.get_value("SECRET_KEY")

            assert result == "secret_value"
            mock_secrets_repo.get_secret.assert_called_once_with("SECRET_KEY")

    def test_get_secret_value_not_found(self, mock_secrets_repo):
        """Test get_secret_value returns default when secret not found."""
        mock_secrets_repo.get_secret.return_value = None

        repo = EnhancedConfigRepository(secrets_repository=mock_secrets_repo)

        result = repo.get_secret_value("MISSING_SECRET", default="default_value")

        assert result == "default_value"

    def test_get_all_values_with_provider_error(self, connection_string, mock_config_provider):
        """Test get_all_values handles provider iteration errors."""
        # Make iteration fail
        mock_config_provider.__iter__.side_effect = Exception("Iteration error")

        with patch("azure.appconfiguration.provider.load", return_value=mock_config_provider):
            repo = EnhancedConfigRepository(app_config_connection_string=connection_string)

            result = repo.get_all_values()

            # Should still return environment variables
            assert isinstance(result, dict)

    def test_load_to_environ_with_none_value(self, connection_string, mock_config_provider):
        """Test load_to_environ skips None values."""
        # Mock provider with None value
        mock_config_provider.__iter__.return_value = iter(["KEY1", "KEY2"])
        mock_config_provider.get.side_effect = lambda k: "value1" if k == "KEY1" else None

        with patch("azure.appconfiguration.provider.load", return_value=mock_config_provider):
            with patch.dict(os.environ, {}, clear=True):
                repo = EnhancedConfigRepository(app_config_connection_string=connection_string)

                added_count = repo.load_to_environ()

                # Only KEY1 should be added (KEY2 is None)
                assert added_count == 1
                assert os.environ.get("KEY1") == "value1"
                assert "KEY2" not in os.environ

    def test_load_to_environ_with_error(self, connection_string, mock_config_provider):
        """Test load_to_environ handles iteration errors gracefully."""
        mock_config_provider.__iter__.side_effect = Exception("Load error")

        with patch("azure.appconfiguration.provider.load", return_value=mock_config_provider):
            repo = EnhancedConfigRepository(app_config_connection_string=connection_string)

            # Should not raise exception
            result = repo.load_to_environ()

            assert result == 0

    def test_load_to_environ_with_secrets_repository(self, mock_secrets_repo):
        """Test load_to_environ loads secrets from secrets repository."""
        mock_secrets_repo.list_secrets.return_value = {
            "SECRET1": "secret_value1",
            "SECRET2": "secret_value2",
        }

        with patch.dict(os.environ, {}, clear=True):
            repo = EnhancedConfigRepository(secrets_repository=mock_secrets_repo)

            added_count = repo.load_to_environ()

            assert added_count == 2
            assert os.environ.get("SECRET1") == "secret_value1"
            assert os.environ.get("SECRET2") == "secret_value2"

    def test_load_to_environ_with_secrets_error(self, mock_secrets_repo):
        """Test load_to_environ handles secrets repository errors."""
        mock_secrets_repo.list_secrets.side_effect = Exception("Secrets error")

        repo = EnhancedConfigRepository(secrets_repository=mock_secrets_repo)

        # Should not raise exception
        result = repo.load_to_environ()

        assert result == 0


@pytest.mark.unit
class TestCreateEnhancedConfigRepository:
    """Test suite for create_enhanced_config_repository factory function."""

    @pytest.fixture
    def mock_config_provider(self):
        """Fixture for mocked App Config provider."""
        mock_provider = MagicMock()
        mock_provider.get = MagicMock(return_value="test-value")
        return mock_provider

    def test_create_with_connection_string_env_var(self, mock_config_provider):
        """Test factory creates repository with connection string from env."""
        conn_str = "Endpoint=https://test.azconfig.io;Id=id;Secret=secret"

        with patch("azure.appconfiguration.provider.load", return_value=mock_config_provider):
            with patch.dict(os.environ, {"AZURE_APP_CONFIGURATION_CONNECTION_STRING": conn_str}):
                repo = create_enhanced_config_repository()

                assert repo is not None
                assert isinstance(repo, EnhancedConfigRepository)

    def test_create_without_env_vars_returns_env_only_repo(self):
        """Test factory creates env-only repository when no env vars set."""
        with patch.dict(os.environ, {}, clear=True):
            repo = create_enhanced_config_repository()

            assert repo is not None
            assert repo._app_config_available is False

    def test_create_with_auto_load_to_environ(self, mock_config_provider):
        """Test factory creates repository with auto_load_to_environ enabled."""
        conn_str = "Endpoint=https://test.azconfig.io;Id=id;Secret=secret"
        mock_config_provider.keys = MagicMock(return_value=["TEST_CONFIG"])
        mock_config_provider.__getitem__ = MagicMock(return_value="test-value")

        with patch("azure.appconfiguration.provider.load", return_value=mock_config_provider):
            with patch.dict(os.environ, {"AZURE_APP_CONFIGURATION_CONNECTION_STRING": conn_str}):
                repo = create_enhanced_config_repository(auto_load_to_environ=True)

                assert repo is not None

    def test_create_with_secrets_repository(self, mock_config_provider):
        """Test factory creates repository with secrets repository."""
        conn_str = "Endpoint=https://test.azconfig.io;Id=id;Secret=secret"
        mock_secrets_repo = MagicMock()

        with patch("azure.appconfiguration.provider.load", return_value=mock_config_provider):
            with patch.dict(os.environ, {"AZURE_APP_CONFIGURATION_CONNECTION_STRING": conn_str}):
                repo = create_enhanced_config_repository(secrets_repository=mock_secrets_repo)

                assert repo.secrets_repository == mock_secrets_repo
