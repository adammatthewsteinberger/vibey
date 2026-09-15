"""Tests for ``vibey_bootstrap.logging.config`` and ``.noise``."""

from __future__ import annotations

import logging
import os

import pytest

from vibey_bootstrap.logging.config import (
    configure_logging,
    debug_logging_enabled,
    effective_log_level,
    env_flag,
)
from vibey_bootstrap.logging.noise import (
    _DEFAULT_NOISY_LOGGERS,
    register_noisy_logger,
    silence_noisy_loggers,
)


@pytest.fixture(autouse=True)
def _clean_env() -> None:
    for k in ("LOG_LEVEL", "DEBUG_LOGGING_ENABLED"):
        os.environ.pop(k, None)


class TestEnvFlag:
    @pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "On"])
    def test_truthy(self, value: str) -> None:
        os.environ["FOO_FLAG"] = value
        try:
            assert env_flag("FOO_FLAG") is True
        finally:
            os.environ.pop("FOO_FLAG", None)

    @pytest.mark.parametrize("value", ["0", "false", "no", "off", ""])
    def test_falsy(self, value: str) -> None:
        os.environ["FOO_FLAG"] = value
        try:
            assert env_flag("FOO_FLAG") is False
        finally:
            os.environ.pop("FOO_FLAG", None)

    def test_default(self) -> None:
        os.environ.pop("FOO_FLAG", None)
        assert env_flag("FOO_FLAG", default=True) is True


class TestEffectiveLogLevel:
    def test_default_info(self) -> None:
        assert effective_log_level() == logging.INFO

    def test_warning(self) -> None:
        os.environ["LOG_LEVEL"] = "WARNING"
        assert effective_log_level() == logging.WARNING

    def test_debug_clamped_without_gate(self) -> None:
        os.environ["LOG_LEVEL"] = "DEBUG"
        assert effective_log_level() == logging.INFO

    def test_debug_honored_with_gate(self) -> None:
        os.environ["LOG_LEVEL"] = "DEBUG"
        os.environ["DEBUG_LOGGING_ENABLED"] = "true"
        assert effective_log_level() == logging.DEBUG

    def test_invalid_level_falls_back(self) -> None:
        os.environ["LOG_LEVEL"] = "ZIGZAG"
        assert effective_log_level() == logging.INFO


class TestDebugLoggingEnabled:
    def test_default(self) -> None:
        assert debug_logging_enabled() is False


def test_configure_logging_idempotent() -> None:
    configure_logging()
    root = logging.getLogger()
    handlers_first = len(root.handlers)
    configure_logging()
    handlers_second = len(root.handlers)
    assert handlers_first == handlers_second


def test_silence_noisy_clamps_level() -> None:
    register_noisy_logger("test.noisy.example")
    silence_noisy_loggers(level=logging.WARNING)
    assert logging.getLogger("test.noisy.example").level == logging.WARNING
    assert "test.noisy.example" in _DEFAULT_NOISY_LOGGERS
