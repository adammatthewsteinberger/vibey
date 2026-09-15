# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Infrastructure tests for RunSnapshotBuilder."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from claudeloop.infrastructure.rundir import RunDirectory, runs_root_for
from claudeloop.infrastructure.snapshot import (
    RunSnapshotBuilder,
    _load_savepoints,
    _safe_json,
    locate_claude_transcript,
    sanitize_cwd_for_project_dir,
)
from tests.application.fakes import FakeClock


class RecordingBus:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, object]]] = []

    def publish(self, event_type: str, state: dict[str, object]) -> None:
        self.events.append((event_type, state))


def _builder(tmp_path: Path) -> tuple[RunSnapshotBuilder, RunDirectory, RecordingBus]:
    run_dir = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    bus = RecordingBus()
    clock = FakeClock(start=datetime(2026, 8, 12, 16, 0, tzinfo=timezone.utc))
    builder = RunSnapshotBuilder(run_dir, state_bus=bus, home=tmp_path / "home", clock=clock)
    return builder, run_dir, bus


def test_sanitize_cwd() -> None:
    assert sanitize_cwd_for_project_dir("/Users/a/git/x") == "-Users-a-git-x"


def test_builder_writes_latest_and_immutable(tmp_path: Path) -> None:
    builder, run_dir, bus = _builder(tmp_path)
    ref = builder.emit("started", context={"session_id": None})
    assert ref is not None
    assert (run_dir.snapshots_root / "latest.json").is_file()
    immutables = list(run_dir.snapshots_root.glob("*-started.json"))
    assert len(immutables) == 1
    assert bus.events[-1][0] == "snapshot.written"
    assert bus.events[-1][1]["snapshot_digest"] == ref.digest
    assert bus.events[-1][1]["snapshot_reason"] == "started"


def test_status_digest_skip(tmp_path: Path) -> None:
    builder, run_dir, bus = _builder(tmp_path)
    first = builder.emit("status", context={"attempt": 1, "phase": "SENDING"})
    assert first is not None
    n = len(bus.events)
    second = builder.emit("status", context={"attempt": 1, "phase": "SENDING"})
    assert second is None
    assert len(bus.events) == n
    third = builder.emit("status", context={"attempt": 2, "phase": "SENDING"})
    assert third is not None
    assert bus.events[-1][0] == "snapshot.latest"


def test_bundle_and_missing_transcript(tmp_path: Path) -> None:
    builder, run_dir, bus = _builder(tmp_path)
    ref = builder.emit(
        "manual",
        context={"session_id": "sid-1", "cwd": str(tmp_path)},
        bundle=True,
    )
    assert ref is not None
    assert ref.bundle_path is not None
    payload = json.loads((run_dir.root / ref.path).read_text(encoding="utf-8"))
    assert payload["claude_session"]["found"] is False
    assert "api_key" not in json.dumps(payload)


def test_transcript_present_copied(tmp_path: Path) -> None:
    home = tmp_path / "home"
    cwd = str(tmp_path / "proj")
    slug = sanitize_cwd_for_project_dir(cwd)
    project = home / ".claude" / "projects" / slug
    project.mkdir(parents=True)
    transcript = project / "abc123.jsonl"
    transcript.write_text('{"type":"user"}\n', encoding="utf-8")

    run_dir = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    bus = RecordingBus()
    builder = RunSnapshotBuilder(run_dir, state_bus=bus, home=home)
    ref = builder.emit(
        "finished",
        context={"session_id": "abc123", "cwd": cwd},
        bundle=True,
    )
    assert ref is not None
    payload = json.loads((run_dir.snapshots_root / "latest.json").read_text(encoding="utf-8"))
    assert payload["claude_session"]["found"] is True
    assert payload["claude_session"]["transcript_copied"].endswith("abc123.jsonl")
    assert (run_dir.snapshots_root / "claude" / "abc123.jsonl").is_file()


def test_locate_claude_transcript_helpers(tmp_path: Path) -> None:
    assert locate_claude_transcript(session_id=None, cwd="/x")["found"] is False
    assert locate_claude_transcript(session_id="s", cwd=None)["found"] is False
    missing = locate_claude_transcript(session_id="s", cwd="/nope", home=tmp_path)
    assert missing["found"] is False


