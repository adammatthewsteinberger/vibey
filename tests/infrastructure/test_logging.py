# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
import logging
from pathlib import Path

import structlog

from vibey.domain.verbosity import LogPlan
from vibey.infrastructure.logging import (
    NullAppLogger,
    StructlogAppLogger,
    _redact_processor,
    _tagged_json,
    apply_third_party_level,
    configure_logging,
    get_logger,
)


def _reset_logging() -> None:
    root = logging.getLogger()
    root.handlers.clear()
    structlog.reset_defaults()


def test_configure_logging_with_human_console(tmp_path: Path) -> None:
    _reset_logging()
    plan = LogPlan(level="DEBUG", include_third_party=False, include_payloads=False)
    configure_logging(plan, human_console=True)

    root = logging.getLogger()
    assert len(root.handlers) == 2  # human + json


def test_configure_logging_without_human_console(tmp_path: Path) -> None:
    _reset_logging()
    plan = LogPlan(level="INFO", include_third_party=False, include_payloads=False)
    configure_logging(plan, human_console=False)

    root = logging.getLogger()
    assert len(root.handlers) == 1  # json only


def test_configure_logging_with_log_file(tmp_path: Path) -> None:
    _reset_logging()
    log_file = tmp_path / "sub" / "test.log"
    plan = LogPlan(level="INFO", include_third_party=False, include_payloads=False)
    configure_logging(plan, log_file=log_file, human_console=False)

    root = logging.getLogger()
    assert len(root.handlers) == 2  # json + file
    assert log_file.parent.is_dir()
    for h in root.handlers:
        if hasattr(h, "close"):
            h.close()


def test_apply_third_party_level_includes() -> None:
    plan = LogPlan(level="DEBUG", include_third_party=True, include_payloads=False)
    apply_third_party_level(plan)
    assert logging.getLogger("asyncpg").level == logging.DEBUG


def test_apply_third_party_level_excludes() -> None:
    plan = LogPlan(level="DEBUG", include_third_party=False, include_payloads=False)
    apply_third_party_level(plan)
    assert logging.getLogger("asyncpg").level >= logging.WARNING


def test_redact_processor() -> None:
    result = _redact_processor(None, "info", {"event": "test", "key": "value"})
    assert "event" in result


def test_tagged_json() -> None:
    renderer = _tagged_json("test_transport")
    output = renderer(None, "info", {"event": "hello"})
    assert "test_transport" in output
    assert "hello" in output


def test_get_logger() -> None:
    _reset_logging()
    plan = LogPlan(level="INFO", include_third_party=False, include_payloads=False)
    configure_logging(plan, human_console=False)
    logger = get_logger(component="test")
    assert logger is not None


def test_structlog_app_logger_with_bound() -> None:
    _reset_logging()
    plan = LogPlan(level="DEBUG", include_third_party=False, include_payloads=False)
    configure_logging(plan, human_console=False)

    bound = get_logger(component="test")
    logger = StructlogAppLogger(bound=bound)
    logger.debug("d")
    logger.info("i")
    logger.warning("w")
    logger.error("e")

    child = logger.bind(extra="val")
    assert isinstance(child, StructlogAppLogger)


def test_structlog_app_logger_without_bound() -> None:
    _reset_logging()
    plan = LogPlan(level="DEBUG", include_third_party=False, include_payloads=False)
    configure_logging(plan, human_console=False)

    logger = StructlogAppLogger(component="auto")
    logger.info("test")


def test_null_app_logger() -> None:
    logger = NullAppLogger()
    assert logger.bind(x=1) is logger
    logger.debug("d")
    logger.info("i")
    logger.warning("w")
    logger.error("e")
