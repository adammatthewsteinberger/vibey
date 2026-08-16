import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest

from vibey.application.dto import RunSpec
from vibey.application.worker import CapacityDeferred
from vibey.domain.effort import Effort
from vibey.domain.engine import IsolationLevel
from vibey.infrastructure.engines.claudeloop_process import (
    AsyncSubprocessExecutor,
    ClaudeLoopProcess,
    CommandResult,
)


class FakeExecutor:
    def __init__(self, result: CommandResult) -> None:
        self.result = result
        self.calls: list[tuple[str, ...]] = []

    async def execute(self, argv: tuple[str, ...]) -> CommandResult:
        self.calls.append(argv)
        return self.result


class CancellingSubprocess:
    returncode = None

    def __init__(self) -> None:
        self.terminated = False
        self.waited = False

    async def communicate(self):  # type: ignore[no-untyped-def]
        raise asyncio.CancelledError

    def terminate(self) -> None:
        self.terminated = True

    async def wait(self) -> None:
        self.waited = True


def spec(tmp_path: Path) -> RunSpec:
    return RunSpec(
        run_id=UUID("00000000-0000-0000-0000-000000000123"),
        worktree_path=tmp_path,
        prompt="# Bounded DESIGN research\n",
        effort=Effort.STANDARD,
        isolation=IsolationLevel.WORKTREE,
    )


async def test_cancelling_executor_terminates_and_reaps_its_child(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    child = CancellingSubprocess()

    async def fake_create(*args, **kwargs):  # type: ignore[no-untyped-def]
        return child

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create)
    with pytest.raises(asyncio.CancelledError):
        await AsyncSubprocessExecutor().execute(("claudeloop", "run"))
    assert child.terminated
    assert child.waited


async def test_run_materializes_plan_enforces_caps_and_reads_latest_response(
    tmp_path: Path,
) -> None:
    run_id = "20260814T120000Z-abcd1234"
    events = tmp_path / ".claudeloop" / "runs" / run_id / "events.jsonl"
    events.parent.mkdir(parents=True)
    events.write_text(
        "not-json\n"
        + json.dumps({"event_type": "chatter.assistant", "payload": {"text": "first"}})
        + "\n"
        + json.dumps({"event_type": "chatter.assistant", "payload": {"text": "final"}})
        + "\n"
    )
    executor = FakeExecutor(CommandResult(0, "", f"Run id: {run_id}\nTrace id: trace-1\n"))
    process = ClaudeLoopProcess(executor=executor, max_turns=1, max_dollars=0.25)

    result = await process.run(spec(tmp_path), web_search=True)

    plan = tmp_path / ".vibey" / "plans" / "00000000-0000-0000-0000-000000000123.md"
    assert plan.read_text() == "# Bounded DESIGN research\n"
    assert executor.calls == [
        (
            "claudeloop",
            "run",
            str(plan),
            "--preset",
            "medium",
            "--effort",
            "high",
            "--cwd",
            str(tmp_path),
            "--max-turns",
            "1",
            "--max-dollars",
            "0.25",
            "--no-auto-model",
            "--max-wait",
            "1",
            "--web-search",
        )
    ]
    assert result.run_id == run_id
    assert result.response == "final"
    assert result.run_dir == events.parent


async def test_result_message_is_a_fallback_when_chatter_is_absent(tmp_path: Path) -> None:
    run_id = "20260814T120000Z-abcd1234"
    events = tmp_path / ".claudeloop" / "runs" / run_id / "events.jsonl"
    events.parent.mkdir(parents=True)
    events.write_text(
        json.dumps(
            {
                "event_type": "sdk.message",
                "payload": {"type": "ResultMessage", "result": "fallback"},
            }
        )
    )
    process = ClaudeLoopProcess(
        executor=FakeExecutor(CommandResult(0, "", f"Run id: {run_id}\n")),
        max_turns=1,
        max_dollars=0.1,
    )
    assert (await process.run(spec(tmp_path))).response == "fallback"


async def test_valid_structured_chatter_survives_turn_exhaustion_exit(tmp_path: Path) -> None:
    run_id = "20260814T120000Z-abcd1234"
    events = tmp_path / ".claudeloop" / "runs" / run_id / "events.jsonl"
    events.parent.mkdir(parents=True)
    response = '```json\n{"questions": []}\n```'
    events.write_text(
        json.dumps({"event_type": "chatter.assistant", "payload": {"text": response}})
    )
    process = ClaudeLoopProcess(
        executor=FakeExecutor(
            CommandResult(1, "", f"Run id: {run_id}\nReached maximum number of turns (1)")
        ),
        max_turns=1,
        max_dollars=0.25,
    )

    result = await process.run(spec(tmp_path))

    assert result.response == response
    assert result.run_dir == events.parent


