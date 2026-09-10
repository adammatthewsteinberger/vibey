# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Coverage for bootstrap composition helpers."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

import pytest

from codexloop.bootstrap import (
    DrainControl,
    RunnerConfig,
    build_api_typer_app,
    build_runner,
    create_savepoint,
    enqueue_run_control,
    events_path_for_run,
    list_run_records,
    list_savepoints,
    read_capacity_windows,
    read_run_events,
    read_run_record,
    read_run_state,
    register_drain,
    restore_run_snapshot,
    run_doctor_checks,
    run_is_live,
    run_stream_ui_for_events,
    take_snapshot,
    unwind_savepoint,
)
from codexloop.domain.control import Stop
from codexloop.domain.errors import ConfigurationError
from codexloop.domain.handoff_marker import HandoffMarker
from codexloop.domain.session import ThreadRef
from codexloop.infrastructure.agent.scripted import (
    ALLOW_TEST_AGENT_ENV,
    TEST_AGENT_SCRIPT_ENV,
)
from codexloop.infrastructure.rundir import RunDirectory, runs_root_for


def _seed_run(tmp_path: Path) -> RunDirectory:
    return RunDirectory.create(runs_root_for(tmp_path))


def test_register_drain_creates_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("codexloop.bootstrap._ACTIVE_DRAIN", None)
    drain = register_drain()
    assert isinstance(drain, DrainControl)
    assert register_drain() is drain


