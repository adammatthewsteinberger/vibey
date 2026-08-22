# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Tests for infrastructure/engines/loop_process_adapter.py.

Tests the LoopProcessAdapter's file-based operations (snapshot, send_prompt,
stop, classify, attribute) without spawning real subprocesses.
"""

import json
from pathlib import Path
from uuid import uuid4

import pytest

from vibey.application.dto import RunHandle
from vibey.domain.capacity import CreditsExhausted
from vibey.domain.engine import EngineId
from vibey.domain.job import FailureClass
from vibey.infrastructure.engines.classify import CREDITS_FIXTURES
from vibey.infrastructure.engines.descriptors import CLAUDELOOP, CODEXLOOP
from vibey.infrastructure.engines.loop_process_adapter import (
    EXIT_CODE_WIND_DOWN,
    LoopProcessAdapter,
    _active_processes,
    _communicate,
    _render_plan,
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


def test_render_plan_adds_codexloop_checkbox_without_losing_prompt() -> None:
    prompt = "Implement work item ws\n\nRun every verification gate."

    rendered = _render_plan(CODEXLOOP, prompt)

    assert rendered.startswith("# Work Plan\n\n- [ ] Implement work item ws\n")
    assert rendered.endswith(f"## Instructions\n\n{prompt}\n")


def test_render_plan_preserves_other_engine_prompts() -> None:
    assert _render_plan(CLAUDELOOP, "plain prompt") == "plain prompt"


def test_render_plan_handles_an_empty_codexloop_prompt() -> None:
    assert "- [ ] Complete task" in _render_plan(CODEXLOOP, "")


def _make_fake_binary(tmp_path: Path, name: str, script: str) -> Path:
    """Create a fake binary script and add its directory to PATH."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    binary = bin_dir / name
    binary.write_text(f"#!/bin/sh\n{script}\n")
    binary.chmod(0o755)
    return bin_dir