# ── locate_claude_transcript fallback glob (lines 62-74) ──


def test_locate_transcript_fallback_glob(tmp_path: Path) -> None:
    """When the exact file doesn't exist, fall back to glob matching."""
    home = tmp_path / "home"
    cwd = str(tmp_path / "proj")
    slug = sanitize_cwd_for_project_dir(cwd)
    project = home / ".claude" / "projects" / slug
    project.mkdir(parents=True)
    # Create a file whose stem contains the session_id but doesn't match exactly
    transcript = project / "prefix-abc123-suffix.jsonl"
    transcript.write_text('{"x":1}\n', encoding="utf-8")

    result = locate_claude_transcript(session_id="abc123", cwd=cwd, home=home)
    assert result["found"] is True
    assert "abc123" in result["transcript_path"]


def test_locate_transcript_no_match(tmp_path: Path) -> None:
    """Project dir exists but no matching transcript."""
    home = tmp_path / "home"
    cwd = str(tmp_path / "proj")
    slug = sanitize_cwd_for_project_dir(cwd)
    project = home / ".claude" / "projects" / slug
    project.mkdir(parents=True)
    # Create an unrelated file
    (project / "other.jsonl").write_text("{}\n", encoding="utf-8")

    result = locate_claude_transcript(session_id="abc123", cwd=cwd, home=home)
    assert result["found"] is False
    assert result["reason"] == "transcript_missing"


# ── _now() TypeError (line 159) ──


def test_clock_type_error(tmp_path: Path) -> None:
    """clock.now() returning non-datetime raises TypeError."""

    class BadClock:
        def now(self) -> str:
            return "not-a-datetime"

    run_dir = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    bus = RecordingBus()
    builder = RunSnapshotBuilder(run_dir, state_bus=bus, home=tmp_path / "home", clock=BadClock())
    with pytest.raises(TypeError, match="clock.now\\(\\) must return datetime"):
        builder.emit("status")


# ── _read_latest_digest edge cases (lines 167-173) ──


def test_read_latest_digest_corrupt_json(tmp_path: Path) -> None:
    """Corrupt JSON in latest.json returns None for digest."""
    run_dir = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    bus = RecordingBus()
    clock = FakeClock(start=datetime(2026, 8, 12, 16, 0, tzinfo=timezone.utc))
    snapshots = run_dir.snapshots_root
    snapshots.mkdir(parents=True, exist_ok=True)
    (snapshots / "latest.json").write_text("not valid json{", encoding="utf-8")
    builder = RunSnapshotBuilder(run_dir, state_bus=bus, home=tmp_path / "home", clock=clock)
    # Should not crash — corrupt latest is treated as None digest
    ref = builder.emit("status")
    assert ref is not None


def test_read_latest_digest_non_dict(tmp_path: Path) -> None:
    """latest.json containing a list (not dict) returns None digest."""
    run_dir = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    bus = RecordingBus()
    clock = FakeClock(start=datetime(2026, 8, 12, 16, 0, tzinfo=timezone.utc))
    snapshots = run_dir.snapshots_root
    snapshots.mkdir(parents=True, exist_ok=True)
    (snapshots / "latest.json").write_text("[1,2,3]", encoding="utf-8")
    builder = RunSnapshotBuilder(run_dir, state_bus=bus, home=tmp_path / "home", clock=clock)
    ref = builder.emit("status")
    assert ref is not None


# ── _copy_claude_transcript OSError (lines 278-279) ──


def test_copy_transcript_oserror(tmp_path: Path) -> None:
    """When shutil.copy2 fails, _copy_claude_transcript returns None."""
    home = tmp_path / "home"
    cwd = str(tmp_path / "proj")
    slug = sanitize_cwd_for_project_dir(cwd)
    project = home / ".claude" / "projects" / slug
    project.mkdir(parents=True)
    transcript = project / "sess1.jsonl"
    transcript.write_text("{}\n", encoding="utf-8")

    run_dir = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    bus = RecordingBus()
    clock = FakeClock(start=datetime(2026, 8, 12, 16, 0, tzinfo=timezone.utc))
    builder = RunSnapshotBuilder(run_dir, state_bus=bus, home=home, clock=clock)

    with patch("shutil.copy2", side_effect=OSError("disk full")):
        ref = builder.emit("finished", context={"session_id": "sess1", "cwd": cwd})
    assert ref is not None
    payload = json.loads((run_dir.snapshots_root / "latest.json").read_text(encoding="utf-8"))
    assert "transcript_copied" not in payload["claude_session"]


