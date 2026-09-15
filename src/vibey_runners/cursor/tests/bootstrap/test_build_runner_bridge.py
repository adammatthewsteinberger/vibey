# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from cursorloop.bootstrap import BuiltRunner, build_runner
from cursorloop.infrastructure.config import RunnerConfig


def test_build_runner_launches_bridge_when_no_client(tmp_path: Path) -> None:
    config = RunnerConfig(api_key="crsr_test", managed_hooks=False)
    fake_bridge = SimpleNamespace(
        client=object(),
        agent=SimpleNamespace(agent_id="a1", close=lambda: None),
        owns_client=True,
        close=lambda: None,
    )
    with (
        patch("cursorloop.bootstrap.open_live_bridge", return_value=fake_bridge) as open_bridge,
        patch("cursorloop.bootstrap.CursorAgentGateway") as gateway_cls,
        patch("cursorloop.bootstrap.CursorCapacityProbe"),
    ):
        gateway_cls.return_value = SimpleNamespace(
            agent_id=lambda: "a1",
            close=lambda: None,
            send_turn=None,
            set_profile=None,
            set_cwd=None,
            cancel_active_run=None,
        )
        built = build_runner(cwd=tmp_path, config=config)
    assert isinstance(built, BuiltRunner)
    open_bridge.assert_called_once()
    assert built.bridge is fake_bridge
    built.close()


def test_build_runner_uses_scripted_without_bridge(tmp_path: Path, monkeypatch: object) -> None:
    script = tmp_path / "done.json"
    script.write_text(
        json_dumps_done(),
        encoding="utf-8",
    )
    monkeypatch.setenv("CURSORLOOP_ALLOW_TEST_AGENT", "1")  # type: ignore[attr-defined]
    monkeypatch.setenv("CURSORLOOP_TEST_AGENT_SCRIPT", str(script))  # type: ignore[attr-defined]
    config = RunnerConfig(managed_hooks=False)
    with patch("cursorloop.bootstrap.open_live_bridge") as open_bridge:
        built = build_runner(cwd=tmp_path, config=config)
    open_bridge.assert_not_called()
    assert built.bridge is None
    built.close()


def json_dumps_done() -> str:
    return """{
  "probes": [{"signals": {}}],
  "turns": [{
    "signals": {},
    "verdict": {"complete": true, "remaining_work": [], "blocked_on": null, "summary": "done"},
    "output_text": "CURSORLOOP_TASK_FULLY_COMPLETE"
  }]
}
"""


def test_build_runner_forwards_scripted_events_to_sink(tmp_path: Path, monkeypatch: object) -> None:
    """Scripted mode forwards raw_events through on_event callback to event sink."""
    import anyio

    script = tmp_path / "events.json"
    script.write_text(
        json_dumps_with_events(),
        encoding="utf-8",
    )
    monkeypatch.setenv("CURSORLOOP_ALLOW_TEST_AGENT", "1")  # type: ignore[attr-defined]
    monkeypatch.setenv("CURSORLOOP_TEST_AGENT_SCRIPT", str(script))  # type: ignore[attr-defined]
    config = RunnerConfig(managed_hooks=False)
    built = build_runner(cwd=tmp_path, config=config)

    # Actually execute a turn to trigger event emission
    async def send_turn_async() -> None:
        await built.gateway.send_turn("test prompt")

    anyio.run(send_turn_async)

    events_file = built.run_dir.events_path
    assert events_file.exists()
    lines = events_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) > 0
    # Verify events were written with expected structure
    events = [json.loads(line) for line in lines if line.strip()]
    assert len(events) == 4  # 4 raw_events from fixture
    # Check each event has the expected fields
    for event in events:
        assert "ts" in event
        assert "run_id" in event
        assert "event_type" in event
        assert event["event_type"] in ["tool_call", "status", "usage"]
    # Verify specific event payloads were preserved
    tool_events = [e for e in events if e["event_type"] == "tool_call"]
    assert len(tool_events) == 2
    assert tool_events[0]["payload"]["name"] == "Read"
    assert tool_events[0]["payload"]["status"] == "started"
    built.close()


def json_dumps_with_events() -> str:
    return """{
  "probes": [{"signals": {}}],
  "turns": [{
    "signals": {},
    "verdict": {"complete": true, "remaining_work": [], "blocked_on": null, "summary": "done"},
    "output_text": "CURSORLOOP_TASK_FULLY_COMPLETE",
    "raw_events": [
      {"type": "tool_call", "name": "Read", "call_id": "call_1", "status": "started"},
      {"type": "tool_call", "name": "Read", "call_id": "call_1", "status": "completed"},
      {"type": "status", "status": "thinking", "message": "Processing"},
      {"type": "usage", "total_tokens": 100}
    ]
  }]
}
"""