def test_help_text_returns_none_when_binary_not_found() -> None:
    fake_desc = CLAUDELOOP.__class__(
        engine_id=EngineId.CLAUDELOOP,
        binary="vibey_test_nonexistent_binary_for_help_text",
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
    assert adapter.help_text is None


def test_help_text_fetches_and_caches_real_output(tmp_path: Path) -> None:
    import os

    bin_dir = _make_fake_binary(
        tmp_path, "fakecli_help1", 'echo "usage: fakecli_help1 run [OPTIONS] --my-flag <str>"'
    )
    old_path = os.environ.get("PATH", "")
    os.environ["PATH"] = f"{bin_dir}:{old_path}"
    try:
        desc = CLAUDELOOP.__class__(
            engine_id=EngineId.CLAUDELOOP,
            binary="fakecli_help1",
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

        help_text = adapter.help_text

        assert help_text is not None
        assert "--my-flag" in help_text
    finally:
        os.environ["PATH"] = old_path


def test_help_text_is_cached_after_first_fetch(tmp_path: Path) -> None:
    """A binary invoked once for --help, not once per access."""
    import os

    counter_file = tmp_path / "invocation_count"
    bin_dir = _make_fake_binary(
        tmp_path,
        "fakecli_help2",
        f'printf x >> {counter_file}\necho "usage: fakecli_help2 run [OPTIONS]"',
    )
    old_path = os.environ.get("PATH", "")
    os.environ["PATH"] = f"{bin_dir}:{old_path}"
    try:
        desc = CLAUDELOOP.__class__(
            engine_id=EngineId.CLAUDELOOP,
            binary="fakecli_help2",
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

        first = adapter.help_text
        second = adapter.help_text

        assert first == second
        assert counter_file.read_text() == "x"  # invoked exactly once
    finally:
        os.environ["PATH"] = old_path


def test_help_text_returns_none_on_subprocess_error(tmp_path: Path) -> None:
    import os
    from unittest.mock import patch

    bin_dir = _make_fake_binary(tmp_path, "fakecli_help3", 'echo "usage: fakecli_help3"')
    old_path = os.environ.get("PATH", "")
    os.environ["PATH"] = f"{bin_dir}:{old_path}"
    try:
        desc = CLAUDELOOP.__class__(
            engine_id=EngineId.CLAUDELOOP,
            binary="fakecli_help3",
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

        with patch("subprocess.run", side_effect=OSError("boom")):
            assert adapter.help_text is None
    finally:
        os.environ["PATH"] = old_path


async def test_tail_yields_translated_events(tmp_path: Path) -> None:
    adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
    run_dir = tmp_path / "test-run"
    run_dir.mkdir(parents=True)
    handle = _make_handle(run_dir)

    events_path = run_dir / "events.jsonl"
    events_path.write_text(
        '{"event_type":"run.started","at":"2026-01-01T00:00:00+00:00","payload":{}}\n'
        '{"event_type":"chatter.assistant","at":"2026-01-01T00:00:01+00:00","payload":{"text":"hi"}}\n'
    )

    meta_path = run_dir / "meta.json"
    meta_path.write_text('{"status":"finished"}')

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
        '{"event_type":"run.started","at":"2026-01-01T00:00:01+00:00","payload":{}}\n'
    )

    meta_path = run_dir / "meta.json"
    meta_path.write_text('{"status":"finished"}')

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
        '{"event_type":"run.started","at":"2026-01-01T00:00:00+00:00","payload":{}}\n'
    )

    meta_path = run_dir / "meta.json"
    meta_path.write_text('{"status":"finished"}')

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
        '{"event_type":"run.started","at":"2026-01-01T00:00:00+00:00","payload":{}}\n'
    )

    meta_path = run_dir / "meta.json"
    meta_path.write_text('{"status":"finished"}')

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
        '\n   \n{"event_type":"run.started","at":"2026-01-01T00:00:00+00:00","payload":{}}\n'
    )

    meta_path = run_dir / "meta.json"
    meta_path.write_text('{"status":"finished"}')

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
    events_path.write_text('{"kind":"run.started","at":"2026-01-01T00:00:00+00:00","payload":{}}\n')

    meta_path = run_dir / "meta.json"
    meta_path.write_text('{"status":"finished"}')

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
        '{"event_type":"run.started","timestamp":"2026-06-15T12:00:00+00:00","payload":{}}\n'
    )

    meta_path = run_dir / "meta.json"
    meta_path.write_text('{"status":"finished"}')

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
    events_path.write_text('{"event_type":"run.started","payload":{}}\n')

    meta_path = run_dir / "meta.json"
    meta_path.write_text('{"status":"finished"}')

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


async def test_communicate_reaps_an_already_exited_process_on_error() -> None:
    from unittest.mock import AsyncMock

    process = AsyncMock()
    process.communicate.side_effect = RuntimeError("communication failed")
    process.returncode = 1

    with pytest.raises(RuntimeError, match="communication failed"):
        await _communicate(process, timeout=1.0)

    process.kill.assert_not_called()
    process.wait.assert_awaited_once()


async def test_stop_reaps_an_exited_registered_process(tmp_path: Path) -> None:
    import asyncio
    from unittest.mock import MagicMock

    adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
    run_dir = tmp_path / "test-run"
    run_dir.mkdir(parents=True)
    (run_dir / "stop-summary.md").write_text("Stopped.")
    handle = _make_handle(run_dir)
    process = MagicMock()
    process.returncode = 0
    process.wait.return_value = asyncio.get_running_loop().create_future()
    process.wait.return_value.set_result(0)
    _active_processes[handle.run_id] = process

    await adapter.stop(handle)

    process.wait.assert_called_once_with()


