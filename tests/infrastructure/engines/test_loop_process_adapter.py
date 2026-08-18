"""Tests for infrastructure/engines/loop_process_adapter.py.

Tests the LoopProcessAdapter's file-based operations (snapshot, send_prompt,
stop, classify, attribute) without spawning real subprocesses.
"""

import json
from pathlib import Path
from uuid import uuid4

from vibey.application.dto import RunHandle
from vibey.domain.capacity import CreditsExhausted
from vibey.domain.engine import EngineId
from vibey.domain.job import FailureClass
from vibey.infrastructure.engines.classify import CREDITS_FIXTURES
from vibey.infrastructure.engines.descriptors import CLAUDELOOP, CODEXLOOP
from vibey.infrastructure.engines.loop_process_adapter import (
    EXIT_CODE_WIND_DOWN,
    LoopProcessAdapter,
)


def _make_handle(run_dir: Path) -> RunHandle:
    return RunHandle(
        run_id=uuid4(),
        engine_id=EngineId.CLAUDELOOP,
        run_dir=run_dir,
        pid=None,
    )


def test_exit_code_wind_down_is_75() -> None:
    assert EXIT_CODE_WIND_DOWN == 75


def test_descriptor_property() -> None:
    adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
    assert adapter.descriptor is CLAUDELOOP


def test_classify_credits_exhausted() -> None:
    adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
    result = adapter.classify(CREDITS_FIXTURES[EngineId.CLAUDELOOP])
    assert isinstance(result, CreditsExhausted)


def test_attribute_normal_exit() -> None:
    adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
    result = adapter.attribute(0, "")
    assert result == FailureClass.WORK


def test_attribute_wind_down() -> None:
    adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
    result = adapter.attribute(75, "")
    assert isinstance(result, FailureClass)


async def test_send_prompt_writes_inbox_file(tmp_path: Path) -> None:
    adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
    run_dir = tmp_path / ".claudeloop" / "runs" / "test-run"
    run_dir.mkdir(parents=True)
    handle = _make_handle(run_dir)

    await adapter.send_prompt(handle, "Hello from test", now=True)

    inbox = run_dir / "inbox"
    assert inbox.is_dir()
    files = list(inbox.iterdir())
    assert len(files) == 1
    content = json.loads(files[0].read_text())
    assert content["command"] == "prompt-now"
    assert content["text"] == "Hello from test"


async def test_send_prompt_at_break(tmp_path: Path) -> None:
    adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
    run_dir = tmp_path / ".claudeloop" / "runs" / "test-run"
    run_dir.mkdir(parents=True)
    handle = _make_handle(run_dir)

    await adapter.send_prompt(handle, "Later prompt", now=False)

    inbox = run_dir / "inbox"
    files = list(inbox.iterdir())
    content = json.loads(files[0].read_text())
    assert content["command"] == "prompt-at-break"


async def test_snapshot_returns_ref_when_file_exists(tmp_path: Path) -> None:
    adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
    run_dir = tmp_path / "test-run"
    run_dir.mkdir(parents=True)
    handle = _make_handle(run_dir)

    snapshot_dir = run_dir / "snapshots"
    snapshot_dir.mkdir(parents=True)
    snapshot_file = snapshot_dir / "latest.json"
    snapshot_file.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "session_id": "sess-123",
            }
        )
    )

    ref = await adapter.snapshot(handle)

    assert ref is not None
    assert ref.schema_version == 1
    assert ref.session_id == "sess-123"


async def test_snapshot_returns_none_when_missing(tmp_path: Path) -> None:
    adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
    run_dir = tmp_path / "test-run"
    run_dir.mkdir(parents=True)
    handle = _make_handle(run_dir)

    ref = await adapter.snapshot(handle)
    assert ref is None


