import json
from pathlib import Path
from uuid import uuid4

import pytest

from vibey.application.dto import RunSpec
from vibey.domain.effort import Effort
from vibey.domain.engine import IsolationLevel
from vibey.domain.ledger import EventKind
from vibey.domain.phase import Phase
from vibey.infrastructure.engines.descriptors import ALL_DESCRIPTORS, CLAUDELOOP
from vibey.infrastructure.engines.scripted import ScriptedEngine
from vibey.infrastructure.engines.tailer import (
    UnknownEventKind,
    translate_event,
    translate_run_iter,
)


def _spec(worktree: Path) -> RunSpec:
    return RunSpec(
        run_id=uuid4(),
        worktree_path=worktree,
        prompt="implement the outbox relay",
        effort=Effort.LOW,
        isolation=IsolationLevel.WORKTREE,
    )


async def test_start_writes_the_real_run_directory_shape(tmp_path: Path) -> None:
    engine = ScriptedEngine(descriptor=CLAUDELOOP, base_dir=tmp_path)
    spec = _spec(tmp_path / "worktree")

    handle = await engine.start(spec)

    for expected in (
        "meta.json",
        "events.jsonl",
        "audit.jsonl",
        "bus.jsonl",
        "status.json",
        "savepoints.jsonl",
        "stop-summary.md",
    ):
        assert (handle.run_dir / expected).exists(), f"missing {expected}"
    assert (handle.run_dir / "inbox").is_dir()
    assert (handle.run_dir / "snapshots" / "latest.json").exists()


async def test_run_dir_is_under_the_descriptors_state_dir(tmp_path: Path) -> None:
    engine = ScriptedEngine(descriptor=CLAUDELOOP, base_dir=tmp_path)
    spec = _spec(tmp_path / "worktree")

    handle = await engine.start(spec)

    assert f"/{CLAUDELOOP.state_dir}/runs/{spec.run_id}" in str(handle.run_dir)


async def test_meta_json_matches_the_descriptor_and_spec(tmp_path: Path) -> None:
    engine = ScriptedEngine(descriptor=CLAUDELOOP, base_dir=tmp_path)
    spec = _spec(tmp_path / "worktree")

    handle = await engine.start(spec)
    meta = json.loads((handle.run_dir / "meta.json").read_text())

    assert meta["run_id"] == str(spec.run_id)
    assert meta["effort"] == "low"


async def test_snapshot_schema_version_is_one(tmp_path: Path) -> None:
    engine = ScriptedEngine(descriptor=CLAUDELOOP, base_dir=tmp_path)
    spec = _spec(tmp_path / "worktree")
    handle = await engine.start(spec)

    snapshot = await engine.snapshot(handle)

    assert snapshot is not None
    assert snapshot.schema_version == 1


async def test_preflight_reports_installed_and_auth_ok_by_default(tmp_path: Path) -> None:
    engine = ScriptedEngine(descriptor=CLAUDELOOP, base_dir=tmp_path)
    result = await engine.preflight()
    assert result.installed is True
    assert result.auth_ok is True
    assert result.version == CLAUDELOOP.min_version


async def test_preflight_reports_not_installed_when_configured(tmp_path: Path) -> None:
    engine = ScriptedEngine(descriptor=CLAUDELOOP, base_dir=tmp_path, installed=False)
    result = await engine.preflight()
    assert result.installed is False


async def test_stop_writes_a_stop_summary_and_returns_it(tmp_path: Path) -> None:
    engine = ScriptedEngine(descriptor=CLAUDELOOP, base_dir=tmp_path)
    handle = await engine.start(_spec(tmp_path / "worktree"))

    summary = await engine.stop(handle)

    assert summary.complete is True
    assert (handle.run_dir / "stop-summary.md").read_text().strip()


async def test_send_prompt_writes_the_control_plane_inbox(tmp_path: Path) -> None:
    engine = ScriptedEngine(descriptor=CLAUDELOOP, base_dir=tmp_path)
    handle = await engine.start(_spec(tmp_path / "worktree"))

    await engine.send_prompt(handle, "please add a test for the retry cap", now=True)

    inbox_files = list((handle.run_dir / "inbox").glob("*.json"))
    assert len(inbox_files) == 1
    written = json.loads(inbox_files[0].read_text())
    assert written["command"] == "prompt-now"
    assert written["text"] == "please add a test for the retry cap"


async def test_send_prompt_at_break_uses_a_different_command(tmp_path: Path) -> None:
    engine = ScriptedEngine(descriptor=CLAUDELOOP, base_dir=tmp_path)
    handle = await engine.start(_spec(tmp_path / "worktree"))

    await engine.send_prompt(handle, "continue when convenient", now=False)

    inbox_files = list((handle.run_dir / "inbox").glob("*.json"))
    written = json.loads(inbox_files[0].read_text())
    assert written["command"] == "prompt-at-break"