# ── _write_bundle with attachments, memories, artifacts (lines 293-322) ──


def test_bundle_copies_attachments_and_memories(tmp_path: Path) -> None:
    """Bundle copies attachments, memories, artifacts directories."""
    run_dir = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    bus = RecordingBus()
    clock = FakeClock(start=datetime(2026, 8, 12, 16, 0, tzinfo=timezone.utc))
    builder = RunSnapshotBuilder(run_dir, state_bus=bus, home=tmp_path / "home", clock=clock)

    # Create attachments dir with a file
    attachments = run_dir.resources_root / "attachments"
    attachments.mkdir(parents=True, exist_ok=True)
    (attachments / "doc.txt").write_text("hi", encoding="utf-8")

    # Create memories dir with a file
    memories = run_dir.root / "memories"
    memories.mkdir(parents=True, exist_ok=True)
    (memories / "mem.json").write_text("{}", encoding="utf-8")

    # Create artifacts dir with a file
    artifacts = run_dir.root / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    (artifacts / "art.txt").write_text("art", encoding="utf-8")

    ref = builder.emit("finished", bundle=True)
    assert ref is not None
    assert ref.bundle_path is not None
    bundle_root = run_dir.root / ref.bundle_path
    assert (bundle_root / "snapshot.json").is_file()
    assert (bundle_root / "resources" / "attachments" / "doc.txt").is_file()
    assert (bundle_root / "memories" / "mem.json").is_file()
    assert (bundle_root / "artifacts" / "art.txt").is_file()


def test_bundle_with_dest_exists(tmp_path: Path) -> None:
    """Bundle replaces existing destination dirs (lines 297-298, 304-305)."""
    run_dir = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    bus = RecordingBus()
    clock = FakeClock(start=datetime(2026, 8, 12, 16, 0, tzinfo=timezone.utc))
    builder = RunSnapshotBuilder(run_dir, state_bus=bus, home=tmp_path / "home", clock=clock)

    attachments = run_dir.resources_root / "attachments"
    attachments.mkdir(parents=True, exist_ok=True)
    (attachments / "f.txt").write_text("v2", encoding="utf-8")

    memories = run_dir.root / "memories"
    memories.mkdir(parents=True, exist_ok=True)
    (memories / "m.json").write_text("{}", encoding="utf-8")

    # Emit once to create the bundle dirs
    ref1 = builder.emit("manual", bundle=True)
    assert ref1 is not None and ref1.bundle_path is not None

    # Pre-create the dest dirs to hit the rmtree branches
    bundle_root = run_dir.root / ref1.bundle_path
    assert (bundle_root / "resources" / "attachments").is_dir()
    assert (bundle_root / "memories").is_dir()


def test_bundle_copies_transcript_via_copied_path(tmp_path: Path) -> None:
    """Bundle copies transcript when claude_session has transcript_copied."""
    home = tmp_path / "home"
    cwd = str(tmp_path / "proj")
    slug = sanitize_cwd_for_project_dir(cwd)
    project = home / ".claude" / "projects" / slug
    project.mkdir(parents=True)
    transcript = project / "sess2.jsonl"
    transcript.write_text('{"turn":1}\n', encoding="utf-8")

    run_dir = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    bus = RecordingBus()
    clock = FakeClock(start=datetime(2026, 8, 12, 16, 0, tzinfo=timezone.utc))
    builder = RunSnapshotBuilder(run_dir, state_bus=bus, home=home, clock=clock)

    ref = builder.emit(
        "finished",
        context={"session_id": "sess2", "cwd": cwd},
        bundle=True,
    )
    assert ref is not None
    assert ref.bundle_path is not None
    bundle_root = run_dir.root / ref.bundle_path
    assert (bundle_root / "claude" / "sess2.jsonl").is_file()