async def test_snapshot_returns_none_on_invalid_json(tmp_path: Path) -> None:
    adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
    run_dir = tmp_path / "test-run"
    run_dir.mkdir(parents=True)
    handle = _make_handle(run_dir)

    snapshot_dir = run_dir / "snapshots"
    snapshot_dir.mkdir(parents=True)
    (snapshot_dir / "latest.json").write_text("{invalid json")

    ref = await adapter.snapshot(handle)
    assert ref is None


async def test_stop_writes_stop_signal(tmp_path: Path) -> None:
    adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
    run_dir = tmp_path / "test-run"
    run_dir.mkdir(parents=True)
    handle = _make_handle(run_dir)

    # Write a summary so stop() doesn't wait 30 seconds
    summary_path = run_dir / "stop-summary.md"
    summary_path.write_text("Run stopped normally.")

    summary = await adapter.stop(handle)

    assert summary.run_id == handle.run_id
    assert summary.complete is False  # no done marker
    assert "stopped" in summary.summary.lower() or "Run stopped" in summary.summary


async def test_stop_detects_done_marker(tmp_path: Path) -> None:
    adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
    run_dir = tmp_path / "test-run"
    run_dir.mkdir(parents=True)
    handle = _make_handle(run_dir)

    summary_path = run_dir / "stop-summary.md"
    summary_path.write_text(f"All done! {CLAUDELOOP.done_marker}")

    summary = await adapter.stop(handle)
    assert summary.complete is True


async def test_preflight_not_installed(tmp_path: Path) -> None:
    from vibey.infrastructure.engines.descriptors import EngineDescriptor, EngineId

    fake_desc = EngineDescriptor(
        engine_id=EngineId.CLAUDELOOP,
        binary="vibey_test_nonexistent_binary_12345",
        min_version="0.1.0",
        state_dir=".test",
        done_marker="TEST_DONE",
        auth_env=("TEST_KEY",),
        capabilities=frozenset(),
        effort_projection=CLAUDELOOP.effort_projection,
        session_verb="sessions",
        isolation_flags=CLAUDELOOP.isolation_flags,
        cost_per_mtok_in=1.0,
        cost_per_mtok_out=5.0,
        context_window=100_000,
    )
    adapter = LoopProcessAdapter(descriptor=fake_desc)

    result = await adapter.preflight()

    assert result.installed is False
    assert result.version is None


def test_adapter_works_with_any_descriptor() -> None:
    adapter = LoopProcessAdapter(descriptor=CODEXLOOP)
    assert adapter.descriptor.engine_id == EngineId.CODEXLOOP


