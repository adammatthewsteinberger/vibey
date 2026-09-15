# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""RunDirSnapshotSink: the always-current run snapshot at a stable path.

The port existed with no implementation and no caller, so every codexloop
run looked snapshot-less to an external reader (vibey's conformance suite
reported exactly that). These tests pin the shape that reader depends on.
"""

from __future__ import annotations

import json
from pathlib import Path

from codexloop.infrastructure.run_snapshot import RunDirSnapshotSink


def test_writes_latest_json_with_schema_version(tmp_path: Path) -> None:
    sink = RunDirSnapshotSink(tmp_path / "snapshots")

    sink.write({"turns": 2, "session_id": "thread-1"})

    written = json.loads((tmp_path / "snapshots" / "latest.json").read_text())
    assert written["schema_version"] == 1
    assert written["turns"] == 2
    assert written["session_id"] == "thread-1"


def test_creates_the_snapshots_directory_when_absent(tmp_path: Path) -> None:
    sink = RunDirSnapshotSink(tmp_path / "deep" / "snapshots")

    sink.write({"turns": 0})

    assert (tmp_path / "deep" / "snapshots" / "latest.json").is_file()


def test_rewrites_in_place_leaving_no_temp_file(tmp_path: Path) -> None:
    """A poller reads this path at arbitrary instants: the write is atomic,
    and repeated turns must not accumulate files beside it."""
    sink = RunDirSnapshotSink(tmp_path / "snapshots")

    sink.write({"turns": 1})
    sink.write({"turns": 2})

    files = sorted(p.name for p in (tmp_path / "snapshots").iterdir())
    assert files == ["latest.json"]
    assert json.loads((tmp_path / "snapshots" / "latest.json").read_text())["turns"] == 2


def test_serializes_values_json_cannot_encode_natively(tmp_path: Path) -> None:
    """Run state carries paths and similar objects; a snapshot must never
    fail the run just because one field is not JSON-native."""
    sink = RunDirSnapshotSink(tmp_path / "snapshots")

    sink.write({"cwd": Path("/tmp/example")})

    written = json.loads((tmp_path / "snapshots" / "latest.json").read_text())
    assert written["cwd"] == "/tmp/example"
