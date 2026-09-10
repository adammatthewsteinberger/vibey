# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Exhaustive in-process system-live matrix: real adapters + scripted agent."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from claudeloop.bootstrap_ops import unwind_savepoint
from claudeloop.domain.budget import Budget
from claudeloop.domain.classify import TurnSignals
from claudeloop.domain.completion import StructuredVerdict
from claudeloop.domain.control import (
    PromptDeferredCommand,
    PromptNowCommand,
    ResourceMutateCommand,
    SetPermissionModeCommand,
    StopCommand,
)
from claudeloop.domain.waiting import WaitPolicyConfig
from claudeloop.infrastructure.agent.options import DEFAULT_MAX_BUFFER_SIZE, build_turn_options
from claudeloop.infrastructure.lock import FileSessionLock
from claudeloop.infrastructure.redact import REDACTED_VALUE
from tests.application.fakes import (
    CONTINUE_VERDICT,
    DONE_VERDICT,
    FakeClock,
    FakeSleeper,
    ScriptedTurn,
    available_signals,
    credits_exhausted_signals,
    window_exhausted_signals,
)
from tests.live.system.conftest import SystemHarness, build_system_harness

pytestmark = pytest.mark.system

NOW = datetime(2026, 8, 12, 15, 0, tzinfo=timezone.utc)


class _StopEnqueueingSleeper:
    """On first sleep, enqueue stop into the real FileRunControl inbox."""

    def __init__(self, inner: FakeSleeper, holder: dict[str, SystemHarness]) -> None:
        self._inner = inner
        self._holder = holder
        self._fired = False

    async def sleep_until(self, instant: datetime) -> None:
        if not self._fired:
            self._fired = True
            self._holder["h"].control.enqueue(StopCommand())
        await self._inner.sleep_until(instant)


@pytest.mark.asyncio
async def test_happy_complete_one_turn(git_sandbox: Path) -> None:
    h = build_system_harness(
        git_sandbox,
        turns=[ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT)],
        probes=[available_signals()],
    )
    result = await h.runner.run(initial_prompt="do it", continue_prompt="continue")
    assert result.success is True
    assert result.reason == "all done"
    assert (h.run_dir.root / "status.json").is_file()
    assert (h.run_dir.root / "bus.jsonl").is_file()
    assert "finished" in (h.run_dir.root / "audit.jsonl").read_text(encoding="utf-8")
    points = h.runner._save_points.list_points(h.run_id)  # noqa: SLF001
    assert len(points) >= 1
    assert (h.run_dir.snapshots_root / "latest.json").is_file()
    bus = (h.run_dir.root / "bus.jsonl").read_text(encoding="utf-8")
    assert "snapshot.written" in bus or "snapshot.latest" in bus
    meta = h.run_dir.read_meta()
    assert meta.session_id is not None or meta.model is not None


@pytest.mark.asyncio
async def test_happy_multi_turn_continue_then_done(git_sandbox: Path) -> None:
    h = build_system_harness(
        git_sandbox,
        turns=[
            ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT),
            ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT),
        ],
        probes=[available_signals()],
    )
    result = await h.runner.run(initial_prompt="start", continue_prompt="continue")
    assert result.success is True
    assert h.gateway.sent_prompts == ["start", "continue"]


@pytest.mark.asyncio
async def test_prompt_now_replaces_continue(git_sandbox: Path) -> None:
    h = build_system_harness(
        git_sandbox,
        turns=[
            ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT),
            ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT),
        ],
        probes=[available_signals()],
    )
    original = h.gateway.send_turn

    async def _send(prompt_text: str):
        outcome = await original(prompt_text)
        if len(h.gateway.sent_prompts) == 1:
            h.control.enqueue(PromptNowCommand(text="injected-now"))
        return outcome

    h.gateway.send_turn = _send  # type: ignore[method-assign]
    result = await h.runner.run(initial_prompt="start", continue_prompt="continue")
    assert result.success is True
    assert h.gateway.sent_prompts[1] == "injected-now"


@pytest.mark.asyncio
async def test_prompt_at_break_deferred(git_sandbox: Path) -> None:
    h = build_system_harness(
        git_sandbox,
        turns=[
            ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT),
            ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT),
        ],
        probes=[available_signals()],
    )
    original = h.gateway.send_turn

    async def _send(prompt_text: str):
        outcome = await original(prompt_text)
        if len(h.gateway.sent_prompts) == 1:
            h.control.enqueue(PromptDeferredCommand(text="at-break"))
        return outcome

    h.gateway.send_turn = _send  # type: ignore[method-assign]
    result = await h.runner.run(initial_prompt="start", continue_prompt="continue")
    assert result.success is True
    assert h.gateway.sent_prompts[1] == "at-break"