def _make_fake_binary(tmp_path: Path, name: str, script: str) -> Path:
    """Create a fake binary script and add its directory to PATH."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    binary = bin_dir / name
    binary.write_text(f"#!/bin/sh\n{script}\n")
    binary.chmod(0o755)
    return bin_dir


async def test_tail_yields_translated_events(tmp_path: Path) -> None:
    adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
    run_dir = tmp_path / "test-run"
    run_dir.mkdir(parents=True)
    handle = _make_handle(run_dir)

    events_path = run_dir / "events.jsonl"
    events_path.write_text(
        '{"event_type":"session.started","at":"2026-01-01T00:00:00+00:00","payload":{}}\n'
        '{"event_type":"chatter.assistant","at":"2026-01-01T00:00:01+00:00","payload":{"text":"hi"}}\n'
    )

    meta_path = run_dir / "meta.json"
    meta_path.write_text('{"status":"complete"}')

    events = []
    async for event in adapter.tail(handle):
        events.append(event)

    assert len(events) == 2
    assert events[0].kind == "SessionSeeded"
    assert events[1].kind == "TurnCompleted"


async def test_tail_skips_unknown_event_types(tmp_path: Path) -> None:
    adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
    run_dir = tmp_path / "test-run"
    run_dir.mkdir(parents=True)
    handle = _make_handle(run_dir)

    events_path = run_dir / "events.jsonl"
    events_path.write_text(
        '{"event_type":"totally.unknown","at":"2026-01-01T00:00:00+00:00","payload":{}}\n'
        '{"event_type":"session.started","at":"2026-01-01T00:00:01+00:00","payload":{}}\n'
    )

    meta_path = run_dir / "meta.json"
    meta_path.write_text('{"status":"complete"}')

    events = []
    async for event in adapter.tail(handle):
        events.append(event)

    assert len(events) == 1
    assert events[0].kind == "SessionSeeded"


async def test_tail_skips_events_missing_type(tmp_path: Path) -> None:
    adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
    run_dir = tmp_path / "test-run"
    run_dir.mkdir(parents=True)
    handle = _make_handle(run_dir)

    events_path = run_dir / "events.jsonl"
    events_path.write_text(
        '{"payload":{"no":"type"}}\n'
        '{"event_type":"session.started","at":"2026-01-01T00:00:00+00:00","payload":{}}\n'
    )

    meta_path = run_dir / "meta.json"
    meta_path.write_text('{"status":"complete"}')

    events = []
    async for event in adapter.tail(handle):
        events.append(event)

    assert len(events) == 1


async def test_tail_skips_invalid_json_lines(tmp_path: Path) -> None:
    adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
    run_dir = tmp_path / "test-run"
    run_dir.mkdir(parents=True)
    handle = _make_handle(run_dir)

    events_path = run_dir / "events.jsonl"
    events_path.write_text(
        "not valid json\n"
        '{"event_type":"session.started","at":"2026-01-01T00:00:00+00:00","payload":{}}\n'
    )

    meta_path = run_dir / "meta.json"
    meta_path.write_text('{"status":"complete"}')

    events = []
    async for event in adapter.tail(handle):
        events.append(event)

    assert len(events) == 1


async def test_tail_skips_blank_lines(tmp_path: Path) -> None:
    adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
    run_dir = tmp_path / "test-run"
    run_dir.mkdir(parents=True)
    handle = _make_handle(run_dir)

    events_path = run_dir / "events.jsonl"
    events_path.write_text(
        '\n   \n{"event_type":"session.started","at":"2026-01-01T00:00:00+00:00","payload":{}}\n'
    )

    meta_path = run_dir / "meta.json"
    meta_path.write_text('{"status":"complete"}')

    events = []
    async for event in adapter.tail(handle):
        events.append(event)

    assert len(events) == 1


async def test_tail_returns_immediately_when_events_file_missing(tmp_path: Path) -> None:
    """tail() must return without blocking when events.jsonl never appears."""
    adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
    run_dir = tmp_path / "test-run"
    run_dir.mkdir(parents=True)
    handle = _make_handle(run_dir)

    events: list[object] = []
    async for event in adapter.tail(handle):
        events.append(event)

    assert events == []


async def test_tail_uses_kind_field_fallback(tmp_path: Path) -> None:
    adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
    run_dir = tmp_path / "test-run"
    run_dir.mkdir(parents=True)
    handle = _make_handle(run_dir)

    events_path = run_dir / "events.jsonl"
    events_path.write_text(
        '{"kind":"session.started","at":"2026-01-01T00:00:00+00:00","payload":{}}\n'
    )

    meta_path = run_dir / "meta.json"
    meta_path.write_text('{"status":"complete"}')

    events = []
    async for event in adapter.tail(handle):
        events.append(event)

    assert len(events) == 1
    assert events[0].kind == "SessionSeeded"


async def test_tail_uses_timestamp_field_fallback(tmp_path: Path) -> None:
    adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
    run_dir = tmp_path / "test-run"
    run_dir.mkdir(parents=True)
    handle = _make_handle(run_dir)

    events_path = run_dir / "events.jsonl"
    events_path.write_text(
        '{"event_type":"session.started","timestamp":"2026-06-15T12:00:00+00:00","payload":{}}\n'
    )

    meta_path = run_dir / "meta.json"
    meta_path.write_text('{"status":"complete"}')

    events = []
    async for event in adapter.tail(handle):
        events.append(event)

    assert len(events) == 1
    assert events[0].at.year == 2026


async def test_tail_defaults_timestamp_to_now(tmp_path: Path) -> None:
    adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
    run_dir = tmp_path / "test-run"
    run_dir.mkdir(parents=True)
    handle = _make_handle(run_dir)

    events_path = run_dir / "events.jsonl"
    events_path.write_text('{"event_type":"session.started","payload":{}}\n')

    meta_path = run_dir / "meta.json"
    meta_path.write_text('{"status":"complete"}')

    events = []
    async for event in adapter.tail(handle):
        events.append(event)

    assert len(events) == 1
    assert events[0].at is not None


async def test_stop_extracts_remaining_work_from_snapshot(tmp_path: Path) -> None:
    adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
    run_dir = tmp_path / "test-run"
    run_dir.mkdir(parents=True)
    handle = _make_handle(run_dir)

    summary_path = run_dir / "stop-summary.md"
    summary_path.write_text("Stopping run.")

    snapshot_dir = run_dir / "snapshots"
    snapshot_dir.mkdir(parents=True)
    (snapshot_dir / "latest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "remaining_work": ["task-a", "task-b"],
            }
        )
    )

    summary = await adapter.stop(handle)
    assert summary.remaining_work == ("task-a", "task-b")


async def test_stop_handles_missing_summary(tmp_path: Path) -> None:
    adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
    run_dir = tmp_path / "test-run"
    run_dir.mkdir(parents=True)
    handle = _make_handle(run_dir)

    summary = await adapter.stop(handle)
    assert summary.complete is False
    assert str(handle.run_id) in summary.summary


async def test_stop_handles_invalid_snapshot_json(tmp_path: Path) -> None:
    adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
    run_dir = tmp_path / "test-run"
    run_dir.mkdir(parents=True)
    handle = _make_handle(run_dir)

    summary_path = run_dir / "stop-summary.md"
    summary_path.write_text("Done.")

    snapshot_dir = run_dir / "snapshots"
    snapshot_dir.mkdir(parents=True)
    (snapshot_dir / "latest.json").write_text("{bad json")

    summary = await adapter.stop(handle)
    assert summary.remaining_work == ()


async def test_start_raises_process_error_on_spawn_failure(tmp_path: Path) -> None:
    from vibey.application.dto import RunSpec
    from vibey.domain.effort import Effort
    from vibey.domain.engine import IsolationLevel
    from vibey.infrastructure.engines.loop_process_adapter import ProcessError

    fake_desc = CLAUDELOOP.__class__(
        engine_id=EngineId.CLAUDELOOP,
        binary="vibey_test_nonexistent_binary_12345",
        min_version="0.1.0",
        state_dir=".test",
        done_marker="TEST_DONE",
        auth_env=("TEST_KEY",),
        capabilities=frozenset(),
        effort_projection=CLAUDELOOP.effort_projection,
        session_verb="sessions",
        isolation_flags=CLAUDELOOP.isolation_flags,
        cost_per_mtok_in=1.0,
        cost_per_mtok_out=5.0,
        context_window=100_000,
    )
    adapter = LoopProcessAdapter(descriptor=fake_desc)

    import pytest

    spec = RunSpec(
        run_id=uuid4(),
        worktree_path=tmp_path,
        prompt="test prompt",
        effort=Effort.STANDARD,
        isolation=IsolationLevel.WORKTREE,
    )

    with pytest.raises(ProcessError, match="Failed to spawn"):
        await adapter.start(spec)


async def test_preflight_installed_with_doctor_ok(tmp_path: Path, monkeypatch: object) -> None:
    import os

    bin_dir = _make_fake_binary(tmp_path, "fakecli", 'echo "fakecli 1.2.3"')
    doctor_path = bin_dir / "fakecli"
    doctor_path.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = '--version' ]; then echo 'fakecli 1.2.3';"
        " elif [ \"$1\" = 'doctor' ]; then exit 0; fi\n"
    )
    doctor_path.chmod(0o755)

    old_path = os.environ.get("PATH", "")
    os.environ["PATH"] = f"{bin_dir}:{old_path}"
    try:
        desc = CLAUDELOOP.__class__(
            engine_id=EngineId.CLAUDELOOP,
            binary="fakecli",
            min_version="0.1.0",
            state_dir=".test",
            done_marker="TEST_DONE",
            auth_env=("TEST_KEY",),
            capabilities=frozenset(),
            effort_projection=CLAUDELOOP.effort_projection,
            session_verb="sessions",
            isolation_flags=CLAUDELOOP.isolation_flags,
            cost_per_mtok_in=1.0,
            cost_per_mtok_out=5.0,
            context_window=100_000,
        )
        adapter = LoopProcessAdapter(descriptor=desc)
        result = await adapter.preflight()

        assert result.installed is True
        assert result.version == "1.2.3"
        assert result.auth_ok is True
    finally:
        os.environ["PATH"] = old_path


async def test_preflight_installed_doctor_fails_reports_detail(
    tmp_path: Path,
) -> None:
    import os

    bin_dir = _make_fake_binary(tmp_path, "fakecli2", 'echo "fakecli2 0.5.0"')
    doctor_path = bin_dir / "fakecli2"
    doctor_path.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "--version" ]; then echo "fakecli2 0.5.0"; '
        'elif [ "$1" = "doctor" ]; then echo "auth error: bad token" >&2; exit 1; fi\n'
    )
    doctor_path.chmod(0o755)

    old_path = os.environ.get("PATH", "")
    os.environ["PATH"] = f"{bin_dir}:{old_path}"
    try:
        desc = CLAUDELOOP.__class__(
            engine_id=EngineId.CLAUDELOOP,
            binary="fakecli2",
            min_version="0.1.0",
            state_dir=".test",
            done_marker="TEST_DONE",
            auth_env=("VIBEY_TEST_FAKE_AUTH_KEY",),
            capabilities=frozenset(),
            effort_projection=CLAUDELOOP.effort_projection,
            session_verb="sessions",
            isolation_flags=CLAUDELOOP.isolation_flags,
            cost_per_mtok_in=1.0,
            cost_per_mtok_out=5.0,
            context_window=100_000,
        )
        adapter = LoopProcessAdapter(descriptor=desc)
        result = await adapter.preflight()

        assert result.installed is True
        assert result.version == "0.5.0"
        assert result.auth_ok is False
        assert "auth error" in result.detail
    finally:
        os.environ["PATH"] = old_path


async def test_preflight_version_timeout_still_checks_auth(tmp_path: Path) -> None:
    import os

    bin_dir = _make_fake_binary(tmp_path, "fakecli5", 'echo ""')
    doctor_path = bin_dir / "fakecli5"
    doctor_path.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "--version" ]; then sleep 30; '
        'elif [ "$1" = "doctor" ]; then exit 0; fi\n'
    )
    doctor_path.chmod(0o755)

    old_path = os.environ.get("PATH", "")
    os.environ["PATH"] = f"{bin_dir}:{old_path}"
    try:
        import asyncio
        from unittest.mock import patch

        desc = CLAUDELOOP.__class__(
            engine_id=EngineId.CLAUDELOOP,
            binary="fakecli5",
            min_version="0.1.0",
            state_dir=".test",
            done_marker="TEST_DONE",
            auth_env=("TEST_KEY",),
            capabilities=frozenset(),
            effort_projection=CLAUDELOOP.effort_projection,
            session_verb="sessions",
            isolation_flags=CLAUDELOOP.isolation_flags,
            cost_per_mtok_in=1.0,
            cost_per_mtok_out=5.0,
            context_window=100_000,
        )
        adapter = LoopProcessAdapter(descriptor=desc)

        orig_wait_for = asyncio.wait_for
        call_count = 0

        async def _patched_wait_for(coro: object, *, timeout: float) -> object:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise TimeoutError("version check timed out")
            return await orig_wait_for(coro, timeout=timeout)

        with patch("asyncio.wait_for", _patched_wait_for):
            result = await adapter.preflight()

        assert result.installed is True
        assert result.version is None
        assert result.auth_ok is True
    finally:
        os.environ["PATH"] = old_path


async def test_preflight_doctor_exception_falls_back_to_env(tmp_path: Path) -> None:
    import os

    bin_dir = _make_fake_binary(tmp_path, "fakecli6", 'echo "fakecli6 2.0.0"')
    doctor_path = bin_dir / "fakecli6"
    doctor_path.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "--version" ]; then echo "fakecli6 2.0.0"; '
        'elif [ "$1" = "doctor" ]; then sleep 60; fi\n'
    )
    doctor_path.chmod(0o755)

    old_path = os.environ.get("PATH", "")
    old_env = os.environ.get("VIBEY_TEST_FAKE_AUTH", None)
    os.environ["PATH"] = f"{bin_dir}:{old_path}"
    os.environ["VIBEY_TEST_FAKE_AUTH"] = "valid-key"
    try:
        import asyncio
        from unittest.mock import patch

        desc = CLAUDELOOP.__class__(
            engine_id=EngineId.CLAUDELOOP,
            binary="fakecli6",
            min_version="0.1.0",
            state_dir=".test",
            done_marker="TEST_DONE",
            auth_env=("VIBEY_TEST_FAKE_AUTH",),
            capabilities=frozenset(),
            effort_projection=CLAUDELOOP.effort_projection,
            session_verb="sessions",
            isolation_flags=CLAUDELOOP.isolation_flags,
            cost_per_mtok_in=1.0,
            cost_per_mtok_out=5.0,
            context_window=100_000,
        )
        adapter = LoopProcessAdapter(descriptor=desc)

        orig_wait_for = asyncio.wait_for
        call_count = 0

        async def _patched_wait_for(coro: object, *, timeout: float) -> object:
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise TimeoutError("doctor timed out")
            return await orig_wait_for(coro, timeout=timeout)

        with patch("asyncio.wait_for", _patched_wait_for):
            result = await adapter.preflight()

        assert result.installed is True
        assert result.version == "2.0.0"
        assert result.auth_ok is True
    finally:
        os.environ["PATH"] = old_path
        if old_env is None:
            os.environ.pop("VIBEY_TEST_FAKE_AUTH", None)
        else:
            os.environ["VIBEY_TEST_FAKE_AUTH"] = old_env


async def test_start_writes_plan_and_returns_handle(tmp_path: Path) -> None:
    import os

    from vibey.application.dto import RunSpec
    from vibey.domain.effort import Effort
    from vibey.domain.engine import IsolationLevel

    bin_dir = _make_fake_binary(tmp_path, "fakecli3", "sleep 60")
    old_path = os.environ.get("PATH", "")
    os.environ["PATH"] = f"{bin_dir}:{old_path}"
    try:
        desc = CLAUDELOOP.__class__(
            engine_id=EngineId.CLAUDELOOP,
            binary="fakecli3",
            min_version="0.1.0",
            state_dir=".test",
            done_marker="TEST_DONE",
            auth_env=("TEST_KEY",),
            capabilities=frozenset(),
            effort_projection=CLAUDELOOP.effort_projection,
            session_verb="sessions",
            isolation_flags=CLAUDELOOP.isolation_flags,
            cost_per_mtok_in=1.0,
            cost_per_mtok_out=5.0,
            context_window=100_000,
        )
        adapter = LoopProcessAdapter(descriptor=desc)

        # worktree_path is deliberately its own subdirectory, distinct from
        # tmp_path itself (where the fake binary lives) -- start() must root
        # run_dir under the RunSpec's own worktree_path, not wherever the
        # adapter happens to be constructed from. This is the regression
        # case for a real bug where run_dir was rooted under a fixed
        # adapter-level base_dir instead, silently breaking every downstream
        # tail()/stop()/snapshot() lookup whenever the two paths diverged.
        worktree_path = tmp_path / "project"
        worktree_path.mkdir()
        spec = RunSpec(
            run_id=uuid4(),
            worktree_path=worktree_path,
            prompt="test prompt here",
            effort=Effort.STANDARD,
            isolation=IsolationLevel.WORKTREE,
        )

        handle = await adapter.start(spec)

        assert handle.run_id == spec.run_id
        assert handle.engine_id == EngineId.CLAUDELOOP
        assert handle.pid is not None
        assert handle.run_dir == worktree_path / desc.state_dir / "runs" / str(spec.run_id)

        plan_file = worktree_path / ".vibey" / "plans" / f"{spec.run_id}.md"
        assert plan_file.exists()
        assert plan_file.read_text() == "test prompt here"

        import signal

        if handle.pid:
            os.kill(handle.pid, signal.SIGTERM)
    finally:
        os.environ["PATH"] = old_path


async def test_start_skips_plan_for_resume(tmp_path: Path) -> None:
    import os

    from vibey.application.dto import RunSpec
    from vibey.domain.effort import Effort
    from vibey.domain.engine import IsolationLevel

    bin_dir = _make_fake_binary(tmp_path, "fakecli4", "sleep 60")
    old_path = os.environ.get("PATH", "")
    os.environ["PATH"] = f"{bin_dir}:{old_path}"
    try:
        desc = CLAUDELOOP.__class__(
            engine_id=EngineId.CLAUDELOOP,
            binary="fakecli4",
            min_version="0.1.0",
            state_dir=".test",
            done_marker="TEST_DONE",
            auth_env=("TEST_KEY",),
            capabilities=frozenset(),
            effort_projection=CLAUDELOOP.effort_projection,
            session_verb="sessions",
            isolation_flags=CLAUDELOOP.isolation_flags,
            cost_per_mtok_in=1.0,
            cost_per_mtok_out=5.0,
            context_window=100_000,
        )
        adapter = LoopProcessAdapter(descriptor=desc)

        run_id = uuid4()
        spec = RunSpec(
            run_id=run_id,
            worktree_path=tmp_path,
            prompt="resume prompt",
            effort=Effort.STANDARD,
            isolation=IsolationLevel.WORKTREE,
            session_id="sess-existing",
        )

        handle = await adapter.start(spec)

        plan_dir = tmp_path / ".vibey" / "plans"
        assert not plan_dir.exists() or not (plan_dir / f"{run_id}.md").exists()

        import signal

        if handle.pid:
            os.kill(handle.pid, signal.SIGTERM)
    finally:
        os.environ["PATH"] = old_path


async def test_preflight_doctor_exception_no_env_reports_detail(tmp_path: Path) -> None:
    """When doctor raises and auth env vars aren't set, detail says so."""
    import os

    bin_dir = _make_fake_binary(tmp_path, "fakecli7", 'echo "fakecli7 3.0.0"')
    doctor_path = bin_dir / "fakecli7"
    doctor_path.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "--version" ]; then echo "fakecli7 3.0.0"; '
        'elif [ "$1" = "doctor" ]; then sleep 60; fi\n'
    )
    doctor_path.chmod(0o755)

    old_path = os.environ.get("PATH", "")
    os.environ["PATH"] = f"{bin_dir}:{old_path}"
    os.environ.pop("VIBEY_TEST_MISSING_KEY_XYZ", None)
    try:
        import asyncio
        from unittest.mock import patch

        desc = CLAUDELOOP.__class__(
            engine_id=EngineId.CLAUDELOOP,
            binary="fakecli7",
            min_version="0.1.0",
            state_dir=".test",
            done_marker="TEST_DONE",
            auth_env=("VIBEY_TEST_MISSING_KEY_XYZ",),
            capabilities=frozenset(),
            effort_projection=CLAUDELOOP.effort_projection,
            session_verb="sessions",
            isolation_flags=CLAUDELOOP.isolation_flags,
            cost_per_mtok_in=1.0,
            cost_per_mtok_out=5.0,
            context_window=100_000,
        )
        adapter = LoopProcessAdapter(descriptor=desc)

        orig_wait_for = asyncio.wait_for
        call_count = 0

        async def _patched_wait_for(coro: object, *, timeout: float) -> object:
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise TimeoutError("doctor timed out")
            return await orig_wait_for(coro, timeout=timeout)

        with patch("asyncio.wait_for", _patched_wait_for):
            result = await adapter.preflight()

        assert result.installed is True
        assert result.auth_ok is False
        assert "VIBEY_TEST_MISSING_KEY_XYZ" in result.detail
    finally:
        os.environ["PATH"] = old_path


