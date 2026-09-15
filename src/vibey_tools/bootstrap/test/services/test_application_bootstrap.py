"""
Unit Tests for ApplicationBootstrap.

Tests application bootstrap functionality and circular dependency resolution.
"""

import os
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest


# Pytest fixture to handle module mocking/unmocking at the MODULE level
@pytest.fixture(scope="module", autouse=True)
def mock_config_modules():
    """
    Mock config and secrets modules for ApplicationBootstrap tests.

    This fixture runs once for the entire test module and ensures proper cleanup
    after all tests complete, preventing test pollution for other test files.
    """
    # Store original modules before mocking
    original_enhanced_config = sys.modules.get("src.repositories.enhanced_config_repository")
    original_secrets = sys.modules.get("src.repositories.secrets_repository")

    # Mock the modules
    sys.modules["src.repositories.enhanced_config_repository"] = MagicMock()
    sys.modules["src.repositories.secrets_repository"] = MagicMock()

    # Yield to run tests
    yield

    # Cleanup: Restore original modules after all tests in this module complete
    if original_enhanced_config is not None:
        sys.modules["src.repositories.enhanced_config_repository"] = original_enhanced_config
    elif "src.repositories.enhanced_config_repository" in sys.modules:
        del sys.modules["src.repositories.enhanced_config_repository"]

    if original_secrets is not None:
        sys.modules["src.repositories.secrets_repository"] = original_secrets
    elif "src.repositories.secrets_repository" in sys.modules:
        del sys.modules["src.repositories.secrets_repository"]


from vibey_bootstrap.services.application_bootstrap import ApplicationBootstrap  # noqa: E402