async def test_multiple_prompts_do_not_clobber_each_other(tmp_path: Path) -> None:
    engine = ScriptedEngine(descriptor=CLAUDELOOP, base_dir=tmp_path)
    handle = await engine.start(_spec(tmp_path / "worktree"))

    await engine.send_prompt(handle, "first", now=True)
    await engine.send_prompt(handle, "second", now=True)

    inbox_files = list((handle.run_dir / "inbox").glob("*.json"))
    assert len(inbox_files) == 2


async def test_tail_yields_engine_events_in_file_order(tmp_path: Path) -> None:
    engine = ScriptedEngine(descriptor=CLAUDELOOP, base_dir=tmp_path)
    handle = await engine.start(_spec(tmp_path / "worktree"))

    kinds = [e.kind async for e in engine.tail(handle)]

    assert kinds == ["SessionSeeded", "TurnCompleted", "VerdictRendered"]


async def test_replaying_a_scripted_run_directory_through_the_tailer_produces_ledger_drafts(
    tmp_path: Path,
) -> None:
    """Stands in for '3.5: replay a captured real run dir from each engine' --
    no real vendor binaries were available, so the fixture is a scripted run
    directory written to real disk in the documented shape, which the tailer
    then replays exactly as it would a captured one."""
    engine = ScriptedEngine(descriptor=CLAUDELOOP, base_dir=tmp_path)
    spec = _spec(tmp_path / "worktree")
    handle = await engine.start(spec)

    project_id = uuid4()
    correlation_id = uuid4()
    drafts = [
        d
        async for d in translate_run_iter(
            engine.tail(handle),
            project_id=project_id,
            cycle=1,
            phase=Phase.BUILD,
            engine_id=CLAUDELOOP.engine_id,
            job_id=None,
            correlation_id=correlation_id,
        )
    ]

    assert [d.kind for d in drafts] == [
        EventKind.SESSION_SEEDED,
        EventKind.TURN_COMPLETED,
        EventKind.VERDICT_RENDERED,
    ]
    assert all(d.project_id == project_id for d in drafts)
    assert all(d.correlation_id == correlation_id for d in drafts)
    assert all(d.digest for d in drafts)


async def test_explicit_help_text_is_not_overwritten(tmp_path: Path) -> None:
    engine = ScriptedEngine(descriptor=CLAUDELOOP, base_dir=tmp_path, help_text="custom --flag")
    assert engine.help_text == "custom --flag"


async def test_tail_skips_blank_lines(tmp_path: Path) -> None:
    engine = ScriptedEngine(descriptor=CLAUDELOOP, base_dir=tmp_path)
    handle = await engine.start(_spec(tmp_path / "worktree"))
    events_path = handle.run_dir / "events.jsonl"
    content = events_path.read_text()
    events_path.write_text("\n\n" + content + "\n\n")

    kinds = [e.kind async for e in engine.tail(handle)]
    assert kinds == ["SessionSeeded", "TurnCompleted", "VerdictRendered"]


async def test_snapshot_returns_none_when_latest_json_missing(tmp_path: Path) -> None:
    engine = ScriptedEngine(descriptor=CLAUDELOOP, base_dir=tmp_path)
    handle = await engine.start(_spec(tmp_path / "worktree"))
    (handle.run_dir / "snapshots" / "latest.json").unlink()

    result = await engine.snapshot(handle)
    assert result is None


async def test_attribute_returns_a_failure_class(tmp_path: Path) -> None:
    engine = ScriptedEngine(descriptor=CLAUDELOOP, base_dir=tmp_path)
    from vibey.domain.job import FailureClass

    fc = engine.attribute(1, "something went wrong")
    assert isinstance(fc, FailureClass)


def test_translate_event_raises_on_unknown_kind() -> None:
    from datetime import UTC, datetime

    from vibey.application.dto import EngineEvent

    event = EngineEvent(kind="TotallyUnknownKind", at=datetime.now(UTC), payload={})
    with pytest.raises(UnknownEventKind) as exc_info:
        translate_event(
            event,
            project_id=uuid4(),
            cycle=1,
            phase=Phase.BUILD,
            engine_id=CLAUDELOOP.engine_id,
            job_id=None,
            correlation_id=uuid4(),
        )
    assert exc_info.value.kind == "TotallyUnknownKind"


async def test_scripted_available_run_factory(tmp_path: Path) -> None:
    from vibey.infrastructure.engines.scripted import scripted_available_run

    engine = scripted_available_run(CLAUDELOOP, tmp_path)
    assert isinstance(engine, ScriptedEngine)
    assert engine.descriptor == CLAUDELOOP


async def test_all_four_descriptors_produce_a_valid_run_directory(tmp_path: Path) -> None:
    for descriptor in ALL_DESCRIPTORS:
        engine = ScriptedEngine(descriptor=descriptor, base_dir=tmp_path)
        handle = await engine.start(_spec(tmp_path / f"worktree-{descriptor.engine_id}"))
        assert (handle.run_dir / "meta.json").exists()
        assert descriptor.state_dir in str(handle.run_dir)
