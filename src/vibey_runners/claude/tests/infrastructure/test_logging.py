# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for infrastructure/logging.py — loggers, configure_logging, and adapters."""

from __future__ import annotations

import logging
from pathlib import Path

from claudeloop.domain.verbosity import LogPlan
from claudeloop.infrastructure.logging import (
    NullAppLogger,
    StructlogAppLogger,
    apply_third_party_level,
    configure_logging,
    get_logger,
)


class TestConfigureLogging:
    def test_no_file_handler(self, tmp_path: Path) -> None:
        try:
            configure_logging(log_file=None, level="INFO")
            root = logging.getLogger()
            assert len(root.handlers) >= 1
        finally:
            logging.getLogger().handlers.clear()

    def test_with_file_handler(self, tmp_path: Path) -> None:
        log_file = tmp_path / "test.jsonl"
        try:
            configure_logging(log_file=log_file, level="DEBUG")
            root = logging.getLogger()
            file_handlers = [h for h in root.handlers if isinstance(h, logging.FileHandler)]
            assert len(file_handlers) == 1
        finally:
            logging.getLogger().handlers.clear()

    def test_file_creates_parent_dirs(self, tmp_path: Path) -> None:
        log_file = tmp_path / "deep" / "nested" / "test.jsonl"
        try:
            configure_logging(log_file=log_file, level="INFO")
            assert log_file.parent.is_dir()
        finally:
            logging.getLogger().handlers.clear()

    def test_no_human_console(self, tmp_path: Path) -> None:
        try:
            configure_logging(log_file=None, level="INFO", human_console=False)
            root = logging.getLogger()
            assert len(root.handlers) >= 1
        finally:
            logging.getLogger().handlers.clear()


class TestGetLogger:
    def test_returns_bound_logger(self) -> None:
        logger = get_logger(component="test")
        assert logger is not None


class TestStructlogAppLogger:
    def test_all_levels(self) -> None:
        try:
            configure_logging(log_file=None, level="DEBUG")
            adapter = StructlogAppLogger(component="test")
            adapter.debug("d")
            adapter.info("i")
            adapter.warning("w")
            adapter.error("e")
        finally:
            logging.getLogger().handlers.clear()

    def test_bind_returns_new_logger(self) -> None:
        try:
            configure_logging(log_file=None, level="DEBUG")
            adapter = StructlogAppLogger(component="test")
            bound = adapter.bind(request_id="123")
            assert isinstance(bound, StructlogAppLogger)
            assert bound is not adapter
        finally:
            logging.getLogger().handlers.clear()


class TestNullAppLogger:
    def test_all_levels_are_noop(self) -> None:
        logger = NullAppLogger()
        logger.debug("d")
        logger.info("i")
        logger.warning("w")
        logger.error("e")

    def test_bind_returns_same_type(self) -> None:
        logger = NullAppLogger()
        bound = logger.bind(key="val")
        assert isinstance(bound, NullAppLogger)


class TestApplyThirdPartyLevel:
    def test_third_party_stays_quiet_by_default(self) -> None:
        plan = LogPlan(level="DEBUG", include_third_party=False, include_payloads=False)
        apply_third_party_level(plan)
        for name in ("anthropic", "httpx", "httpcore"):
            assert logging.getLogger(name).level >= logging.WARNING

    def test_third_party_widened(self) -> None:
        plan = LogPlan(level="DEBUG", include_third_party=True, include_payloads=False)
        apply_third_party_level(plan)
        for name in ("anthropic", "httpx", "httpcore"):
            assert logging.getLogger(name).level == logging.DEBUG