async def test_tail_polls_until_complete(tmp_path: Path) -> None:
    """When meta.json isn't present initially, tail sleeps and retries."""
    import asyncio

    adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
    run_dir = tmp_path / "test-run"
    run_dir.mkdir(parents=True)
    handle = _make_handle(run_dir)

    events_path = run_dir / "events.jsonl"
    events_path.write_text(
        '{"event_type":"session.started","at":"2026-01-01T00:00:00+00:00","payload":{}}\n'
    )

    meta_path = run_dir / "meta.json"

    async def _write_meta_after_delay() -> None:
        await asyncio.sleep(0.6)
        meta_path.write_text('{"status":"running"}')
        await asyncio.sleep(0.6)
        meta_path.write_text('{"status":"complete"}')

    task = asyncio.create_task(_write_meta_after_delay())
    events: list[object] = []
    async for event in adapter.tail(handle):
        events.append(event)
    await task

    assert len(events) == 1


async def test_tail_outer_exception_breaks_loop(tmp_path: Path) -> None:
    """When an unexpected error occurs in tail's outer loop, it breaks cleanly."""
    adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
    run_dir = tmp_path / "test-run"
    run_dir.mkdir(parents=True)
    handle = _make_handle(run_dir)

    events_path = run_dir / "events.jsonl"
    events_path.write_text(
        '{"event_type":"session.started","at":"2026-01-01T00:00:00+00:00","payload":{}}\n'
    )

    meta_path = run_dir / "meta.json"
    meta_path.write_text("{invalid json for meta}")

    events: list[object] = []
    async for event in adapter.tail(handle):
        events.append(event)

    assert len(events) == 1