async def test_identical_prompt_reuses_completed_run_without_another_paid_call(
    tmp_path: Path,
) -> None:
    previous_plan = tmp_path / ".vibey" / "plans" / "previous.md"
    previous_plan.parent.mkdir(parents=True)
    previous_plan.write_text("# Bounded DESIGN research\n")
    run_dir = tmp_path / ".claudeloop" / "runs" / "20260814T120000Z-abcd1234"
    run_dir.mkdir(parents=True)
    (run_dir / "meta.json").write_text(json.dumps({"plan_path": str(previous_plan)}))
    (run_dir / "events.jsonl").write_text(
        json.dumps({"event_type": "chatter.assistant", "payload": {"text": '{"recovered":true}'}})
    )
    executor = FakeExecutor(CommandResult(0, "", "should not run"))
    process = ClaudeLoopProcess(executor=executor, max_turns=1, max_dollars=0.1)

    result = await process.run(spec(tmp_path))

    assert result.response == '{"recovered":true}'
    assert result.run_dir == run_dir
    assert executor.calls == []


async def test_identical_prompt_reuses_fenced_json_after_leading_prose(tmp_path: Path) -> None:
    previous_plan = tmp_path / ".vibey" / "plans" / "previous.md"
    previous_plan.parent.mkdir(parents=True)
    previous_plan.write_text("# Bounded DESIGN research\n")
    run_dir = tmp_path / ".claudeloop" / "runs" / "20260814T120000Z-abcd1234"
    run_dir.mkdir(parents=True)
    (run_dir / "meta.json").write_text(json.dumps({"plan_path": str(previous_plan)}))
    response = 'Research result:\n```json\n{"recovered":true}\n```'
    (run_dir / "events.jsonl").write_text(
        json.dumps({"event_type": "chatter.assistant", "payload": {"text": response}})
    )
    executor = FakeExecutor(CommandResult(0, "", "should not run"))
    process = ClaudeLoopProcess(executor=executor, max_turns=1, max_dollars=0.1)

    assert (await process.run(spec(tmp_path))).response == response
    assert executor.calls == []


async def test_unstructured_incomplete_response_is_not_reused(tmp_path: Path) -> None:
    previous_plan = tmp_path / ".vibey" / "plans" / "previous.md"
    previous_plan.parent.mkdir(parents=True)
    previous_plan.write_text("# Bounded DESIGN research\n")
    old_run = tmp_path / ".claudeloop" / "runs" / "20260814T120000Z-abcd1234"
    old_run.mkdir(parents=True)
    (old_run / "meta.json").write_text(json.dumps({"plan_path": str(previous_plan)}))
    (old_run / "events.jsonl").write_text(
        json.dumps({"event_type": "chatter.assistant", "payload": {"text": "I'll examine this."}})
    )
    new_run = tmp_path / ".claudeloop" / "runs" / "20260814T130000Z-abcd1234"
    new_run.mkdir()
    (new_run / "events.jsonl").write_text(
        json.dumps({"event_type": "chatter.assistant", "payload": {"text": "{}"}})
    )
    executor = FakeExecutor(CommandResult(0, "", "Run id: 20260814T130000Z-abcd1234\n"))
    process = ClaudeLoopProcess(executor=executor, max_turns=1, max_dollars=0.1)

    assert (await process.run(spec(tmp_path))).response == "{}"
    assert len(executor.calls) == 1


async def test_rate_limit_event_becomes_reset_aware_capacity_defer(tmp_path: Path) -> None:
    run_id = "20260814T130000Z-abcd1234"
    run_dir = tmp_path / ".claudeloop" / "runs" / run_id
    run_dir.mkdir(parents=True)
    (run_dir / "events.jsonl").write_text(
        json.dumps(
            {
                "event_type": "sdk.message",
                "payload": {
                    "type": "RateLimitEvent",
                    "status": "rejected",
                    "rate_limit_type": "five_hour",
                    "resets_at": 1786738200,
                },
            }
        )
    )
    process = ClaudeLoopProcess(
        executor=FakeExecutor(CommandResult(1, "", f"Run id: {run_id}\nnoisy stderr")),
        max_turns=1,
        max_dollars=0.1,
    )

    with pytest.raises(CapacityDeferred) as raised:
        await process.run(spec(tmp_path))

    assert raised.value.retry_at == datetime(2026, 8, 14, 20, 10, tzinfo=UTC)
    assert raised.value.detail == (
        "claudeloop five_hour capacity exhausted until 2026-08-14T20:10:00+00:00"
    )


@pytest.mark.parametrize(
    ("result", "message"),
    [
        (CommandResult(2, "", "bad plan"), "bad plan"),
        (CommandResult(0, "", "no identifier"), "did not report a run id"),
    ],
)
async def test_run_rejects_failed_or_unidentifiable_processes(
    tmp_path: Path, result: CommandResult, message: str
) -> None:
    process = ClaudeLoopProcess(executor=FakeExecutor(result), max_turns=1, max_dollars=0.1)
    with pytest.raises(RuntimeError, match=message):
        await process.run(spec(tmp_path))


@pytest.mark.parametrize(("turns", "dollars"), [(0, 0.1), (1, 0.0), (1, 10.01)])
def test_constructor_rejects_missing_or_excessive_safety_caps(turns: int, dollars: float) -> None:
    with pytest.raises(ValueError, match="cap"):
        ClaudeLoopProcess(
            executor=FakeExecutor(CommandResult(0, "", "")),
            max_turns=turns,
            max_dollars=dollars,
        )