async def test_stop_waits_for_a_running_registered_process(tmp_path: Path) -> None:
    import asyncio
    from unittest.mock import AsyncMock, MagicMock, patch

    adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
    run_dir = tmp_path / "test-run"
    run_dir.mkdir(parents=True)
    (run_dir / "stop-summary.md").write_text("Stopped.")
    handle = _make_handle(run_dir)
    process = MagicMock()
    process.returncode = None
    process.wait.return_value = asyncio.get_running_loop().create_future()
    process.wait.return_value.set_result(0)
    _active_processes[handle.run_id] = process

    with patch("asyncio.wait_for", new=AsyncMock(return_value=0)) as wait_for:
        await adapter.stop(handle)

    wait_for.assert_awaited_once()
    assert wait_for.await_args.kwargs == {"timeout": 2.0}
    process.wait.assert_called_once_with()
    process.terminate.assert_not_called()


@pytest.mark.parametrize("second_wait_fails", [False, True])
async def test_stop_terminates_a_process_that_does_not_exit(
    tmp_path: Path, second_wait_fails: bool
) -> None:
    import asyncio
    from unittest.mock import AsyncMock, MagicMock, patch

    adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
    run_dir = tmp_path / "test-run"
    run_dir.mkdir(parents=True)
    (run_dir / "stop-summary.md").write_text("Stopped.")
    handle = _make_handle(run_dir)
    process = MagicMock()
    process.returncode = None
    process.wait.return_value = asyncio.get_running_loop().create_future()
    process.wait.return_value.set_result(0)
    _active_processes[handle.run_id] = process
    side_effect = [TimeoutError("still running")]
    if second_wait_fails:
        side_effect.append(RuntimeError("terminate failed"))
    else:
        side_effect.append(0)

    with patch("asyncio.wait_for", new=AsyncMock(side_effect=side_effect)):
        await adapter.stop(handle)

    process.terminate.assert_called_once_with()


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
        '{"event_type":"run.started","at":"2026-01-01T00:00:00+00:00","payload":{}}\n'
    )

    meta_path = run_dir / "meta.json"

    async def _write_meta_after_delay() -> None:
        await asyncio.sleep(0.6)
        meta_path.write_text('{"status":"running"}')
        await asyncio.sleep(0.6)
        meta_path.write_text('{"status":"finished"}')

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
        '{"event_type":"run.started","at":"2026-01-01T00:00:00+00:00","payload":{}}\n'
    )

    meta_path = run_dir / "meta.json"
    meta_path.write_text("{invalid json for meta}")

    events: list[object] = []
    async for event in adapter.tail(handle):
        events.append(event)

    assert len(events) == 1


async def test_tail_gives_up_when_process_exits_without_terminal_status(
    tmp_path: Path,
) -> None:
    """Regression: a process that exits (crash, early validation failure)
    without ever writing a terminal meta.json status must not hang tail()
    forever -- confirmed real via codexloop's own plan parser raising
    before it ever touches meta.json's status field. Bounded by wait_for so
    a regression fails this test loudly instead of hanging the suite."""
    import asyncio
    from types import SimpleNamespace

    adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
    run_dir = tmp_path / "test-run"
    run_dir.mkdir(parents=True)
    handle = _make_handle(run_dir)

    events_path = run_dir / "events.jsonl"
    events_path.write_text("")
    # meta.json exists but never carries a terminal (or any) status field --
    # exactly what codexloop's own meta.json looks like today.
    (run_dir / "meta.json").write_text('{"run_id": "x", "pid": 1}')

    _active_processes[handle.run_id] = SimpleNamespace(returncode=0)  # type: ignore[assignment]
    try:
        events2: list[object] = []
        async with asyncio.timeout(5.0):
            async for event in adapter.tail(handle):
                events2.append(event)
        assert events2 == []
    finally:
        _active_processes.pop(handle.run_id, None)


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


