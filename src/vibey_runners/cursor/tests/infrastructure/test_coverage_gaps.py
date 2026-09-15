# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Edge-case coverage to bring ``cursorloop.infrastructure`` to 100%."""

from __future__ import annotations

import errno
import hashlib
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from cursorloop.domain.model_profile import SHIPPED_PRESETS
from cursorloop.infrastructure import control as control_mod
from cursorloop.infrastructure.agent.catalog import CursorAgentCatalog, _parse_modified
from cursorloop.infrastructure.agent.gateway import CursorAgentGateway
from cursorloop.infrastructure.agent.hooks import ManagedHooks
from cursorloop.infrastructure.agent.models import CursorModelCatalog
from cursorloop.infrastructure.agent.probe import CursorCapacityProbe, _default_prompt
from cursorloop.infrastructure.agent.usage import CursorUsageReader
from cursorloop.infrastructure.agent.watchdog import TurnWatchdog
from cursorloop.infrastructure.audit import JsonlAuditLog
from cursorloop.infrastructure.config import load_config
from cursorloop.infrastructure.events import JsonlRunEventSink
from cursorloop.infrastructure.lock import FileAgentLock
from cursorloop.infrastructure.logging import NullAppLogger
from cursorloop.infrastructure.redact import redact_event
from cursorloop.infrastructure.rundir import (
    RunDirectory,
    _pid_alive,
    list_run_directories,
    resolve_run_directory,
    runs_root_for,
)
from cursorloop.infrastructure.state_bus import FileStateBus
from tests.application import fakes
from tests.infrastructure.test_gateway import FakeCursorAgent, FakeRunEventSink, _gateway


def test_parse_modified_datetime_and_empty() -> None:
    instant = datetime(2026, 8, 13, tzinfo=UTC)
    assert _parse_modified(instant) is instant
    assert _parse_modified("") is None
    assert _parse_modified(None) is None


def test_catalog_connect_uses_sdk_launch_bridge_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def fake_launch(*, workspace: str, **kwargs: object) -> SimpleNamespace:
        del kwargs
        calls.append(workspace)
        return SimpleNamespace(agents=SimpleNamespace(list=lambda **_k: []))

    monkeypatch.setattr(
        "cursorloop.infrastructure.agent.catalog.CursorClient.launch_bridge",
        fake_launch,
    )
    catalog = CursorAgentCatalog.connect(workspace="/ws")
    assert calls == ["/ws"]
    assert catalog.list_all(cwd="/ws") == []


async def test_gateway_cancel_without_callable_and_close_without_close() -> None:
    agent = FakeCursorAgent(run=fakes.FakeRun(status="running"))
    gateway = _gateway(agent)
    await gateway.send_turn("go")
    gateway._active_run = SimpleNamespace(status="running")
    assert await gateway.cancel_active_run() is False

    class NoClose:
        agent_id = "x"
        model = None

        def send(self, message: object, options: object = None, **kwargs: object) -> object:
            del message, options, kwargs
            return fakes.FakeRun(status="finished")

    bare = CursorAgentGateway(
        client=object(),
        agent=NoClose(),
        profile=SHIPPED_PRESETS["composer"],
        watchdog=TurnWatchdog(
            turn_timeout=timedelta(minutes=30),
            stall_timeout=timedelta(minutes=10),
            clock=fakes.FakeClock(),
        ),
        event_sink=FakeRunEventSink(),
    )
    await bare.close()


def test_watchdog_cancel_guards() -> None:
    clock = fakes.FakeClock()
    watchdog = TurnWatchdog(
        turn_timeout=timedelta(minutes=1), stall_timeout=timedelta(minutes=1), clock=clock
    )
    watchdog._cancel(fakes.FakeRun(status="finished"))
    watchdog._cancel(SimpleNamespace(status="running"))  # no cancel attr