class TestApplicationBootstrap:
    """Test ApplicationBootstrap initialization and phased startup."""

    def setup_method(self):
        """Set up test environment before each test."""
        # Store original environment
        self.original_env = os.environ.copy()

        # Store original telemetry state
        from vibey_bootstrap.services.telemetry import telemetry_manager

        self.original_telemetry_configured = getattr(telemetry_manager, "_configured", False)

        # Reset telemetry state
        telemetry_manager._configured = False

    def teardown_method(self):
        """Clean up test environment after each test."""
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)

        # Restore telemetry state
        from vibey_bootstrap.services.telemetry import telemetry_manager

        telemetry_manager._configured = self.original_telemetry_configured

    def test_bootstrap_initialization(self):
        """Test ApplicationBootstrap initialization."""
        # Red: Write the test first
        # Act
        bootstrap = ApplicationBootstrap()

        # Assert
        assert bootstrap is not None, "Bootstrap should be created"
        assert bootstrap.secrets_repository is None, "Should have no secrets repo by default"
        assert bootstrap.config_repository is None, "Should not have config repo before init"
        assert bootstrap._bootstrap_completed is False, "Should not be completed initially"

    @patch("vibey_bootstrap.services.application_bootstrap.create_enhanced_config_repository")
    @patch("vibey_bootstrap.services.application_bootstrap.telemetry_manager")
    def test_initialize_complete_flow(self, mock_telemetry, mock_create_config):
        """Test complete bootstrap initialization flow."""
        # Red: Test complete bootstrap flow
        # Arrange - Mock telemetry manager
        mock_telemetry.configure.return_value = True
        mock_telemetry.try_upgrade_from_config.return_value = False
        mock_telemetry.tracer = None

        # Mock config repository
        mock_config_repo = Mock()
        mock_config_repo.get_repository_metrics.return_value = {"configs": 10}
        mock_create_config.return_value = mock_config_repo

        # Act
        bootstrap = ApplicationBootstrap()
        config_repo = bootstrap.initialize()

        # Assert
        assert config_repo is not None, "Should return config repository"
        assert bootstrap._bootstrap_completed is True, "Should mark bootstrap as completed"
        assert bootstrap.config_repository is mock_config_repo, "Should store config repo"

        # Verify telemetry was configured
        mock_telemetry.configure.assert_called_once()

        # Verify config repository was created
        mock_create_config.assert_called_once()

        # Verify telemetry upgrade was attempted
        mock_telemetry.try_upgrade_from_config.assert_called_once_with(mock_config_repo)

    @patch("vibey_bootstrap.services.application_bootstrap.create_enhanced_config_repository")
    @patch("vibey_bootstrap.services.application_bootstrap.telemetry_manager")
    def test_initialize_with_app_insights_from_environment(
        self, mock_telemetry, mock_create_config
    ):
        """Test bootstrap when App Insights available from environment."""
        # Red: Test with App Insights in environment
        # Arrange - Set connection string in environment
        os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"] = "InstrumentationKey=test"

        mock_telemetry.configure.return_value = True
        mock_telemetry.tracer = Mock()  # Simulate successful App Insights setup
        mock_telemetry.try_upgrade_from_config.return_value = False

        mock_config_repo = Mock()
        mock_config_repo.get_repository_metrics.return_value = {}
        mock_create_config.return_value = mock_config_repo

        # Act
        bootstrap = ApplicationBootstrap()
        config_repo = bootstrap.initialize()

        # Assert
        assert config_repo is not None, "Should complete successfully"
        assert bootstrap._bootstrap_completed is True
        mock_telemetry.configure.assert_called_once()

    @patch("vibey_bootstrap.services.application_bootstrap.create_enhanced_config_repository")
    @patch("vibey_bootstrap.services.application_bootstrap.telemetry_manager")
    def test_initialize_with_config_loading_error(self, mock_telemetry, mock_create_config):
        """Test bootstrap handling config loading errors."""
        # Red: Test error handling during config loading
        # Arrange - Mock config repository creation to raise exception
        mock_telemetry.configure.return_value = True
        mock_create_config.side_effect = Exception("Config loading failed")

        # Act & Assert - Should raise RuntimeError
        bootstrap = ApplicationBootstrap()
        with pytest.raises(RuntimeError) as exc_info:
            bootstrap.initialize()

        assert "Application bootstrap failed" in str(exc_info.value)
        assert bootstrap._bootstrap_completed is False, "Should not mark as completed on error"

    @patch("vibey_bootstrap.services.application_bootstrap.create_enhanced_config_repository")
    @patch("vibey_bootstrap.services.application_bootstrap.telemetry_manager")
    def test_initialize_telemetry_upgrade_attempted(self, mock_telemetry, mock_create_config):
        """Test that telemetry upgrade is attempted when config available."""
        # Red: Test telemetry upgrade is called
        # Arrange - Start with basic logging
        mock_telemetry.configure.return_value = True
        mock_telemetry.tracer = None  # Start without tracer
        mock_telemetry.try_upgrade_from_config.return_value = True  # Upgrade attempted

        mock_config_repo = Mock()
        mock_config_repo.get_repository_metrics.return_value = {}
        mock_create_config.return_value = mock_config_repo

        # Act
        bootstrap = ApplicationBootstrap()
        config_repo = bootstrap.initialize()

        # Assert
        assert config_repo is not None
        # Verify upgrade was attempted with the config repository
        mock_telemetry.try_upgrade_from_config.assert_called_once_with(mock_config_repo)

    @patch("vibey_bootstrap.services.application_bootstrap.create_enhanced_config_repository")
    @patch("vibey_bootstrap.services.application_bootstrap.telemetry_manager")
    def test_initialize_idempotent(self, mock_telemetry, mock_create_config):
        """Test that initialize can be called multiple times safely."""
        # Red: Test idempotency
        # Arrange
        mock_telemetry.configure.return_value = True
        mock_telemetry.try_upgrade_from_config.return_value = False
        mock_telemetry.tracer = None

        mock_config_repo = Mock()
        mock_config_repo.get_repository_metrics.return_value = {}
        mock_create_config.return_value = mock_config_repo

        bootstrap = ApplicationBootstrap()

        # Act - Call initialize twice
        config_repo_1 = bootstrap.initialize()
        config_repo_2 = bootstrap.initialize()

        # Assert - Should return same repository and not recreate
        assert config_repo_1 is config_repo_2, "Should return same config repo"
        assert bootstrap._bootstrap_completed is True
        # Config repository should only be created once
        assert mock_create_config.call_count == 1, "Should only create config repo once"

    @patch("vibey_bootstrap.services.application_bootstrap.create_enhanced_config_repository")
    @patch("vibey_bootstrap.services.application_bootstrap.telemetry_manager")
    def test_bootstrap_error_logging(self, mock_telemetry, mock_create_config):
        """Test that bootstrap errors are properly logged."""
        # Red: Test error handling and logging
        # Arrange
        mock_telemetry.configure.return_value = True
        mock_create_config.side_effect = Exception("Config error")

        # Act
        bootstrap = ApplicationBootstrap()
        try:
            bootstrap.initialize()
        except RuntimeError:
            pass  # Expected

        # Assert - Bootstrap should not be completed
        assert bootstrap._bootstrap_completed is False
        assert bootstrap.config_repository is None


