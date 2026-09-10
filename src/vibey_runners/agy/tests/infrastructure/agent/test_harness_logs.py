# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for agyloop.infrastructure.agent.harness_logs."""

from __future__ import annotations

import logging

import pytest

from agyloop.domain.errors import AgentConfigError
from agyloop.infrastructure.agent.harness_logs import (
    capture_harness_logs,
    raise_if_empty_withdrawn,
)


def test_capture_harness_logs_and_raise_if_empty_withdrawn() -> None:
    # 1. capture_harness_logs captures log records
    with capture_harness_logs() as logs:
        logging.getLogger("google.antigravity").error("test harness error log")
        logging.getLogger("google.antigravity").debug("debug record ignored")
    assert any("test harness error log" in line for line in logs)

    # 2. Non-empty output text is ignored
    raise_if_empty_withdrawn(
        output_text="some model text",
        logs=["404 NOT_FOUND models/gemini-2.5-flash-lite is no longer available"],
    )

    # 3. Empty output text without withdrawn model logs returns cleanly
    raise_if_empty_withdrawn(output_text="", logs=["just normal logs without error"])

    # 4. Empty output text WITH withdrawn model logs raises AgentConfigError
    with pytest.raises(AgentConfigError, match="withdrawn model"):
        raise_if_empty_withdrawn(
            output_text="",
            logs=["404 NOT_FOUND models/gemini-2.5-flash-lite is no longer available to new users"],
        )
