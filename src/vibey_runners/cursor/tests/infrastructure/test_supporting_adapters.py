# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Smoke coverage for Task 15 adapters beyond the four plan-snippet suites."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path

import anyio
import pytest

from cursorloop.domain.control import (
    Prompt,
    SavePoint,
    SetCwd,
    SetEffort,
    SetModel,
    Snapshot,
    Stop,
    WindDown,
)
from cursorloop.domain.handoff_marker import HandoffMarker
from cursorloop.infrastructure.audit import JsonlAuditLog
from cursorloop.infrastructure.clock import AnyioSleeper, SystemClock
from cursorloop.infrastructure.config import load_config
from cursorloop.infrastructure.control import FileRunControl
from cursorloop.infrastructure.events import JsonlRunEventSink
from cursorloop.infrastructure.logging import (
    NullAppLogger,
    StructlogAppLogger,
    configure_logging,
)
from cursorloop.infrastructure.notify import StderrNotifier
from cursorloop.infrastructure.progress import ConsoleProgressReporter
from cursorloop.infrastructure.redact import redact
from cursorloop.infrastructure.rundir import (
    RunDirectory,
    list_run_directories,
    resolve_run_directory,
    runs_root_for,
)
from cursorloop.infrastructure.state_bus import FileStateBus


def test_redact_walks_nested_containers() -> None:
    assert redact({"nested": [{"api_key": "x"}, ("ok",)]}) == {
        "nested": [{"api_key": "***"}, ("ok",)]
    }
    assert redact(42) == 42