async def test_tail_enriches_verdict_with_done_marker(tmp_path: Path) -> None:
    """VerdictRendered events get done_marker injected into payload when missing."""
    from vibey.infrastructure.engines.descriptors import AGYLOOP

    adapter = LoopProcessAdapter(descriptor=AGYLOOP)
    run_dir = tmp_path / "test-run"
    run_dir.mkdir(parents=True)
    handle = _make_handle(run_dir)

    events_path = run_dir / "events.jsonl"
    # agyloop's "finished" event maps to VerdictRendered but doesn't have done_marker in payload
    events_path.write_text(
        '{"event_type":"finished","ts":"2026-01-01T00:00:00+00:00","payload":{"success":true,"reason":"Done"}}\n'
    )

    meta_path = run_dir / "meta.json"
    meta_path.write_text('{"status":"finished"}')

    events = []
    async for event in adapter.tail(handle):
        events.append(event)

    assert len(events) == 1
    assert events[0].kind == "VerdictRendered"
    # The adapter should inject the done_marker from the descriptor
    assert events[0].payload.get("done_marker") == "AGYLOOP_TASK_FULLY_COMPLETE"


async def test_tail_does_not_enrich_failed_verdict_with_done_marker(tmp_path: Path) -> None:
    """agyloop's "finished" event_type covers both success and failure,
    distinguished only by payload["success"] -- a failed run must never get
    a done_marker injected, or conformance/production code would read a
    failed run as having completed successfully."""
    from vibey.infrastructure.engines.descriptors import AGYLOOP

    adapter = LoopProcessAdapter(descriptor=AGYLOOP)
    run_dir = tmp_path / "test-run"
    run_dir.mkdir(parents=True)
    handle = _make_handle(run_dir)

    events_path = run_dir / "events.jsonl"
    events_path.write_text(
        '{"event_type":"finished","ts":"2026-01-01T00:00:00+00:00",'
        '"payload":{"success":false,"reason":"budget exhausted"}}\n'
    )

    meta_path = run_dir / "meta.json"
    meta_path.write_text('{"status":"failed"}')

    events = []
    async for event in adapter.tail(handle):
        events.append(event)

    assert len(events) == 1
    assert events[0].kind == "VerdictRendered"
    assert "done_marker" not in events[0].payload


async def test_tail_does_not_enrich_verdict_missing_success_key(tmp_path: Path) -> None:
    """A VerdictRendered event whose payload has no "success" key at all
    (e.g. an engine like claudeloop, whose own structured-output schema uses
    "complete" instead) must not get a done_marker injected -- there is no
    positive confirmation of success to enrich from, and defaulting to True
    when the key is merely absent would incorrectly treat "we don't know"
    as "it succeeded"."""
    adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
    run_dir = tmp_path / "test-run"
    run_dir.mkdir(parents=True)
    handle = _make_handle(run_dir)

    events_path = run_dir / "events.jsonl"
    events_path.write_text(
        '{"event_type":"finished","at":"2026-01-01T00:00:00+00:00",'
        '"payload":{"complete":false,"summary":"still working"}}\n'
    )

    meta_path = run_dir / "meta.json"
    meta_path.write_text('{"status":"finished"}')

    events = []
    async for event in adapter.tail(handle):
        events.append(event)

    assert len(events) == 1
    assert events[0].kind == "VerdictRendered"
    assert "done_marker" not in events[0].payload


async def test_tail_preserves_existing_done_marker(tmp_path: Path) -> None:
    """If an event already has done_marker in payload, don't overwrite it."""
    adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
    run_dir = tmp_path / "test-run"
    run_dir.mkdir(parents=True)
    handle = _make_handle(run_dir)

    events_path = run_dir / "events.jsonl"
    events_path.write_text(
        '{"event_type":"finished","at":"2026-01-01T00:00:00+00:00",'
        '"payload":{"done_marker":"CUSTOM_MARKER"}}\n'
    )

    meta_path = run_dir / "meta.json"
    meta_path.write_text('{"status":"finished"}')

    events = []
    async for event in adapter.tail(handle):
        events.append(event)

    assert len(events) == 1
    assert events[0].kind == "VerdictRendered"
    # Should preserve the existing done_marker, not overwrite with descriptor's
    assert events[0].payload.get("done_marker") == "CUSTOM_MARKER"