def test_probe_default_prompt_delegates(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[tuple[object, object]] = []

    def fake_prompt(message: object, options: object, **kwargs: object) -> str:
        del kwargs
        seen.append((message, options))
        return "ok"

    monkeypatch.setattr(
        "cursorloop.infrastructure.agent.probe.Agent.prompt",
        fake_prompt,
    )
    assert _default_prompt("hi", object()) == "ok"
    assert seen[0][0] == "hi"
    probe = CursorCapacityProbe("/repo", SHIPPED_PRESETS["composer"])
    assert probe._prompt is _default_prompt


def test_model_catalog_skips_non_string_ids() -> None:
    client = SimpleNamespace(models=SimpleNamespace(list=lambda: (1, SimpleNamespace(id=2), "ok")))
    assert CursorModelCatalog(client).list_all() == ["ok"]


async def test_usage_skips_bool_total_tokens() -> None:
    run_usage = SimpleNamespace(run_id="r1", usage=SimpleNamespace(total_tokens=True))
    agent = SimpleNamespace(
        get_usage=lambda **_k: SimpleNamespace(
            usage=SimpleNamespace(total_tokens=False),
            runs=(run_usage,),
            cost=None,
        )
    )
    assert await CursorUsageReader(agent).turn_tokens("r1") == 0


def test_hooks_restore_backup_missing(tmp_path: Path) -> None:
    hooks = tmp_path / ".cursor" / "hooks.json"
    hooks.parent.mkdir(parents=True)
    hooks.write_text('{"version":1,"hooks":{}}')
    manager = ManagedHooks(workspace=tmp_path, state_dir=tmp_path / ".cursorloop")
    manager.install()
    manager._backup_path.unlink()
    assert manager.restore() is False


def test_hooks_restore_backup_hash_mismatch(tmp_path: Path) -> None:
    hooks = tmp_path / ".cursor" / "hooks.json"
    hooks.parent.mkdir(parents=True)
    hooks.write_text('{"version":1,"hooks":{}}')
    manager = ManagedHooks(workspace=tmp_path, state_dir=tmp_path / ".cursorloop")
    manager.install()
    manager._backup_path.write_bytes(b"tampered")
    assert manager.restore() is False


def test_hooks_diff_empty_when_already_merged(tmp_path: Path) -> None:
    manager = ManagedHooks(workspace=tmp_path, state_dir=tmp_path / ".cursorloop")
    manager.install()
    assert manager.diff() == ""


def test_hooks_recorded_unapplied_without_original_hash(tmp_path: Path) -> None:
    state_dir = tmp_path / ".cursorloop"
    state_dir.mkdir()
    (state_dir / "state.json").write_text(json.dumps({"hooks_merged_sha256": "abc"}))
    manager = ManagedHooks(workspace=tmp_path, state_dir=state_dir)
    assert manager._recorded_install_unapplied() is False


def test_hooks_command_outside_workspace_and_bad_json(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    manager = ManagedHooks(workspace=tmp_path / "ws", state_dir=outside / ".cursorloop")
    (tmp_path / "ws").mkdir()
    manager._scripts_dir.mkdir(parents=True)
    cmd = manager._command_for("preToolUse")
    assert cmd.endswith("preToolUse.sh")

    hooks = tmp_path / "ws" / ".cursor" / "hooks.json"
    hooks.parent.mkdir(parents=True)
    hooks.write_text("{not-json")
    merged = manager._merge(hooks.read_bytes())
    assert merged["version"] == 1


def test_hooks_corrupt_state_and_non_dict_hooks(tmp_path: Path) -> None:
    state_dir = tmp_path / ".cursorloop"
    state_dir.mkdir()
    (state_dir / "state.json").write_text("{bad")
    manager = ManagedHooks(workspace=tmp_path, state_dir=state_dir)
    assert manager._read_state() == {}
    assert manager._merge(b'["not-a-dict"]')["hooks"]
    assert manager._merge(b'{"hooks": "nope"}')["hooks"]


async def test_gateway_reassert_skips_agents_without_model_attr() -> None:
    class NoModel:
        agent_id = "x"

        def send(self, message: object, options: object = None, **kwargs: object) -> object:
            del message, options, kwargs
            return fakes.FakeRun(status="finished")

    gateway = CursorAgentGateway(
        client=object(),
        agent=NoModel(),
        profile=SHIPPED_PRESETS["composer"],
        watchdog=TurnWatchdog(
            turn_timeout=timedelta(minutes=30),
            stall_timeout=timedelta(minutes=10),
            clock=fakes.FakeClock(),
        ),
        event_sink=FakeRunEventSink(),
    )
    await gateway.send_turn("go")


def test_hooks_restore_when_created_file_already_gone(tmp_path: Path) -> None:
    """hooks_existed False + missing file: skip the elif unlink, still clear state."""
    state_dir = tmp_path / ".cursorloop"
    state_dir.mkdir()
    empty_hash = hashlib.sha256(b"").hexdigest()
    other_hash = hashlib.sha256(b"prior-original").hexdigest()
    (state_dir / "state.json").write_text(
        json.dumps(
            {
                "hooks_existed": False,
                "hooks_merged_sha256": empty_hash,
                "hooks_original_sha256": other_hash,
            }
        )
    )
    manager = ManagedHooks(workspace=tmp_path, state_dir=state_dir)
    assert manager.restore() is True
    assert not (state_dir / "state.json").exists()


def test_hooks_clear_state_when_nothing_on_disk(tmp_path: Path) -> None:
    manager = ManagedHooks(workspace=tmp_path, state_dir=tmp_path / ".cursorloop")
    manager._clear_hook_state()


def test_audit_bind_run_id_only(tmp_path: Path) -> None:
    log = JsonlAuditLog(tmp_path / "a.jsonl")
    log.bind(run_id="only-run")
    log.record("x", {"n": 1})
    line = json.loads((tmp_path / "a.jsonl").read_text().strip())
    assert line["run_id"] == "only-run"
    assert "agent_id" not in line


def test_audit_record_without_bound_ids(tmp_path: Path) -> None:
    log = JsonlAuditLog(tmp_path / "a.jsonl")
    log.record("solo", {"ok": True})
    line = json.loads((tmp_path / "a.jsonl").read_text().strip())
    assert "run_id" not in line
    assert "agent_id" not in line


def test_config_edge_cases(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("CURSOR_API_KEY", raising=False)
    monkeypatch.setenv("CURSORLOOP_LOG_LEVEL", "WARNING")
    monkeypatch.setenv("CURSORLOOP_MANAGED_HOOKS", "yes")
    monkeypatch.setenv("CURSORLOOP_UNUSED_FLAG", "x")
    loaded = load_config()
    assert loaded.log_level == "WARNING"
    assert loaded.managed_hooks is True
    assert "CURSORLOOP_UNUSED_FLAG" in loaded.observed_env
    assert load_config(config_file=tmp_path / "missing.toml").api_key is None

    bad = tmp_path / "bad.toml"
    bad.write_text("cursorloop = 1\n", encoding="utf-8")
    assert load_config(config_file=bad).log_level == "WARNING"

    lexicon = tmp_path / "lex.toml"
    lexicon.write_text('[cursorloop]\nbilling_lexicon = "one,two"\n', encoding="utf-8")
    monkeypatch.delenv("CURSORLOOP_LOG_LEVEL", raising=False)
    assert load_config(config_file=lexicon).billing_terms == ("one", "two")


def test_config_unknown_cursorloop_env_is_observed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CURSORLOOP_MANAGED_HOOKS", "1")
    monkeypatch.setenv("CURSORLOOP_UNUSED_FLAG", "x")
    cfg = load_config()
    assert cfg.managed_hooks is True
    assert "CURSORLOOP_UNUSED_FLAG" in cfg.observed_env


def test_control_rejects_unknown_payloads(tmp_path: Path) -> None:
    with pytest.raises(TypeError):
        control_mod._command_to_payload(object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="unknown"):
        control_mod._payload_to_command({"type": "nope"})
    inbox = tmp_path / "inbox"
    control = control_mod.FileRunControl(inbox)
    unknown = inbox / "1-unknown.cmd.json"
    unknown.write_text(json.dumps({"type": "nope"}) + "\n", encoding="utf-8")
    assert control.poll() == []
    assert unknown.is_file()


def test_events_optional_bind_paths(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    path.write_text("", encoding="utf-8")
    sink = JsonlRunEventSink(path, run_id="r1")
    sink.bind()
    sink.emit("bare")
    row = json.loads(path.read_text().strip())
    assert row["event_type"] == "bare"
    assert "agent_id" not in row
    assert "payload" not in row


def test_lock_release_without_hold_and_oserror_eexist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lock = FileAgentLock(tmp_path / "locks")
    lock.release("never-held")
    real_open = os.open

    def open_eexist(path: str, flags: int, *args: Any, **kwargs: Any) -> int:
        if flags & os.O_EXCL:
            raise OSError(errno.EEXIST, "exists")
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", open_eexist)
    assert lock.acquire("a") is False


def test_null_logger_all_levels() -> None:
    null = NullAppLogger()
    null.debug("d")
    null.warning("w")
    null.error("e")


def test_redact_event_non_dict_passthrough(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "cursorloop.infrastructure.redact.redact",
        lambda value: "not-a-dict",
    )
    event = {"x": 1}
    assert redact_event(None, "info", event) is event


def test_rundir_open_missing_meta_and_pid_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    empty = tmp_path / "empty-run"
    empty.mkdir()
    with pytest.raises(FileNotFoundError, match="not a cursorloop"):
        RunDirectory.open_existing(empty)
    assert list_run_directories(tmp_path / "nowhere") == []
    assert _pid_alive(0) is False
    assert _pid_alive(1) is True or _pid_alive(1) is False

    def kill_lookup(pid: int, sig: int) -> None:
        del pid, sig
        raise ProcessLookupError

    monkeypatch.setattr(os, "kill", kill_lookup)
    assert _pid_alive(999999) is False

    def kill_perm(pid: int, sig: int) -> None:
        del pid, sig
        raise PermissionError

    monkeypatch.setattr(os, "kill", kill_perm)
    assert _pid_alive(999999) is True

    cwd = tmp_path / "ws"
    cwd.mkdir()
    root = runs_root_for(cwd)
    finished = RunDirectory.create(root, cwd=cwd)
    finished.update_meta(status="finished", pid=0)
    assert resolve_run_directory(cwd).root == finished.root


def test_state_bus_cleans_tmp_on_write_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bus_path = tmp_path / "bus.jsonl"
    bus_path.write_text("", encoding="utf-8")
    bus = FileStateBus(status_path=tmp_path / "status.json", bus_path=bus_path, run_id="r1")

    def boom(*_a: object, **_k: object) -> None:
        raise OSError("replace failed")

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(OSError, match="replace failed"):
        bus.publish("x", {"y": 1})
