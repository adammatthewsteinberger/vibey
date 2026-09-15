# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for agyloop.infrastructure.logging."""

from __future__ import annotations

from pathlib import Path

from agyloop.domain.verbosity import LogPlan
from agyloop.infrastructure.logging import (
    StructlogAppLogger,
    _redact_processor,
    apply_third_party_level,
    configure_logging,
)


def test_redact_processor_fallback() -> None:
    from unittest.mock import patch

    assert _redact_processor(None, "info", {"key": "val"}) == {"key": "val"}
    with patch("agyloop.infrastructure.logging.redact", return_value="not a dict"):
        assert _redact_processor(None, "info", {"key": "val"}) == {"key": "val"}


def test_configure_logging_human_and_json_file(tmp_path: Path) -> None:
    log_file = tmp_path / "run.log"
    # 1. Human console + log file
    configure_logging(log_file=log_file, level="DEBUG", human_console=True)
    logger = StructlogAppLogger()
    logger.debug("test_debug_event", foo="bar")
    logger.info("test_info_event", secret_key="123")
    logger.warning("test_warn_event")
    logger.error("test_error_event")
    assert log_file.is_file()
    content = log_file.read_text(encoding="utf-8")
    assert "test_info_event" in content

    # 2. JSON console without log file
    configure_logging(log_file=None, level="INFO", human_console=False)
    bound = logger.bind(run_id="r1")
    bound.info("bound_event")


def test_apply_third_party_level() -> None:
    # 1. Standard log plan (raises floor to WARNING)
    plan1 = LogPlan(level="DEBUG", include_third_party=False, include_payloads=False)
    apply_third_party_level(plan1)

    # 2. Widened net log plan (includes third party at DEBUG)
    plan2 = LogPlan(level="DEBUG", include_third_party=True, include_payloads=False)
    apply_third_party_level(plan2)
