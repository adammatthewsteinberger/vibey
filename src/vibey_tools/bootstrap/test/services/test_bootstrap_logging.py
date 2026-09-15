# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""
Unit Tests for BootstrapLogger.

Tests bootstrap logging functionality and circular dependency resolution.
"""

import logging
import os

import pytest

from vibey_bootstrap.services.bootstrap_logging import (
    BootstrapLogger,
    ExtraFieldsFormatter,
    get_bootstrap_logger,
)


class TestBootstrapLogging:
    """Test bootstrap logging functionality."""

    def setup_method(self):
        """Set up test environment before each test."""
        # Store original state
        self.original_configured = BootstrapLogger._configured
        self.original_handlers = logging.getLogger().handlers.copy()

        # Reset logging state
        BootstrapLogger._configured = False

    def teardown_method(self):
        """Clean up test environment after each test."""
        # Restore original state
        BootstrapLogger._configured = self.original_configured

        # Restore original handlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.handlers.extend(self.original_handlers)

    def test_bootstrap_logger_configuration(self):
        """Test that bootstrap logging configures correctly."""
        # Red: Write the test first
        # Arrange
        assert BootstrapLogger._configured is False, "Should start unconfigured"

        # Act
        BootstrapLogger.configure_bootstrap_logging()

        # Assert
        assert BootstrapLogger._configured is True, "Should be configured after call"

        # Verify root logger has handler
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) > 0, "Should have at least one handler"

        # Verify handler is StreamHandler
        has_stream_handler = any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers)
        assert has_stream_handler, "Should have a StreamHandler"

    def test_get_bootstrap_logger(self):
        """Test that get_bootstrap_logger returns working logger."""
        # Red: Write the test first
        # Act
        logger = get_bootstrap_logger(__name__)

        # Assert
        assert logger is not None, "Should return a logger"
        assert isinstance(logger, logging.Logger), "Should be a Logger instance"
        assert logger.name == __name__, "Logger name should match module name"

        # Verify logger can log without errors
        logger.info("Test message")
        logger.error("Test error message")

        # Verify bootstrap is configured
        assert BootstrapLogger._configured is True, "Bootstrap should be configured"

    def test_configure_safe_multiple_calls(self):
        """Test that configure can be called multiple times safely."""
        # Red: Test idempotency
        # Arrange
        root_logger = logging.getLogger()

        # Act - call multiple times
        BootstrapLogger.configure_bootstrap_logging()
        handler_count_after_first = len(root_logger.handlers)

        BootstrapLogger.configure_bootstrap_logging()
        handler_count_after_second = len(root_logger.handlers)

        BootstrapLogger.configure_bootstrap_logging()
        handler_count_after_third = len(root_logger.handlers)

        # Assert - should not add duplicate handlers
        assert handler_count_after_first == handler_count_after_second, "2nd call added one"
        assert handler_count_after_second == handler_count_after_third, "3rd call added one"

    def test_logging_works_before_telemetry_config(self):
        """Test that logging works before telemetry configuration."""
        # Red: Test core bootstrap requirement
        # Act - Get logger without any config
        logger = get_bootstrap_logger("test_module")

        # Assert - Should work without telemetry
        try:
            logger.info("Test message before telemetry")
            logger.warning("Warning before telemetry")
            logger.error("Error before telemetry")
            success = True
        except Exception as e:
            success = False
            pytest.fail(f"Logging should work before telemetry: {e}")

        assert success, "Bootstrap logging should work without telemetry"

    def test_bootstrap_logger_different_levels(self):
        """Test bootstrap logger with different logging levels."""
        # Red: Test logging levels
        # Arrange
        logger = get_bootstrap_logger("test_levels")

        # Act & Assert - Should not raise exceptions
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")

        # All calls should succeed without exceptions
        assert True, "All logging levels should work"

    def test_configuration_circular_dependency_resolved(self):
        """Test that circular dependency between config and logging resolved."""
        # Red: Test the core problem bootstrap solves
        # Arrange - Start with no configuration
        assert BootstrapLogger._configured is False

        # Act - Get logger (should auto-configure)
        logger = get_bootstrap_logger("circular_test")

        # Assert - Logging works WITHOUT config being loaded
        logger.info("Logging works before config loaded")

        # Verify we can log structured data
        logger.info("Structured log entry", extra={"key": "value", "operation": "test"})

        # Bootstrap should be configured
        assert BootstrapLogger._configured is True

        # This proves circular dependency is resolved:
        # - Logging works immediately
        # - No need for config to be loaded first
        # - Can log during config loading process


class TestLogLevelConfiguration:
    """Test LOG_LEVEL environment variable configuration."""

    def setup_method(self):
        """Set up test environment before each test."""
        # Store original state
        self.original_configured = BootstrapLogger._configured
        self.original_handlers = logging.getLogger().handlers.copy()
        self.original_env = os.environ.copy()

        # Reset logging state
        BootstrapLogger._configured = False

    def teardown_method(self):
        """Clean up test environment after each test."""
        # Restore original state
        BootstrapLogger._configured = self.original_configured

        # Restore original handlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.handlers.extend(self.original_handlers)

        # Restore environment
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_log_level_from_env_var_debug(self):
        """Test that LOG_LEVEL=DEBUG sets debug level."""
        # Arrange
        os.environ["LOG_LEVEL"] = "DEBUG"

        # Act
        BootstrapLogger.configure_bootstrap_logging()

        # Assert
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG, "Should set DEBUG level from env var"

    def test_log_level_from_env_var_warning(self):
        """Test that LOG_LEVEL=WARNING sets warning level."""
        # Arrange
        os.environ["LOG_LEVEL"] = "WARNING"

        # Act
        BootstrapLogger.configure_bootstrap_logging()

        # Assert
        root_logger = logging.getLogger()
        assert root_logger.level == logging.WARNING, "Should set WARNING level from env var"

    def test_log_level_from_env_var_error(self):
        """Test that LOG_LEVEL=ERROR sets error level."""
        # Arrange
        os.environ["LOG_LEVEL"] = "ERROR"

        # Act
        BootstrapLogger.configure_bootstrap_logging()

        # Assert
        root_logger = logging.getLogger()
        assert root_logger.level == logging.ERROR, "Should set ERROR level from env var"

    def test_log_level_defaults_to_info(self):
        """Test that LOG_LEVEL defaults to INFO when not set."""
        # Arrange - ensure LOG_LEVEL is not set
        os.environ.pop("LOG_LEVEL", None)

        # Act
        BootstrapLogger.configure_bootstrap_logging()

        # Assert
        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO, "Should default to INFO level"

    def test_log_level_invalid_defaults_to_info(self):
        """Test that invalid LOG_LEVEL defaults to INFO."""
        # Arrange
        os.environ["LOG_LEVEL"] = "INVALID_LEVEL"

        # Act
        BootstrapLogger.configure_bootstrap_logging()

        # Assert
        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO, "Should default to INFO for invalid level"

    def test_log_level_parameter_overrides_env(self):
        """Test that level parameter overrides LOG_LEVEL env var."""
        # Arrange
        os.environ["LOG_LEVEL"] = "ERROR"

        # Act - pass level parameter
        BootstrapLogger.configure_bootstrap_logging(level="DEBUG")

        # Assert
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG, "Parameter should override env var"

    def test_log_level_case_insensitive(self):
        """Test that LOG_LEVEL is case insensitive."""
        # Arrange
        os.environ["LOG_LEVEL"] = "debug"

        # Act
        BootstrapLogger.configure_bootstrap_logging()

        # Assert
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG, "Should handle lowercase level"


class TestExtraFieldsFormatter:
    """Test ExtraFieldsFormatter functionality."""

    def test_formatter_includes_extra_fields(self):
        """Test that extra fields are included in formatted output."""
        # Arrange
        formatter = ExtraFieldsFormatter("%(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.batch_id = "batch-123"
        record.operation = "test_op"

        # Act
        formatted = formatter.format(record)

        # Assert
        assert "Test message" in formatted, "Should include base message"
        assert "batch_id" in formatted, "Should include extra field name"
        assert "batch-123" in formatted, "Should include extra field value"
        assert "operation" in formatted, "Should include operation field"
        assert "test_op" in formatted, "Should include operation value"

    def test_formatter_handles_no_extra_fields(self):
        """Test that formatter works when no extra fields present."""
        # Arrange
        formatter = ExtraFieldsFormatter("%(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Act
        formatted = formatter.format(record)

        # Assert
        assert formatted == "Test message", "Should just return base message"
        assert "|" not in formatted, "Should not have separator when no extra fields"

    def test_formatter_handles_complex_extra_values(self):
        """Test that formatter handles complex extra values like lists and dicts."""
        # Arrange
        formatter = ExtraFieldsFormatter("%(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.messages = [{"id": 1}, {"id": 2}]
        record.metadata = {"key": "value"}

        # Act
        formatted = formatter.format(record)

        # Assert
        assert "Test message" in formatted, "Should include base message"
        assert "messages" in formatted, "Should include messages field"
        assert "metadata" in formatted, "Should include metadata field"

    def test_formatter_excludes_standard_log_record_attrs(self):
        """Test that standard LogRecord attributes are not in extra output."""
        # Arrange
        formatter = ExtraFieldsFormatter("%(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.custom_field = "custom_value"

        # Act
        formatted = formatter.format(record)

        # Assert - should not include standard attrs like name, levelname, etc.
        # But should include custom_field
        assert "custom_field" in formatted, "Should include custom field"
        assert "custom_value" in formatted, "Should include custom value"
        # The standard fields should not appear in the extra JSON part
        parts = formatted.split(" | ")
        if len(parts) > 1:
            extra_json = parts[1]
            assert '"name"' not in extra_json, "Should not include standard 'name' attr"
            assert '"levelname"' not in extra_json, "Should not include standard 'levelname' attr"