def test_config_reads_toml_and_optional_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    cfg = tmp_path / "cursorloop.toml"
    cfg.write_text(
        '[cursorloop]\nlog_level = "DEBUG"\nbilling_lexicon = ["a", "b"]\nmanaged_hooks = false\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("CURSORLOOP_LOG_FILE", str(tmp_path / "run.log"))
    monkeypatch.setenv("CURSORLOOP_MODEL", "composer-2.5")
    monkeypatch.setenv("CURSORLOOP_MAX_TURNS", "9")
    monkeypatch.setenv("CURSORLOOP_MAX_DOLLARS", "1.5")
    monkeypatch.setenv("CURSORLOOP_RATE_LIMIT_LEXICON", "slow,busy")
    monkeypatch.setenv("CURSORLOOP_MANAGED_HOOKS", "off")
    loaded = load_config(config_file=cfg)
    assert loaded.log_level == "DEBUG"
    assert loaded.billing_terms == ("a", "b")
    assert loaded.managed_hooks is False
    assert loaded.model == "composer-2.5"
    assert loaded.max_turns == 9
    assert loaded.max_dollars == 1.5
    assert loaded.rate_limit_terms == ("slow", "busy")
    assert loaded.log_file == str(tmp_path / "run.log")


def test_audit_log_appends_redacted_jsonl(tmp_path: Path) -> None:
    path = tmp_path / "audit.jsonl"
    log = JsonlAuditLog(path, run_id="r1")
    log.bind(agent_id="a1")
    log.record("turn", {"api_key": "crsr_abcdefghijklmnopqrstuvwxyz012345", "ok": 1})
    line = json.loads(path.read_text(encoding="utf-8").strip())
    assert line["event_type"] == "turn"
    assert line["run_id"] == "r1"
    assert line["agent_id"] == "a1"
    assert line["api_key"] == "***"
    assert "crsr_" not in path.read_text(encoding="utf-8")


def test_clock_and_sleeper_real_time() -> None:
    clock = SystemClock()
    now = clock.now()
    assert now.tzinfo is not None

    async def _run() -> None:
        sleeper = AnyioSleeper(clock)
        await sleeper.sleep_until(clock.now() - timedelta(seconds=1))
        await sleeper.sleep_until(clock.now() + timedelta(milliseconds=5))

    anyio.run(_run)


def test_notify_and_progress(capsys: pytest.CaptureFixture[str]) -> None:
    StderrNotifier().notify("credits depleted")
    err = capsys.readouterr().err
    assert "credits depleted" in err
    ConsoleProgressReporter().turn_sent(attempt=2)
    ConsoleProgressReporter().waiting(reason="window", until=datetime.now(UTC))
    ConsoleProgressReporter().finished(success=True, reason="done")
    out = capsys.readouterr().out
    assert "attempt 2" in out
    assert "Done" in out


def test_events_and_state_bus(tmp_path: Path) -> None:
    events = JsonlRunEventSink(tmp_path / "events.jsonl", run_id="r1")
    events.bind(agent_id="a1", attempt=3, phase="RUNNING", turn_id="t1", trace_id="tr")
    events.emit("tick", {"api_key": "secret"})
    row = json.loads((tmp_path / "events.jsonl").read_text(encoding="utf-8").strip())
    assert row["agent_id"] == "a1"
    assert row["payload"]["api_key"] == "***"

    bus = FileStateBus(
        status_path=tmp_path / "status.json",
        bus_path=tmp_path / "bus.jsonl",
        run_id="r1",
    )
    bus.publish("phase", {"phase": "WAITING", "password": "x"})
    status = json.loads((tmp_path / "status.json").read_text(encoding="utf-8"))
    assert status["phase"] == "WAITING"
    assert status["password"] == "***"
    assert (tmp_path / "bus.jsonl").read_text(encoding="utf-8").strip()


def test_rundir_create_list_resolve(tmp_path: Path) -> None:
    cwd = tmp_path / "ws"
    cwd.mkdir()
    plan = cwd / "plan.md"
    plan.write_text("- [ ] x\n", encoding="utf-8")
    root = runs_root_for(cwd)
    first = RunDirectory.create(root, cwd=cwd, plan_path=plan)
    first.update_meta(status="finished", agent_id="agent-1", phase="DONE")
    first.write_stop_summary("# stopped\n")
    assert first.resources_root.is_dir()
    assert first.snapshots_root.is_dir()
    second = RunDirectory.create(root, cwd=cwd)
    listed = list_run_directories(cwd)
    assert {d.root for d in listed} == {first.root, second.root}
    assert resolve_run_directory(cwd, first.root.name).read_meta().status == "finished"
    active = resolve_run_directory(cwd)
    assert active.root == second.root
    with pytest.raises(FileNotFoundError):
        resolve_run_directory(tmp_path / "empty")


def test_rundir_write_handoff_marker_atomic(tmp_path: Path) -> None:
    """write_handoff_marker uses tmp + replace for crash safety."""
    cwd = tmp_path / "ws"
    cwd.mkdir()
    root = runs_root_for(cwd)
    run_dir = RunDirectory.create(root, cwd=cwd)
    marker = HandoffMarker(
        run_id="test-run",
        reason="low headroom",
        produced_at=datetime.now(UTC),
        headroom=0.15,
        headroom_source="budget.turns",
        turns_spent=5,
        dollars_spent=1.23,
    )
    result_path = run_dir.write_handoff_marker(marker)
    assert result_path == run_dir.handoff_marker_path
    assert run_dir.handoff_marker_path.is_file()
    written = run_dir.handoff_marker_path.read_text(encoding="utf-8")
    assert "test-run" in written
    assert "low headroom" in written
    # tmp file should not exist after successful write
    assert not run_dir.handoff_marker_path.with_suffix(".json.tmp").exists()


def test_control_enqueue_poll_and_stop_outranks(tmp_path: Path) -> None:
    control = FileRunControl(tmp_path / "inbox")
    control.enqueue(Prompt(text="go"))
    control.enqueue(SetModel(model="composer-2.5"))
    control.enqueue(SetEffort(effort="high"))
    control.enqueue(SetCwd(path="/tmp"))
    control.enqueue(Snapshot())
    control.enqueue(SavePoint())
    control.enqueue(WindDown(reason="low headroom"))
    control.enqueue(Stop())
    polled = control.poll()
    assert isinstance(polled[0], Stop)
    assert isinstance(polled[1], Prompt)
    assert {type(c) for c in polled} == {
        Stop,
        Prompt,
        SetModel,
        SetEffort,
        SetCwd,
        Snapshot,
        SavePoint,
        WindDown,
    }
    assert control.poll() == []
    bad = tmp_path / "inbox" / "1-bad.cmd.json"
    bad.write_text("{not-json", encoding="utf-8")
    assert control.poll() == []
    assert bad.is_file()


def test_control_wind_down_round_trip(tmp_path: Path) -> None:
    control = FileRunControl(tmp_path / "inbox")
    control.enqueue(WindDown(reason="test reason"))
    polled = control.poll()
    assert len(polled) == 1
    assert isinstance(polled[0], WindDown)
    assert polled[0].reason == "test reason"


def test_logging_configure_and_loggers(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    log_file = tmp_path / "app.log"
    configure_logging(log_file=log_file, level="INFO", human_console=True)
    logger = StructlogAppLogger(run_id="r1", agent_id="a1")
    child = logger.bind(phase="RUNNING", event_type="turn")
    child.info("hello", api_key="crsr_abcdefghijklmnopqrstuvwxyz012345")
    child.debug("ignored-at-info")
    child.warning("warn")
    child.error("err")
    assert log_file.is_file()
    body = log_file.read_text(encoding="utf-8")
    assert "crsr_" not in body
    null = NullAppLogger()
    null.bind(x=1).info("noop")
    configure_logging(log_file=None, level="DEBUG", human_console=False)
    logging.getLogger().handlers.clear()
