# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Snapshot builder writes JSON under .agyloop/runs/<id>/snapshots/."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from agyloop.infrastructure.rundir import RunDirectory, runs_root_for
from agyloop.infrastructure.snapshot import RunSnapshotBuilder, _load_savepoints


class _FrozenClock:
    def now(self) -> datetime:
        return datetime(2026, 8, 13, 12, 0, tzinfo=UTC)


def test_manual_snapshot_writes_latest_and_bundle(tmp_path: Path) -> None:
    directory = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    directory.update_meta(conversation_id="conv-snap", status="finished")
    (directory.root / "plan.md").write_text("# Test Plan\n", encoding="utf-8")
    builder = RunSnapshotBuilder(directory)
    ref = builder.emit("manual", context={"session_id": "conv-snap"})
    assert ref is not None
    assert ref.reason == "manual"
    assert (directory.root / "snapshots" / "latest.json").is_file()
    assert (directory.root / ref.path).is_file()
    assert ref.bundle_path is not None
    assert (directory.root / ref.bundle_path / "snapshot.json").is_file()
    assert (directory.root / ref.bundle_path / "plan.md").is_file()


def test_status_snapshot_skips_duplicate_digest(tmp_path: Path) -> None:
    directory = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    builder = RunSnapshotBuilder(directory, clock=_FrozenClock())
    first = builder.emit("status", bundle=False)
    second = builder.emit("status", bundle=False)
    assert first is not None
    assert second is None


def test_snapshot_builder_edge_cases(tmp_path: Path) -> None:
    directory = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    directory.snapshots_root.mkdir(parents=True, exist_ok=True)

    # Corrupt latest.json
    latest = directory.snapshots_root / "latest.json"
    latest.write_text("invalid json", encoding="utf-8")

    builder = RunSnapshotBuilder(directory)
    assert builder._latest_digest is None

    latest.write_text('"string json"', encoding="utf-8")
    assert builder._read_latest_digest() is None

    latest.write_text(json.dumps({"schema_version": 1, "run_id": "r1"}), encoding="utf-8")
    assert builder._read_latest_digest() is not None

    # Invalid clock returning non-datetime
    class BadClock:
        def now(self) -> str:
            return "not a datetime"

    bad_builder = RunSnapshotBuilder(directory, clock=BadClock())
    with pytest.raises(TypeError, match="must return datetime"):
        bad_builder._now()

    # Bundle write OSError
    with patch("pathlib.Path.mkdir", side_effect=OSError("disk full")):
        res = builder._write_bundle("manual", {})
        assert res is None


def test_load_savepoints(tmp_path: Path) -> None:
    missing = tmp_path / "missing.jsonl"
    assert _load_savepoints(missing) == []

    sp_file = tmp_path / "savepoints.jsonl"
    lines = ["\n"] + [json.dumps({"idx": i}) for i in range(25)] + ["bad json\n"]
    sp_file.write_text("\n".join(lines), encoding="utf-8")

    rows = _load_savepoints(sp_file)
    assert len(rows) == 20  # capped at last 20
    assert rows[-1]["idx"] == 24

    with patch("pathlib.Path.read_text", side_effect=OSError("perm denied")):
        assert _load_savepoints(sp_file) == []
