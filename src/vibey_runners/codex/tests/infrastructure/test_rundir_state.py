# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Run directory layout, idempotent create, unique ids, and file state store."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from codexloop.infrastructure.events import JsonlRunEventSink
from codexloop.infrastructure.redact import REDACTED_VALUE
from codexloop.infrastructure.rundir import RunDirectory, runs_root_for
from codexloop.infrastructure.state import FileRunStateStore

_SK_TOKEN = "sk-abcdefghijklmnopqrstuvwxyz0123"


def test_runs_root_is_under_codexloop(tmp_path: Path) -> None:
    assert runs_root_for(tmp_path) == tmp_path / ".codexloop" / "runs"


def test_run_directory_layout(tmp_path: Path) -> None:
    directory = RunDirectory.create(runs_root_for(tmp_path))
    assert directory.meta_path.is_file()
    assert directory.state_path.is_file()
    assert directory.events_path.is_file()
    assert directory.inbox.is_dir()
    assert directory.archive.is_dir()
    meta = json.loads(directory.meta_path.read_text(encoding="utf-8"))
    assert meta["run_id"] == directory.run_id


def test_create_is_idempotent(tmp_path: Path) -> None:
    first = RunDirectory.create(runs_root_for(tmp_path))
    first.inbox.joinpath("keep.me").write_text("ok", encoding="utf-8")
    second = RunDirectory.create(runs_root_for(tmp_path), run_id=first.run_id)
    assert second.root == first.root
    assert second.inbox.joinpath("keep.me").read_text(encoding="utf-8") == "ok"
    assert second.meta_path.is_file()
    assert second.inbox.is_dir()
    assert second.archive.is_dir()


def test_update_meta_merges_effective_settings(tmp_path: Path) -> None:
    directory = RunDirectory.create(runs_root_for(tmp_path))
    directory.update_meta({"sandbox_mode": "workspace-write", "network_access": True})
    meta = json.loads(directory.meta_path.read_text(encoding="utf-8"))
    assert meta["run_id"] == directory.run_id
    assert meta["sandbox_mode"] == "workspace-write"
    assert meta["network_access"] is True


def test_update_meta_recovers_from_non_object_json(tmp_path: Path) -> None:
    directory = RunDirectory.create(runs_root_for(tmp_path))
    directory.meta_path.write_text("[]\n", encoding="utf-8")
    directory.update_meta({"network_access": False})
    assert json.loads(directory.meta_path.read_text(encoding="utf-8")) == {"network_access": False}


def test_run_id_is_uuid_and_never_reused(tmp_path: Path) -> None:
    first = RunDirectory.create(runs_root_for(tmp_path))
    second = RunDirectory.create(runs_root_for(tmp_path))
    assert first.run_id != second.run_id
    uuid.UUID(first.run_id)
    uuid.UUID(second.run_id)
    assert first.root != second.root
    assert first.root.is_dir()
    assert second.root.is_dir()


def test_file_run_state_store_roundtrip(tmp_path: Path) -> None:
    runs_root = runs_root_for(tmp_path)
    directory = RunDirectory.create(runs_root)
    store = FileRunStateStore(runs_root)
    assert store.load("missing") is None
    store.save(directory.run_id, {"attempt": 3, "phase": "turn"})
    assert store.load(directory.run_id) == {"attempt": 3, "phase": "turn"}
    assert json.loads(directory.state_path.read_text(encoding="utf-8")) == {
        "attempt": 3,
        "phase": "turn",
    }


def test_file_run_state_store_redacts_secrets(tmp_path: Path) -> None:
    runs_root = runs_root_for(tmp_path)
    directory = RunDirectory.create(runs_root)
    store = FileRunStateStore(runs_root)
    store.save(
        directory.run_id,
        {"phase": "turn", "secret_value": "super-secret", "note": _SK_TOKEN},
    )
    raw = json.loads(directory.state_path.read_text(encoding="utf-8"))
    assert raw["secret_value"] == REDACTED_VALUE
    assert _SK_TOKEN not in raw["note"]
    assert REDACTED_VALUE in raw["note"]


def test_state_store_non_object_json_is_none(tmp_path: Path) -> None:
    runs_root = tmp_path / "runs"
    run = runs_root / "rid"
    run.mkdir(parents=True)
    (run / "state.json").write_text("[1]\n", encoding="utf-8")
    assert FileRunStateStore(runs_root).load("rid") is None


def test_event_sink_creates_missing_file(tmp_path: Path) -> None:
    path = tmp_path / "new" / "events.jsonl"
    sink = JsonlRunEventSink(path)
    assert path.is_file()
    sink.emit({"event_type": "created"})
    assert "created" in path.read_text(encoding="utf-8")


def test_event_sink_appends_redacted_jsonl(tmp_path: Path) -> None:
    directory = RunDirectory.create(runs_root_for(tmp_path))
    sink = JsonlRunEventSink(directory.events_path)
    sink.emit({"event_type": "turn.started", "note": _SK_TOKEN, "ok": True})
    sink.emit({"event_type": "turn.completed"})
    raw_lines = directory.events_path.read_text(encoding="utf-8").splitlines()
    lines = [json.loads(line) for line in raw_lines]
    assert len(lines) == 2
    assert lines[0]["event_type"] == "turn.started"
    assert lines[0]["ok"] is True
    assert _SK_TOKEN not in json.dumps(lines[0])
    assert lines[0]["note"] == REDACTED_VALUE
    assert lines[1]["event_type"] == "turn.completed"