async def test_stop_remaining_work_round_trips_through_snapshot(tmp_path: Path) -> None:
    """stop() extracts remaining_work list from the snapshot file."""
    adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
    run_dir = tmp_path / "test-run"
    run_dir.mkdir(parents=True)
    handle = _make_handle(run_dir)

    summary_path = run_dir / "stop-summary.md"
    summary_path.write_text("Run stopped normally.")

    snapshot_dir = run_dir / "snapshots"
    snapshot_dir.mkdir(parents=True)
    (snapshot_dir / "latest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "session_id": "sess-123",
                "remaining_work": ["task-a", "task-b"],
            }
        )
    )

    summary = await adapter.stop(handle)
    assert summary.remaining_work == ("task-a", "task-b")


async def test_stop_handles_corrupt_snapshot_gracefully(tmp_path: Path) -> None:
    """When snapshot exists but re-read fails, stop() still returns."""
    from vibey.application.dto import SnapshotRef

    run_dir = tmp_path / "test-run"
    run_dir.mkdir(parents=True)

    corrupt_file = run_dir / "snapshots" / "latest.json"
    corrupt_file.parent.mkdir(parents=True)
    corrupt_file.write_text("{not valid json")

    fake_ref = SnapshotRef(path=corrupt_file, schema_version=1, session_id="s1")

    class _CorruptSnapshotAdapter(LoopProcessAdapter):
        async def snapshot(self, handle: RunHandle) -> SnapshotRef | None:
            return fake_ref

    adapter = _CorruptSnapshotAdapter(descriptor=CLAUDELOOP)
    handle = _make_handle(run_dir)

    summary_path = run_dir / "stop-summary.md"
    summary_path.write_text("Run stopped normally.")

    summary = await adapter.stop(handle)

    assert summary.remaining_work == ()
    assert summary.complete is False