class TestApplicationBootstrapLogging:
    """Test ApplicationBootstrap logging functionality."""

    @patch("vibey_bootstrap.services.application_bootstrap.create_enhanced_config_repository")
    @patch("vibey_bootstrap.services.application_bootstrap.telemetry_manager")
    def test_get_config_repository_before_init(self, mock_telemetry, mock_create_config):
        """Test get_config_repository returns None before initialization."""
        # Red: Test getter before initialization
        # Arrange
        bootstrap = ApplicationBootstrap()

        # Act
        config_repo = bootstrap.get_config_repository()

        # Assert
        assert config_repo is None, "Should return None before initialization"

    @patch("vibey_bootstrap.services.application_bootstrap.create_enhanced_config_repository")
    @patch("vibey_bootstrap.services.application_bootstrap.telemetry_manager")
    def test_get_config_repository_after_init(self, mock_telemetry, mock_create_config):
        """Test get_config_repository returns repository after initialization."""
        # Red: Test getter after initialization
        # Arrange
        mock_telemetry.configure.return_value = True
        mock_telemetry.try_upgrade_from_config.return_value = False
        mock_telemetry.tracer = None

        mock_config_repo = Mock()
        mock_config_repo.get_repository_metrics.return_value = {}
        mock_create_config.return_value = mock_config_repo

        bootstrap = ApplicationBootstrap()
        bootstrap.initialize()

        # Act
        config_repo = bootstrap.get_config_repository()

        # Assert
        assert config_repo is mock_config_repo, "Should return config repo after init"

    @patch("vibey_bootstrap.services.application_bootstrap.create_enhanced_config_repository")
    @patch("vibey_bootstrap.services.application_bootstrap.telemetry_manager")
    def test_is_bootstrap_completed(self, mock_telemetry, mock_create_config):
        """Test is_bootstrap_completed status tracking."""
        # Red: Test completion status
        # Arrange
        mock_telemetry.configure.return_value = True
        mock_telemetry.try_upgrade_from_config.return_value = False
        mock_telemetry.tracer = None

        mock_config_repo = Mock()
        mock_config_repo.get_repository_metrics.return_value = {}
        mock_create_config.return_value = mock_config_repo

        bootstrap = ApplicationBootstrap()

        # Act & Assert - Before initialization
        assert bootstrap.is_bootstrap_completed() is False

        # Act - Initialize
        bootstrap.initialize()

        # Assert - After initialization
        assert bootstrap.is_bootstrap_completed() is True

    @patch("vibey_bootstrap.services.application_bootstrap.create_enhanced_config_repository")
    @patch("vibey_bootstrap.services.application_bootstrap.telemetry_manager")
    def test_telemetry_upgrade_successful(self, mock_telemetry, mock_create_config):
        """Test successful telemetry upgrade from config."""
        # Arrange - Start without App Insights
        mock_telemetry.configure.return_value = True
        mock_telemetry.tracer = None  # Start without tracer

        # Mock successful upgrade
        def upgrade_telemetry(config_repo):
            mock_telemetry.tracer = Mock()  # Simulate successful upgrade
            return True

        mock_telemetry.try_upgrade_from_config.side_effect = upgrade_telemetry

        mock_config_repo = Mock()
        mock_config_repo.get_repository_metrics.return_value = {}
        mock_create_config.return_value = mock_config_repo

        # Act
        bootstrap = ApplicationBootstrap()
        config_repo = bootstrap.initialize()

        # Assert
        assert config_repo is not None
        assert bootstrap._bootstrap_completed is True
        mock_telemetry.try_upgrade_from_config.assert_called_once_with(mock_config_repo)

    @patch("vibey_bootstrap.services.application_bootstrap.create_enhanced_config_repository")
    @patch("vibey_bootstrap.services.application_bootstrap.telemetry_manager")
    def test_telemetry_upgrade_failed(self, mock_telemetry, mock_create_config):
        """Test telemetry upgrade fails but bootstrap continues."""
        # Arrange
        mock_telemetry.configure.return_value = True
        mock_telemetry.tracer = None

        # Mock failed upgrade (returns True but tracer remains None)
        mock_telemetry.try_upgrade_from_config.return_value = True

        mock_config_repo = Mock()
        mock_config_repo.get_repository_metrics.return_value = {}
        mock_create_config.return_value = mock_config_repo

        # Act - Should complete successfully despite upgrade failure
        bootstrap = ApplicationBootstrap()
        config_repo = bootstrap.initialize()

        # Assert
        assert config_repo is not None
        assert bootstrap._bootstrap_completed is True

    @patch("vibey_bootstrap.services.application_bootstrap.create_enhanced_config_repository")
    @patch("vibey_bootstrap.services.application_bootstrap.telemetry_manager")
    def test_finalize_configuration_with_metrics_error(self, mock_telemetry, mock_create_config):
        """Test finalization continues when metrics retrieval fails."""
        # Arrange
        mock_telemetry.configure.return_value = True
        mock_telemetry.try_upgrade_from_config.return_value = False
        mock_telemetry.tracer = None

        mock_config_repo = Mock()
        mock_config_repo.get_repository_metrics.side_effect = Exception("Metrics error")
        mock_create_config.return_value = mock_config_repo

        # Act - Should complete successfully despite metrics error
        bootstrap = ApplicationBootstrap()
        config_repo = bootstrap.initialize()

        # Assert
        assert config_repo is not None
        assert bootstrap._bootstrap_completed is True

    @patch("vibey_bootstrap.services.application_bootstrap.create_enhanced_config_repository")
    @patch("vibey_bootstrap.services.application_bootstrap.telemetry_manager")
    def test_bootstrap_with_secrets_repository(self, mock_telemetry, mock_create_config):
        """Test bootstrap initialization with secrets repository."""
        # Arrange
        mock_secrets_repo = Mock()
        mock_telemetry.configure.return_value = True
        mock_telemetry.try_upgrade_from_config.return_value = False
        mock_telemetry.tracer = None

        mock_config_repo = Mock()
        mock_config_repo.get_repository_metrics.return_value = {}
        mock_create_config.return_value = mock_config_repo

        # Act
        bootstrap = ApplicationBootstrap(secrets_repository=mock_secrets_repo)
        config_repo = bootstrap.initialize()

        # Assert
        assert bootstrap.secrets_repository is mock_secrets_repo
        assert config_repo is not None
        # Verify secrets repo was passed to config creation
        call_args = mock_create_config.call_args
        assert call_args.kwargs.get("secrets_repository") is mock_secrets_repo

    @patch("vibey_bootstrap.services.application_bootstrap.create_enhanced_config_repository")
    @patch("vibey_bootstrap.services.application_bootstrap.telemetry_manager")
    def test_config_repository_auto_load_enabled(self, mock_telemetry, mock_create_config):
        """Test that config repository is created with auto_load_to_environ=True."""
        # Arrange
        mock_telemetry.configure.return_value = True
        mock_telemetry.try_upgrade_from_config.return_value = False
        mock_telemetry.tracer = None

        mock_config_repo = Mock()
        mock_config_repo.get_repository_metrics.return_value = {}
        mock_create_config.return_value = mock_config_repo

        # Act
        bootstrap = ApplicationBootstrap()
        bootstrap.initialize()

        # Assert - Verify auto_load_to_environ was set to True
        call_args = mock_create_config.call_args
        assert call_args.kwargs.get("auto_load_to_environ") is True