@pytest.mark.asyncio
async def test_stop_writes_summary(git_sandbox: Path) -> None:
    h = build_system_harness(
        git_sandbox,
        turns=[
            ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT),
            ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT),
        ],
        probes=[available_signals()],
    )
    h.control.enqueue(StopCommand())
    result = await h.runner.run(initial_prompt="start", continue_prompt="continue")
    assert result.success is False
    assert "stopped" in result.reason
    summary = h.run_dir.stop_summary_path
    assert summary.is_file()
    text = summary.read_text(encoding="utf-8")
    assert h.run_id in text
    assert h.run_dir.read_meta().status == "stopped"


@pytest.mark.asyncio
async def test_stop_during_wait_interrupts(git_sandbox: Path) -> None:
    holder: dict[str, SystemHarness] = {}
    clock = FakeClock(start=NOW)
    inner = FakeSleeper(clock)
    sleeper = _StopEnqueueingSleeper(inner, holder)
    resets = NOW + timedelta(hours=2)
    h = build_system_harness(
        git_sandbox,
        turns=[
            ScriptedTurn(
                signals=window_exhausted_signals(resets_at=resets),
                verdict=CONTINUE_VERDICT,
            )
        ],
        probes=[available_signals()],
        clock=clock,
        sleeper=sleeper,  # type: ignore[arg-type]
    )
    holder["h"] = h
    result = await h.runner.run(initial_prompt="start", continue_prompt="continue")
    assert result.success is False
    assert "stopped" in result.reason
    assert h.run_dir.stop_summary_path.is_file()


@pytest.mark.asyncio
async def test_unwind_refused_while_active(git_sandbox: Path) -> None:
    h = build_system_harness(
        git_sandbox,
        turns=[ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT)],
        probes=[available_signals()],
    )
    assert h.run_dir.read_meta().status == "active"
    point = h.runner._save_points.create(  # noqa: SLF001
        run_id=h.run_id, label="manual", message="manual"
    )
    assert point is not None
    with pytest.raises(RuntimeError, match="still active"):
        unwind_savepoint(git_sandbox, "1", backup=True, run_id=h.run_id)


@pytest.mark.asyncio
async def test_unwind_after_finish_with_backup(git_sandbox: Path) -> None:
    h = build_system_harness(
        git_sandbox,
        turns=[
            ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT),
            ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT),
        ],
        probes=[available_signals()],
    )
    (git_sandbox / "a.txt").write_text("one\n", encoding="utf-8")
    result = await h.runner.run(initial_prompt="start", continue_prompt="continue")
    assert result.success is True
    (git_sandbox / "a.txt").write_text("two\n", encoding="utf-8")
    h.runner._save_points.create(run_id=h.run_id, label="extra", message="extra")  # noqa: SLF001
    out = unwind_savepoint(git_sandbox, "1", backup=True, run_id=h.run_id)
    assert out["to_n"] == 1
    assert out["backup_ref"]


@pytest.mark.asyncio
async def test_stop_outranks_prompts_via_file_control(git_sandbox: Path) -> None:
    h = build_system_harness(
        git_sandbox,
        turns=[
            ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT),
            ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT),
        ],
        probes=[available_signals()],
    )
    h.control.enqueue(PromptNowCommand(text="should-not-apply"))
    h.control.enqueue(StopCommand())
    result = await h.runner.run(initial_prompt="start", continue_prompt="continue")
    assert result.success is False
    assert "stopped" in result.reason


@pytest.mark.asyncio
async def test_budget_turns_exhausted(git_sandbox: Path) -> None:
    h = build_system_harness(
        git_sandbox,
        turns=[
            ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT),
            ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT),
        ],
        probes=[available_signals()],
        budget=Budget(max_turns=1),
    )
    result = await h.runner.run(initial_prompt="start", continue_prompt="continue")
    assert result.success is False
    assert "budget" in result.reason.lower() or "turn" in result.reason.lower()


@pytest.mark.asyncio
async def test_dollar_budget(git_sandbox: Path) -> None:
    h = build_system_harness(
        git_sandbox,
        turns=[
            ScriptedTurn(
                signals=available_signals(),
                verdict=CONTINUE_VERDICT,
                cost_usd=1.0,
            )
        ],
        probes=[available_signals()],
        budget=Budget(max_dollars=0.5),
    )
    result = await h.runner.run(initial_prompt="start", continue_prompt="continue")
    assert result.success is False


@pytest.mark.asyncio
async def test_auth_failure_terminal(git_sandbox: Path) -> None:
    h = build_system_harness(
        git_sandbox,
        turns=[
            ScriptedTurn(
                signals=TurnSignals(assistant_error="authentication_failed"),
                verdict=DONE_VERDICT,
            )
        ],
        probes=[available_signals()],
    )
    result = await h.runner.run(initial_prompt="start", continue_prompt="continue")
    assert result.success is False
    assert "auth" in result.reason.lower()


