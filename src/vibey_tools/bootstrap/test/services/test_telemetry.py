"""
Unit Tests for TelemetryManager.

Tests telemetry manager upgrade functionality and Application Insights integration.
"""

import os
from unittest.mock import Mock

from vibey_bootstrap.services.telemetry import telemetry_manager


class TestTelemetryManagerUpgrade:
    """Test TelemetryManager upgrade functionality."""

    def setup_method(self):
        """Set up test environment before each test."""
        # Store original environment
        self.original_env = os.environ.copy()

        # Store original telemetry state
        self.original_configured = getattr(telemetry_manager, "_configured", False)
        self.original_tracer = getattr(telemetry_manager, "tracer", None)

        # Reset telemetry state
        telemetry_manager._configured = False
        telemetry_manager.tracer = None

    def teardown_method(self):
        """Clean up test environment after each test."""
        # Restore environment
        os.environ.clear()
        os.environ.update(self.original_env)

        # Restore telemetry state
        telemetry_manager._configured = self.original_configured
        telemetry_manager.tracer = self.original_tracer

    def test_configure_with_connection_string(self):
        """Test configure with App Insights connection string."""
        # Red: Write the test first
        # Arrange
        connection_string = "InstrumentationKey=test-key;IngestionEndpoint=https://test.endpoint"

        # Act - Since Azure Monitor may not be available in test environment,
        # this should fallback gracefully to basic logging
        result = telemetry_manager.configure(connection_string=connection_string)

        # Assert
        assert result is True, "Configure should return True even with fallback"
        assert telemetry_manager._configured is True, "Should be marked as configured"

    def test_configure_without_connection_string(self):
        """Test configure without connection string falls back to console."""
        # Red: Test graceful fallback when no connection string
        # Arrange - Ensure no connection string in environment
        os.environ.pop("APPLICATIONINSIGHTS_CONNECTION_STRING", None)

        # Act
        result = telemetry_manager.configure(connection_string=None)

        # Assert - Should succeed with basic logging fallback
        assert result is True, "Configure should return True with fallback"
        assert telemetry_manager._configured is True, "Should be marked as configured"
        assert telemetry_manager.tracer is None, "Should not have App Insights tracer"

    def test_configure_with_allow_reconfigure(self):
        """Test that configure supports allow_reconfigure parameter."""
        # Red: Test reconfiguration behavior
        # Arrange - Configure once
        telemetry_manager.configure(connection_string=None)
        assert telemetry_manager._configured is True

        # Act - Try to configure again without allow_reconfigure
        result_without_flag = telemetry_manager.configure(connection_string="test")

        # Assert - Should return True but not reconfigure
        assert result_without_flag is True, "Should return True (already configured)"

        # Act - Try to configure with allow_reconfigure=True
        result_with_flag = telemetry_manager.configure(
            connection_string="test", allow_reconfigure=True
        )

        # Assert - Should reconfigure
        assert result_with_flag is True, "Should return True after reconfiguration"
        assert telemetry_manager._configured is True

    def test_try_upgrade_from_config_no_tracer_initially(self):
        """Test upgrade when no tracer configured initially."""
        # Red: Test upgrade attempt when starting with basic logging
        # Arrange - Start with basic logging (no tracer)
        telemetry_manager.configure(connection_string=None)
        assert telemetry_manager.tracer is None, "Should start without tracer"

        # Mock config repository that has connection string
        # Note: Uses get_value() to check env vars first, not get_secret_value()
        mock_config_repo = Mock()
        mock_config_repo.get_value.return_value = "InstrumentationKey=test"

        # Act
        upgrade_attempted = telemetry_manager.try_upgrade_from_config(mock_config_repo)

        # Assert - Should attempt upgrade
        assert upgrade_attempted is True, "Should attempt upgrade when connection string available"
        mock_config_repo.get_value.assert_called_once_with("APPLICATIONINSIGHTS_CONNECTION_STRING")

    def test_try_upgrade_from_config_no_connection_string(self):
        """Test upgrade when no connection string in config."""
        # Red: Test upgrade when config has no connection string
        # Arrange - Start with basic logging
        telemetry_manager.configure(connection_string=None)
        assert telemetry_manager.tracer is None

        # Mock config repository that returns None for connection string
        # Note: Uses get_value() first, then get_secret_value() as fallback
        mock_config_repo = Mock()
        mock_config_repo.get_value.return_value = None
        mock_config_repo.get_secret_value.return_value = None

        # Act
        upgrade_attempted = telemetry_manager.try_upgrade_from_config(mock_config_repo)

        # Assert - Should not attempt upgrade
        assert upgrade_attempted is False, "Should not attempt upgrade without connection string"
        mock_config_repo.get_value.assert_called_once_with("APPLICATIONINSIGHTS_CONNECTION_STRING")
        # Should also try get_secret_value as fallback
        mock_config_repo.get_secret_value.assert_called_once_with(
            "APPLICATIONINSIGHTS_CONNECTION_STRING"
        )

    def test_try_upgrade_from_config_with_error(self):
        """Test upgrade handles configuration errors gracefully."""
        # Red: Test error handling during upgrade
        # Arrange - Start with basic logging
        telemetry_manager.configure(connection_string=None)
        assert telemetry_manager.tracer is None

        # Mock config repository that raises exception on get_value
        mock_config_repo = Mock()
        mock_config_repo.get_value.side_effect = Exception("Config error")

        # Act - Should not raise, should handle gracefully
        upgrade_attempted = telemetry_manager.try_upgrade_from_config(mock_config_repo)

        # Assert - Should return False and continue with basic logging
        assert upgrade_attempted is False, "Should return False on error"
        assert telemetry_manager.tracer is None, "Should still have no tracer"

    def test_try_upgrade_from_config_configure_fails(self):
        """Test upgrade when configure fails."""
        # Red: Test upgrade when configure succeeds but tracer not set
        # Arrange - Start with basic logging
        telemetry_manager.configure(connection_string=None)
        assert telemetry_manager.tracer is None

        # Mock config repository with connection string found via get_value
        mock_config_repo = Mock()
        mock_config_repo.get_value.return_value = "InstrumentationKey=test"

        # Act - Configure will succeed but not set tracer (telemetry not available)
        upgrade_attempted = telemetry_manager.try_upgrade_from_config(mock_config_repo)

        # Assert - Should return True (upgrade was attempted)
        # Tracer may or may not be set depending on telemetry availability
        assert upgrade_attempted is True, "Should return True when upgrade attempted"

    def test_try_upgrade_from_config_already_has_tracer(self):
        """Test that upgrade returns False when tracer already configured."""
        # Red: Test no upgrade when already using App Insights
        # Arrange - Mock that we already have a tracer
        telemetry_manager.tracer = Mock()  # Simulate existing tracer

        # Mock config repository
        mock_config_repo = Mock()

        # Act
        upgrade_attempted = telemetry_manager.try_upgrade_from_config(mock_config_repo)

        # Assert - Should return False (no upgrade needed)
        assert upgrade_attempted is False, "Should not upgrade when tracer already exists"
        # Should not even call get_secret_value
        mock_config_repo.get_secret_value.assert_not_called()

    def test_get_tracer_method(self):
        """Test get_tracer method returns tracer."""
        # Red: Test get_tracer method
        # Arrange - Set a mock tracer
        mock_tracer = Mock()
        telemetry_manager.tracer = mock_tracer

        # Act
        retrieved_tracer = telemetry_manager.get_tracer()

        # Assert
        assert retrieved_tracer is mock_tracer, "Should return the configured tracer"

    def test_create_span_without_tracer(self):
        """Test create_span returns None without tracer."""
        # Red: Test create_span when no tracer configured
        # Arrange - Ensure no tracer
        telemetry_manager.tracer = None

        # Act
        span = telemetry_manager.create_span("test_span", attributes={"key": "value"})

        # Assert - Should return None gracefully
        assert span is None, "Should return None when no tracer configured"

    def test_structured_logging_methods(self):
        """Test structured logging methods work without errors."""
        # Red: Test that logging methods don't raise exceptions
        # Arrange
        telemetry_manager.configure(connection_string=None)

        # Act & Assert - Should not raise exceptions
        telemetry_manager.log_email_processing_start(
            message_id="test-123", user_email="test@example.com"
        )
        telemetry_manager.log_email_processing_success(
            message_id="test-123", user_email="test@example.com", processing_time_ms=100
        )
        telemetry_manager.log_email_processing_error(
            error="Test error", message_id="test-123", user_email="test@example.com"
        )
        telemetry_manager.log_queue_message_received(queue_name="test-queue", message_id="msg-123")
        telemetry_manager.log_storage_operation(
            operation="upload", container="test-container", blob_name="test.txt", success=True
        )

        # All calls should succeed without exceptions
        assert True, "All structured logging methods should work"