async def test_run_exit_code_reads_the_live_process_registry(tmp_path: Path) -> None:
    from types import SimpleNamespace

    adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
    run_dir = tmp_path / "test-run"
    run_dir.mkdir(parents=True)
    handle = _make_handle(run_dir)

    # No registered process (never started, or stop() already released it).
    assert adapter.run_exit_code(handle) is None

    _active_processes[handle.run_id] = SimpleNamespace(returncode=None)  # type: ignore[assignment]
    try:
        assert adapter.run_exit_code(handle) is None  # still running
        _active_processes[handle.run_id] = SimpleNamespace(returncode=75)  # type: ignore[assignment]
        assert adapter.run_exit_code(handle) == 75
    finally:
        _active_processes.pop(handle.run_id, None)


async def test_tail_normalizes_vendor_success_into_vibey_complete(tmp_path: Path) -> None:
    """claudeloop/agyloop verdicts say {"success": bool}; every vibey
    consumer reads {"complete": bool}. Caught live: a real claudeloop run
    finished its item, rendered success=true, and the implement handler
    still failed it as "did not report completion"."""
    adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
    run_dir = tmp_path / "test-run"
    run_dir.mkdir(parents=True)
    handle = _make_handle(run_dir)

    (run_dir / "events.jsonl").write_text(
        '{"event_type":"finished","ts":"2026-01-01T00:00:00+00:00",'
        '"payload":{"success":true,"reason":"Done"}}\n'
        '{"event_type":"finished","ts":"2026-01-01T00:00:01+00:00",'
        '"payload":{"success":false,"reason":"Nope"}}\n'
    )
    (run_dir / "meta.json").write_text('{"status":"finished"}')

    events = [event async for event in adapter.tail(handle)]

    assert [e.payload.get("complete") for e in events] == [True, False]


async def test_tail_never_overwrites_an_explicit_complete_key(tmp_path: Path) -> None:
    adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
    run_dir = tmp_path / "test-run"
    run_dir.mkdir(parents=True)
    handle = _make_handle(run_dir)

    (run_dir / "events.jsonl").write_text(
        '{"event_type":"finished","ts":"2026-01-01T00:00:00+00:00",'
        '"payload":{"complete":false,"success":true}}\n'
        '{"event_type":"finished","ts":"2026-01-01T00:00:01+00:00",'
        '"payload":{"reason":"no completion field at all"}}\n'
    )
    (run_dir / "meta.json").write_text('{"status":"finished"}')

    events = [event async for event in adapter.tail(handle)]

    assert events[0].payload["complete"] is False
    assert "complete" not in events[1].payload


def test_isolate_python_env_strips_the_orchestrator_venv() -> None:
    """Engine sessions inheriting vibey's env pip-installed INTO vibey's
    own venv, twice, live -- shadowing modules for every later gate run."""
    from vibey.infrastructure.engines.loop_process_adapter import isolate_python_env

    env = {
        "VIRTUAL_ENV": "/repo/.venv",
        "VIRTUAL_ENV_PROMPT": "vibey",
        "PYTHONPATH": "/repo/src",
        "PYTHONHOME": "/somewhere",
        "PATH": "/repo/.venv/bin:/usr/local/bin:/repo/.venv:/usr/bin",
        "HOME": "/Users/dev",
        "ANTHROPIC_API_KEY": "sk-test",
    }

    isolated = isolate_python_env(env, venv_prefixes=("/repo/.venv", None))

    for stripped in ("VIRTUAL_ENV", "VIRTUAL_ENV_PROMPT", "PYTHONPATH", "PYTHONHOME"):
        assert stripped not in isolated
    assert isolated["PATH"] == "/usr/local/bin:/usr/bin"
    # Everything the engine actually needs passes through untouched.
    assert isolated["HOME"] == "/Users/dev"
    assert isolated["ANTHROPIC_API_KEY"] == "sk-test"
    # The input mapping is never mutated.
    assert env["VIRTUAL_ENV"] == "/repo/.venv"