@pytest.mark.asyncio
async def test_credits_vs_window(git_sandbox: Path) -> None:
    h = build_system_harness(
        git_sandbox,
        turns=[
            ScriptedTurn(signals=credits_exhausted_signals(), verdict=CONTINUE_VERDICT),
            ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT),
        ],
        probes=[
            available_signals(),
            available_signals(),
        ],
        wait_policy=WaitPolicyConfig(
            credits_probe_interval=timedelta(seconds=1),
            credits_probe_ceiling=timedelta(seconds=10),
        ),
    )
    result = await h.runner.run(initial_prompt="start", continue_prompt="continue")
    assert result.success is True


@pytest.mark.asyncio
async def test_capacity_outranks_done(git_sandbox: Path) -> None:
    resets = NOW + timedelta(minutes=30)
    holder: dict[str, SystemHarness] = {}
    clock = FakeClock(start=NOW)
    inner = FakeSleeper(clock)
    sleeper = _StopEnqueueingSleeper(inner, holder)
    h = build_system_harness(
        git_sandbox,
        turns=[
            ScriptedTurn(
                signals=window_exhausted_signals(resets_at=resets),
                verdict=DONE_VERDICT,
            )
        ],
        probes=[available_signals()],
        clock=clock,
        sleeper=sleeper,  # type: ignore[arg-type]
    )
    holder["h"] = h
    result = await h.runner.run(initial_prompt="start", continue_prompt="continue")
    assert result.success is False


@pytest.mark.asyncio
async def test_events_redact_secrets(git_sandbox: Path) -> None:
    h = build_system_harness(
        git_sandbox,
        turns=[
            ScriptedTurn(
                signals=available_signals(),
                verdict=DONE_VERDICT,
                raw_events=({"api_key": "sk-ant-abcdefghijklmnopqrstuvwxyz012345", "ok": True},),
            )
        ],
        probes=[available_signals()],
    )
    await h.runner.run(initial_prompt="start", continue_prompt="continue")
    events = h.run_dir.events_path.read_text(encoding="utf-8")
    assert "sk-ant-abcdefghijklmnopqrstuvwxyz012345" not in events
    assert REDACTED_VALUE in events


@pytest.mark.asyncio
async def test_session_lock_contention(git_sandbox: Path) -> None:
    lock = FileSessionLock(git_sandbox / ".claudeloop" / "locks")
    assert lock.acquire("sess-a") is True
    assert lock.acquire("sess-a") is False
    lock.release("sess-a")
    assert lock.acquire("sess-a") is True
    lock.release("sess-a")


def test_max_buffer_size_default_and_override() -> None:
    opts = build_turn_options(cwd="/tmp")
    assert opts.max_buffer_size == DEFAULT_MAX_BUFFER_SIZE
    opts2 = build_turn_options(cwd="/tmp", max_buffer_size=2_000_000)
    assert opts2.max_buffer_size == 2_000_000


@pytest.mark.asyncio
async def test_blocked_verdict(git_sandbox: Path) -> None:
    h = build_system_harness(
        git_sandbox,
        turns=[
            ScriptedTurn(
                signals=available_signals(),
                verdict=StructuredVerdict(complete=False, blocked_on="need MCP creds"),
            )
        ],
        probes=[available_signals()],
    )
    result = await h.runner.run(initial_prompt="start", continue_prompt="continue")
    assert result.success is False
    assert "MCP" in result.reason or "need" in result.reason


@pytest.mark.asyncio
async def test_resource_inbox_attach_and_skill(git_sandbox: Path) -> None:
    """Mid-run ResourceMutateCommand hits real RunResourceStore + gateway flush."""
    note = git_sandbox / "brief.txt"
    note.write_text("attach me\n", encoding="utf-8")
    h = build_system_harness(
        git_sandbox,
        turns=[
            ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT),
            ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT),
        ],
        probes=[available_signals()],
    )
    h.control.enqueue(ResourceMutateCommand(action="add", kind="attachment", value=str(note)))
    h.control.enqueue(ResourceMutateCommand(action="add", kind="skill", value="demo-skill"))
    h.control.enqueue(SetPermissionModeCommand(mode="plan"))
    result = await h.runner.run(initial_prompt="start", continue_prompt="continue")
    assert result.success is True
    snap = h.resources.store.snapshot()
    assert "brief.txt" in snap.attachments
    assert "demo-skill" in snap.skills
    assert "plan" in h.gateway.permission_modes
    assert h.gateway.resource_updates
