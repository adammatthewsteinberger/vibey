# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Unit tests for the test-only JSON-scripted agent and env gate."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from claudeloop.infrastructure.agent.scripted import (
    ALLOW_TEST_AGENT_ENV,
    TEST_AGENT_SCRIPT_ENV,
    load_agent_script,
    resolve_test_agent_from_env,
)


@pytest.mark.asyncio
async def test_load_and_replay_script(tmp_path: Path) -> None:
    script_path = tmp_path / "script.json"
    script_path.write_text(
        json.dumps(
            {
                "probes": [{"signals": {}}],
                "turns": [
                    {
                        "signals": {},
                        "verdict": {"complete": True, "summary": "done"},
                        "session_id": "s1",
                        "raw_events": [{"api_key": "sk-ant-abcdefghijklmnopqrstuvwxyz"}],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    script = load_agent_script(script_path)
    assert len(script.turns) == 1
    assert script.turns[0].verdict is not None
    assert script.turns[0].verdict.complete is True

    events: list[dict[str, object]] = []
    os.environ[ALLOW_TEST_AGENT_ENV] = "1"
    os.environ[TEST_AGENT_SCRIPT_ENV] = str(script_path)
    try:
        resolved = resolve_test_agent_from_env(on_event=events.append)
        assert resolved is not None
        gateway, probe = resolved
        await probe.probe()
        outcome = await gateway.send_turn("go")
        assert outcome.session_id == "s1"
        assert outcome.verdict is not None and outcome.verdict.complete
        assert events and events[0]["api_key"] == "sk-ant-abcdefghijklmnopqrstuvwxyz"
        await gateway.close()
        assert gateway.closed is True
    finally:
        os.environ.pop(ALLOW_TEST_AGENT_ENV, None)
        os.environ.pop(TEST_AGENT_SCRIPT_ENV, None)


def test_script_without_allow_flag_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    script_path = tmp_path / "script.json"
    script_path.write_text(
        json.dumps({"probes": [{}], "turns": [{"verdict": {"complete": True}}]}),
        encoding="utf-8",
    )
    monkeypatch.delenv(ALLOW_TEST_AGENT_ENV, raising=False)
    monkeypatch.setenv(TEST_AGENT_SCRIPT_ENV, str(script_path))
    with pytest.raises(RuntimeError, match="ALLOW_TEST_AGENT"):
        resolve_test_agent_from_env()


def test_no_script_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(TEST_AGENT_SCRIPT_ENV, raising=False)
    monkeypatch.setenv(ALLOW_TEST_AGENT_ENV, "1")
    assert resolve_test_agent_from_env() is None


def test_window_exhausted_parses_resets_at(tmp_path: Path) -> None:
    script_path = tmp_path / "wait.json"
    script_path.write_text(
        json.dumps(
            {
                "probes": [{}],
                "turns": [
                    {
                        "signals": {
                            "rate_limit_status": "rejected",
                            "rate_limit_type": "five_hour",
                            "resets_at": "2099-01-01T00:00:00+00:00",
                        },
                        "verdict": {"complete": False, "remaining_work": ["x"]},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    script = load_agent_script(script_path)
    assert script.turns[0].signals.resets_at is not None
    assert script.turns[0].signals.resets_at.year == 2099