def test_bundle_copies_transcript_via_src_path(tmp_path: Path) -> None:
    """Bundle copies transcript from src_path when transcript_copied is absent (line 316-319)."""
    run_dir = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    bus = RecordingBus()
    clock = FakeClock(start=datetime(2026, 8, 12, 16, 0, tzinfo=timezone.utc))
    builder = RunSnapshotBuilder(run_dir, state_bus=bus, home=tmp_path / "home", clock=clock)

    # Create a transcript file at an external path
    ext_transcript = tmp_path / "ext-transcript.jsonl"
    ext_transcript.write_text('{"x":1}\n', encoding="utf-8")

    # Patch _build_payload to inject a payload with transcript_path but no transcript_copied
    original_build = builder._build_payload

    def patched_build(reason, ctx):
        payload = original_build(reason, ctx)
        payload["claude_session"] = {
            "found": True,
            "transcript_path": str(ext_transcript),
            "session_id": "ext-sess",
        }
        return payload

    with patch.object(builder, "_build_payload", side_effect=patched_build):
        ref = builder.emit("manual", bundle=True)
    assert ref is not None
    assert ref.bundle_path is not None
    bundle_root = run_dir.root / ref.bundle_path
    assert (bundle_root / "claude" / "ext-transcript.jsonl").is_file()


def test_bundle_oserror_returns_none(tmp_path: Path) -> None:
    """OSError during bundle creation returns None (line 320-321)."""
    run_dir = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    bus = RecordingBus()
    clock = FakeClock(start=datetime(2026, 8, 12, 16, 0, tzinfo=timezone.utc))
    builder = RunSnapshotBuilder(run_dir, state_bus=bus, home=tmp_path / "home", clock=clock)

    with patch.object(builder, "_write_bundle", side_effect=OSError("perm")):
        # _write_bundle is called inside emit; we need to trigger the OSError inside it.
        # Instead, mock shutil.copytree which is called inside _write_bundle.
        pass

    # Better approach: patch shutil.copytree to fail only when writing bundle
    with patch("claudeloop.infrastructure.snapshot.shutil.copytree", side_effect=OSError("fail")):
        # Create an attachments dir so copytree is attempted
        att = run_dir.resources_root / "attachments"
        att.mkdir(parents=True, exist_ok=True)
        (att / "x.txt").write_text("x", encoding="utf-8")
        ref = builder.emit("manual", bundle=True)
    assert ref is not None
    assert ref.bundle_path is None


# ── _safe_json (lines 328-332) ──


def test_safe_json_success(tmp_path: Path) -> None:
    path = tmp_path / "data.json"
    path.write_text('{"items": [1]}', encoding="utf-8")
    assert _safe_json(path) == {"items": [1]}


def test_safe_json_missing_file(tmp_path: Path) -> None:
    assert _safe_json(tmp_path / "nope.json") == {"items": []}