class TestInitializeApplication:
    """Test the initialize_application convenience function."""

    @patch("vibey_bootstrap.services.application_bootstrap.ApplicationBootstrap")
    def test_initialize_application_without_secrets(self, mock_bootstrap_class):
        """Test initialize_application without secrets repository."""
        # Arrange
        mock_bootstrap_instance = Mock()
        mock_config_repo = Mock()
        mock_bootstrap_instance.initialize.return_value = mock_config_repo
        mock_bootstrap_class.return_value = mock_bootstrap_instance

        # Act
        from vibey_bootstrap.services.application_bootstrap import initialize_application

        result = initialize_application()

        # Assert
        assert result is mock_config_repo
        mock_bootstrap_class.assert_called_once_with(secrets_repository=None)
        mock_bootstrap_instance.initialize.assert_called_once()

    @patch("vibey_bootstrap.services.application_bootstrap.ApplicationBootstrap")
    def test_initialize_application_with_secrets(self, mock_bootstrap_class):
        """Test initialize_application with secrets repository."""
        # Arrange
        mock_secrets_repo = Mock()
        mock_bootstrap_instance = Mock()
        mock_config_repo = Mock()
        mock_bootstrap_instance.initialize.return_value = mock_config_repo
        mock_bootstrap_class.return_value = mock_bootstrap_instance

        # Act
        from vibey_bootstrap.services.application_bootstrap import initialize_application

        result = initialize_application(secrets_repository=mock_secrets_repo)

        # Assert
        assert result is mock_config_repo
        mock_bootstrap_class.assert_called_once_with(secrets_repository=mock_secrets_repo)
        mock_bootstrap_instance.initialize.assert_called_once()