def test_json_thread_catalog_tolerates_bad_payloads(tmp_path: Path) -> None:
    path = tmp_path / ".codexloop" / "threads.json"
    path.parent.mkdir(parents=True)
    path.write_text("{not-json", encoding="utf-8")
    ctx = build_runner(RunnerConfig(), cwd=tmp_path, ensure_run=False)
    assert ctx.catalog is not None
    assert list(ctx.catalog.list_threads()) == []

    path.write_text(json.dumps({"nope": True}) + "\n", encoding="utf-8")
    ctx = build_runner(RunnerConfig(), cwd=tmp_path, ensure_run=False)
    assert list(ctx.catalog.list_threads()) == []

    path.write_text(
        json.dumps(
            [
                "skip",
                {"thread_id": "t1"},
                {
                    "thread_id": "t2",
                    "cwd": str(tmp_path),
                    "started_at": "not-a-date",
                    "model": "gpt",
                },
                {
                    "thread_id": "ok",
                    "cwd": str(tmp_path),
                    "started_at": "2026-08-13T00:00:00+00:00",
                    "model": "gpt-5",
                },
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    ctx = build_runner(RunnerConfig(), cwd=tmp_path, ensure_run=False)
    assert [t.thread_id for t in ctx.catalog.list_threads()] == ["ok"]
    assert ctx.catalog.get("ok") is not None
    assert ctx.catalog.get("missing") is None
    ctx.catalog.record(ThreadRef("new", str(tmp_path), datetime(2026, 8, 13, tzinfo=UTC), "gpt-5"))
    assert ctx.catalog.get("new") is not None


def test_select_gateway_returns_app_server_when_probe_succeeds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = object()

    async def ok(*, cwd: Path) -> tuple[object, None]:
        del cwd
        return fake, None

    monkeypatch.setattr("codexloop.bootstrap.probe_app_server_transport", ok)
    ctx = build_runner(RunnerConfig(), transport="app-server", cwd=tmp_path)
    assert ctx.gateway is fake


def test_select_gateway_prints_reason_on_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    async def fail(*, cwd: Path) -> tuple[None, str]:
        del cwd
        return None, "appserver unavailable"

    monkeypatch.setattr("codexloop.bootstrap.probe_app_server_transport", fail)
    build_runner(RunnerConfig(), transport="app-server", cwd=tmp_path)
    assert "appserver unavailable" in capsys.readouterr().err


def test_network_access_forces_exec_without_app_server_probe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    async def should_not_run(*, cwd: Path) -> tuple[object, None]:
        del cwd
        raise AssertionError("app-server probe must not run with network access")

    monkeypatch.setattr("codexloop.bootstrap.probe_app_server_transport", should_not_run)
    ctx = build_runner(RunnerConfig(network_access=True), transport="app-server", cwd=tmp_path)
    assert ctx.gateway.__class__.__name__ == "CodexExecGateway"
    assert "network access requires exec transport" in capsys.readouterr().err


def test_build_runner_records_effective_sandbox_settings(tmp_path: Path) -> None:
    ctx = build_runner(RunnerConfig(network_access=True), cwd=tmp_path)
    assert ctx.run_id is not None
    meta_path = runs_root_for(tmp_path) / ctx.run_id / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta["sandbox_mode"] == "workspace-write"
    assert meta["network_access"] is True

    assert ctx.handoff_marker_writer is not None
    marker = HandoffMarker(
        run_id=ctx.run_id,
        reason="test",
        produced_at=datetime(2026, 8, 22, tzinfo=UTC),
    )
    ctx.handoff_marker_writer(marker)
    assert (runs_root_for(tmp_path) / ctx.run_id / "handoff.json").is_file()


def test_build_runner_scripted_and_write_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixtures = Path(__file__).resolve().parent / "live" / "fixtures" / "agent_scripts"
    script = fixtures / "done.json"
    monkeypatch.setenv(ALLOW_TEST_AGENT_ENV, "1")
    monkeypatch.setenv(TEST_AGENT_SCRIPT_ENV, str(script))
    ctx = build_runner(RunnerConfig(), cwd=tmp_path, ensure_run=False)
    ctx.write_artifact("note.txt", "hi")  # no-op without rundir

    ctx2 = build_runner(RunnerConfig(), cwd=tmp_path, ensure_run=True)
    ctx2.write_artifact("note.txt", "hi")
    note = next((tmp_path / ".codexloop" / "runs").glob("*/note.txt"))
    assert note.read_text(encoding="utf-8") == "hi"


def test_list_and_read_run_helpers(tmp_path: Path) -> None:
    assert list_run_records(tmp_path) == []
    assert read_run_record(cwd=tmp_path) is None
    assert read_run_events(cwd=tmp_path) == ""
    assert read_run_state(cwd=tmp_path) == {}
    assert run_is_live(cwd=tmp_path) is False

    older = _seed_run(tmp_path)
    newer_root = runs_root_for(tmp_path) / "run_newer"
    newer_root.mkdir()
    (newer_root / "meta.json").write_text(
        json.dumps({"started_at": "not-iso", "pid": os.getpid()}) + "\n",
        encoding="utf-8",
    )
    (newer_root / "state.json").write_text(json.dumps(["not", "dict"]) + "\n", encoding="utf-8")
    (older.root / "meta.json").write_text(
        json.dumps({"started_at": "2020-01-01T00:00:00+00:00", "pid": "x"}) + "\n",
        encoding="utf-8",
    )
    (older.root / "events.jsonl").write_text("evt\n", encoding="utf-8")
    (older.root / "state.json").write_text(json.dumps({"phase": "wait"}) + "\n", encoding="utf-8")

    records = list_run_records(tmp_path)
    assert len(records) == 2
    latest = read_run_record(cwd=tmp_path)
    assert latest is not None
    assert latest["run_id"] == "run_newer"
    assert read_run_record(older.run_id, cwd=tmp_path)["run_id"] == older.run_id
    assert read_run_record("missing", cwd=tmp_path) is None
    assert read_run_events(older.run_id, cwd=tmp_path) == "evt\n"
    assert read_run_events("run_newer", cwd=tmp_path) == ""
    assert read_run_state(older.run_id, cwd=tmp_path)["phase"] == "wait"
    assert run_is_live("run_newer", cwd=tmp_path) is True
    assert run_is_live(older.run_id, cwd=tmp_path) is False

    dead = runs_root_for(tmp_path) / "run_dead"
    dead.mkdir()
    (dead / "meta.json").write_text(json.dumps({"pid": 999_999_999}) + "\n", encoding="utf-8")
    assert run_is_live("run_dead", cwd=tmp_path) is False


def test_latest_run_key_oserror(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from codexloop import bootstrap as boot

    record = {"root": str(tmp_path / "missing"), "meta": {}}

    def boom(self: Path) -> object:
        raise OSError("gone")

    monkeypatch.setattr(Path, "stat", boom)
    assert boot._latest_run_key(record) == datetime.min.replace(tzinfo=UTC)


def test_record_from_dir_non_dict_json(tmp_path: Path) -> None:
    from codexloop import bootstrap as boot

    root = tmp_path / "r"
    root.mkdir()
    (root / "meta.json").write_text(json.dumps(["x"]) + "\n", encoding="utf-8")
    (root / "state.json").write_text(json.dumps("s") + "\n", encoding="utf-8")
    record = boot._record_from_dir(root)
    assert record["meta"] == {}
    assert record["state"] == {}


def test_enqueue_and_savepoint_helpers(tmp_path: Path) -> None:
    rundir = _seed_run(tmp_path)
    path = enqueue_run_control(Stop(), cwd=tmp_path)
    assert path.is_file()
    with pytest.raises(ConfigurationError, match="no run found"):
        enqueue_run_control(Stop(), cwd=tmp_path / "empty")

    # non-git cwd → create returns None
    assert create_savepoint(cwd=tmp_path) is None
    assert list_savepoints(cwd=tmp_path) == []

    snap = take_snapshot(cwd=tmp_path, name="snap1")
    assert snap.is_dir()
    restore_run_snapshot("snap1", cwd=tmp_path)
    assert events_path_for_run(cwd=tmp_path) == rundir.events_path


def test_unwind_refuses_live(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _seed_run(tmp_path)
    monkeypatch.setattr("codexloop.bootstrap.run_is_live", lambda *a, **k: True)
    with pytest.raises(ConfigurationError, match="live"):
        unwind_savepoint("1", cwd=tmp_path)


def test_doctor_and_capacity_and_ui(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    report = run_doctor_checks(cwd=tmp_path)
    assert report.auth_mode
    monkeypatch.setattr(
        "codexloop.bootstrap.read_rollout_rate_limits",
        lambda: None,
    )
    assert read_capacity_windows(cwd=tmp_path) is None

    seen: list[Path] = []
    monkeypatch.setattr("codexloop.bootstrap.run_stream_ui", lambda path: seen.append(path))
    run_stream_ui_for_events(tmp_path / "events.jsonl")
    assert seen == [tmp_path / "events.jsonl"]
    assert build_api_typer_app() is not None


def test_unwind_success_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _seed_run(tmp_path)

    class _Store:
        def unwind(self, **kwargs: object) -> object:
            from codexloop.domain.savepoint import SavePointRef, UnwindResult

            point = SavePointRef(
                n=1,
                sha="abc",
                label="t",
                ref="refs/x",
                at=datetime(2026, 1, 1, tzinfo=UTC),
                committed=True,
            )
            return UnwindResult(to=point, backup_ref=None, restored_sha="abc")

    monkeypatch.setattr("codexloop.bootstrap.run_is_live", lambda *a, **k: False)
    monkeypatch.setattr("codexloop.bootstrap.GitSavePointStore", lambda **k: _Store())
    result = unwind_savepoint("1", cwd=tmp_path, backup=False)
    assert result.restored_sha == "abc"


def test_drain_and_register_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    from codexloop import bootstrap as boot

    monkeypatch.setattr(boot, "_ACTIVE_DRAIN", None)
    assert boot.current_drain() is None
    custom = DrainControl()
    assert register_drain(custom) is custom
    assert boot.current_drain() is custom
    custom.request_stop()
    assert list(custom.poll()) == [Stop()]
    assert list(custom.poll()) == []


def test_gateway_fallback_without_reason(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    async def fail(*, cwd: Path) -> tuple[None, str | None]:
        del cwd
        return None, None

    monkeypatch.setattr("codexloop.bootstrap.probe_app_server_transport", fail)
    build_runner(RunnerConfig(), transport="app-server", cwd=tmp_path)
    assert capsys.readouterr().err == ""


def test_unknown_transport_and_load_config(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="unknown transport"):
        build_runner(RunnerConfig(), transport="pigeon", cwd=tmp_path)
    ctx = build_runner(None, cwd=tmp_path, flags={"model": "gpt-test"})
    assert ctx.model == "gpt-test"


def test_latest_key_and_meta_branches(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from codexloop import bootstrap as boot

    # started_at present but not a string → fall through to mtime
    root = tmp_path / "r1"
    root.mkdir()
    (root / "meta.json").write_text(json.dumps({"started_at": 123}) + "\n", encoding="utf-8")
    key = boot._latest_run_key(boot._record_from_dir(root))
    assert key.tzinfo is not None

    # meta not a dict → mtime path
    assert boot._latest_run_key({"root": str(root), "meta": "nope"}).tzinfo is not None

    # state without meta
    only_state = tmp_path / "r2"
    only_state.mkdir()
    (only_state / "state.json").write_text(json.dumps({"a": 1}) + "\n", encoding="utf-8")
    record = boot._record_from_dir(only_state)
    assert record["meta"] == {}
    assert record["state"] == {"a": 1}

    monkeypatch.setattr(
        "codexloop.bootstrap.read_run_record",
        lambda *a, **k: {"meta": "bad", "root": str(tmp_path)},
    )
    assert run_is_live(cwd=tmp_path) is False