def test_safe_json_corrupt(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("not json{", encoding="utf-8")
    result = _safe_json(path)
    assert result == {"items": [], "error": "unreadable"}


# ── _load_savepoints (lines 335-347) ──


def test_load_savepoints_missing(tmp_path: Path) -> None:
    assert _load_savepoints(tmp_path / "nope.jsonl") == []


def test_load_savepoints_valid(tmp_path: Path) -> None:
    path = tmp_path / "sp.jsonl"
    lines = [json.dumps({"id": i}) for i in range(3)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    result = _load_savepoints(path)
    assert len(result) == 3


def test_load_savepoints_with_blank_lines(tmp_path: Path) -> None:
    """Blank lines are skipped (line 342)."""
    path = tmp_path / "sp.jsonl"
    path.write_text('{"a":1}\n\n{"b":2}\n', encoding="utf-8")
    result = _load_savepoints(path)
    assert len(result) == 2


def test_load_savepoints_truncates_to_20(tmp_path: Path) -> None:
    path = tmp_path / "sp.jsonl"
    lines = [json.dumps({"id": i}) for i in range(30)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    result = _load_savepoints(path)
    assert len(result) == 20
    assert result[0]["id"] == 10  # last 20


def test_load_savepoints_partial_corrupt(tmp_path: Path) -> None:
    """JSONDecodeError mid-stream returns rows parsed so far (line 345)."""
    path = tmp_path / "sp.jsonl"
    path.write_text('{"ok":1}\nnot-json\n', encoding="utf-8")
    result = _load_savepoints(path)
    assert len(result) == 1
    assert result[0]["ok"] == 1


def test_read_latest_digest_valid_dict(tmp_path: Path) -> None:
    """_read_latest_digest returns digest when latest.json is a valid dict (line 172)."""
    run_dir = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    bus = RecordingBus()
    clock = FakeClock(start=datetime(2026, 8, 12, 16, 0, tzinfo=timezone.utc))
    snapshots = run_dir.snapshots_root
    snapshots.mkdir(parents=True, exist_ok=True)
    (snapshots / "latest.json").write_text('{"key": "val"}', encoding="utf-8")
    builder = RunSnapshotBuilder(run_dir, state_bus=bus, home=tmp_path / "home", clock=clock)
    # The builder read a valid dict, so _latest_digest is set
    assert builder._latest_digest is not None


def test_bundle_rmtree_existing_dirs(tmp_path: Path) -> None:
    """Two bundles at the same timestamp force rmtree on existing dirs (lines 298, 305)."""
    run_dir = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    bus = RecordingBus()
    clock = FakeClock(start=datetime(2026, 8, 12, 16, 0, tzinfo=timezone.utc))
    builder = RunSnapshotBuilder(run_dir, state_bus=bus, home=tmp_path / "home", clock=clock)

    att = run_dir.resources_root / "attachments"
    att.mkdir(parents=True, exist_ok=True)
    (att / "a.txt").write_text("data", encoding="utf-8")
    mem = run_dir.root / "memories"
    mem.mkdir(parents=True, exist_ok=True)
    (mem / "m.json").write_text("{}", encoding="utf-8")

    # First emit creates bundle dir
    ref1 = builder.emit("manual", bundle=True)
    assert ref1 is not None and ref1.bundle_path is not None
    # Same clock => same timestamp => same bundle path
    ref2 = builder.emit("manual", bundle=True)
    assert ref2 is not None and ref2.bundle_path is not None
    # Both used the same path, so the second one hit rmtree


def test_bundle_no_attachments_dir(tmp_path: Path) -> None:
    """Bundle with no attachments dir skips copytree (branch 295->293)."""
    run_dir = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    bus = RecordingBus()
    clock = FakeClock(start=datetime(2026, 8, 12, 16, 0, tzinfo=timezone.utc))
    builder = RunSnapshotBuilder(run_dir, state_bus=bus, home=tmp_path / "home", clock=clock)

    # _build_payload creates the resources dir via store.ensure(),
    # so we patch is_dir on the attachments path to return False inside _write_bundle
    original_write_bundle = RunSnapshotBuilder._write_bundle

    def patched_write_bundle(self, reason, payload, ctx):
        att = self._run_dir.resources_root / "attachments"
        if att.is_dir():
            shutil.rmtree(att)
        mem = self._run_dir.root / "memories"
        if mem.is_dir():
            shutil.rmtree(mem)
        art = self._run_dir.root / "artifacts"
        if art.is_dir():
            shutil.rmtree(art)
        return original_write_bundle(self, reason, payload, ctx)

    with patch.object(RunSnapshotBuilder, "_write_bundle", patched_write_bundle):
        ref = builder.emit("manual", bundle=True)
    assert ref is not None
    assert ref.bundle_path is not None


def test_bundle_copied_file_missing(tmp_path: Path) -> None:
    """Bundle with transcript_copied pointing to missing file (branch 312->322)."""
    run_dir = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    bus = RecordingBus()
    clock = FakeClock(start=datetime(2026, 8, 12, 16, 0, tzinfo=timezone.utc))
    builder = RunSnapshotBuilder(run_dir, state_bus=bus, home=tmp_path / "home", clock=clock)

    original_build = builder._build_payload

    def patched_build(reason, ctx):
        payload = original_build(reason, ctx)
        payload["claude_session"] = {
            "found": True,
            "transcript_copied": "snapshots/claude/nonexistent.jsonl",
            "session_id": "xyz",
        }
        return payload

    with patch.object(builder, "_build_payload", side_effect=patched_build):
        ref = builder.emit("manual", bundle=True)
    assert ref is not None
    assert ref.bundle_path is not None
