# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from pathlib import Path

import pytest

from agyloop.infrastructure.config import load_config
from agyloop.infrastructure.events import JsonlRunEventSink
from agyloop.infrastructure.state_bus import FileStateBus


def test_load_config_nested_toml_and_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "agyloop.toml").write_text(
        "gateway = 'cli'\n[model]\nlow = 'g-low'\nmedium = 'g-med'\nhigh = 'g-high'\n[run]\nmax_turns = 7\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("AGYLOOP_MAX_TURNS", raising=False)
    cfg = load_config(cwd=tmp_path, home=tmp_path)
    assert cfg.gateway == "cli"
    assert cfg.model_low == "g-low"
    assert cfg.model_high == "g-high"
    assert cfg.max_turns == 7
    assert cfg.resolved_profile().model == "g-low"

    # Coercion from env
    monkeypatch.setenv("AGYLOOP_MAX_TURNS", "11")
    monkeypatch.setenv("AGYLOOP_MAX_DOLLARS", "15.75")
    monkeypatch.setenv("AGYLOOP_AUTO_MODEL", "false")
    monkeypatch.setenv("AGYLOOP_GATEWAY", "cli")
    cfg = load_config(cwd=tmp_path, home=tmp_path)
    assert cfg.max_turns == 11
    assert cfg.max_dollars == 15.75
    assert cfg.auto_model is False
    assert cfg.gateway == "cli"

    # CLI overrides with None values filtered out
    cfg = load_config(
        cwd=tmp_path, home=tmp_path, cli_overrides={"max_turns": 3, "max_dollars": None}
    )
    assert cfg.max_turns == 3


def test_event_sink_redacts_and_binds(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    sink = JsonlRunEventSink(path, run_id="r1", trace_id="t1")
    sink.bind(session_id="s1", attempt=2, phase="RUNNING", trace_id="t2", turn_id="turn_42")
    sink.emit("turn.completed", {"api_key": "secret", "ok": True})

    # Emit without payload
    sink.emit("heartbeat")

    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert "secret" not in lines[0]
    assert "***" in lines[0]
    assert "turn.completed" in lines[0]
    assert "turn_42" in lines[0]
    assert "heartbeat" in lines[1]
    assert "payload" not in lines[1]


def test_state_bus_writes_status_and_bus(tmp_path: Path) -> None:
    bus = FileStateBus(
        status_path=tmp_path / "status.json",
        bus_path=tmp_path / "bus.jsonl",
        run_id="r1",
    )
    bus.publish("status", {"phase": "RUNNING", "access_token": "sekrit-token"})
    status = (tmp_path / "status.json").read_text(encoding="utf-8")
    assert "RUNNING" in status
    assert "sekrit-token" not in status
    assert "***" in status
    assert (tmp_path / "bus.jsonl").read_text(encoding="utf-8").count("\n") == 1

    # Exception during _write_status_atomic cleans up tmp file and reraises
    from unittest.mock import patch

    with (
        patch("os.replace", side_effect=OSError("disk failure")),
        pytest.raises(OSError, match="disk failure"),
    ):
        bus.publish("status", {"phase": "FAILED"})