def test_isolate_python_env_handles_missing_path_and_no_prefixes() -> None:
    from vibey.infrastructure.engines.loop_process_adapter import isolate_python_env

    no_path = isolate_python_env({"VIRTUAL_ENV": "/v"}, venv_prefixes=("/v",))
    assert "PATH" not in no_path

    no_prefixes = isolate_python_env({"PATH": "/v/bin:/usr/bin"}, venv_prefixes=(None,))
    assert no_prefixes["PATH"] == "/v/bin:/usr/bin"

    # A PATH entry that merely shares the prefix STRING is not under the
    # venv directory and must survive.
    lookalike = isolate_python_env(
        {"PATH": "/repo/.venv-tools/bin:/repo/.venv/bin"}, venv_prefixes=("/repo/.venv",)
    )
    assert lookalike["PATH"] == "/repo/.venv-tools/bin"


async def test_start_spawns_the_engine_with_an_isolated_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from unittest.mock import AsyncMock

    from vibey.application.dto import RunSpec
    from vibey.domain.effort import Effort
    from vibey.domain.engine import IsolationLevel
    from vibey.infrastructure.engines import loop_process_adapter as module

    captured: dict[str, object] = {}

    async def fake_exec(*argv, **kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        process = AsyncMock()
        process.pid = 4242
        process.returncode = None
        return process

    monkeypatch.setattr(module.asyncio, "create_subprocess_exec", fake_exec)
    monkeypatch.setenv("VIRTUAL_ENV", "/orchestrator/.venv")

    adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
    spec = RunSpec(
        run_id=uuid4(),
        worktree_path=tmp_path,
        prompt="do the thing",
        effort=Effort.LOW,
        isolation=IsolationLevel.WORKTREE,
    )
    handle = await adapter.start(spec)
    _active_processes.pop(handle.run_id, None)

    env = captured["env"]
    assert isinstance(env, dict)
    assert "VIRTUAL_ENV" not in env
    assert "/orchestrator/.venv" not in env.get("PATH", "")


async def test_tail_reads_codexloop_flat_events_keyed_by_type(tmp_path: Path) -> None:
    """codexloop passes the wrapped codex CLI's stream through nearly
    verbatim: the key is "type", not "event_type", and fields sit at the
    top level with no payload envelope. Accepting only event_type/kind
    dropped every codexloop event as "event_missing_type", which made its
    whole LOOP_EVENT_MAP entry unreachable."""
    adapter = LoopProcessAdapter(descriptor=CODEXLOOP)
    run_dir = tmp_path / "cx-run"
    run_dir.mkdir(parents=True)
    handle = _make_handle(run_dir)

    (run_dir / "events.jsonl").write_text(
        '{"type":"thread.started","thread_id":"t-1"}\n'
        '{"type":"run.verdict","success":true,"complete":true,'
        '"done_marker":"CODEXLOOP_TASK_FULLY_COMPLETE"}\n'
    )
    (run_dir / "meta.json").write_text('{"status":"finished"}')

    events = [event async for event in adapter.tail(handle)]

    assert [e.kind for e in events] == ["SessionSeeded", "VerdictRendered"]
    # A flat event is its own payload: dropping the non-"payload" fields
    # would discard exactly what every consumer downstream reads.
    assert events[0].payload["thread_id"] == "t-1"
    assert events[1].payload["done_marker"] == "CODEXLOOP_TASK_FULLY_COMPLETE"
    assert events[1].payload["complete"] is True
