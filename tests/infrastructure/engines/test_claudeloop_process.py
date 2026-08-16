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


# --- AsyncSubprocessExecutor normal path ------------------------------------


async def test_async_subprocess_executor_normal_path(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    class FakeProc:
        returncode = 0

        async def communicate(self) -> tuple[bytes, bytes]:
            return b"output\n", b"err\n"

    async def fake_create(*args, **kwargs):  # type: ignore[no-untyped-def]
        return FakeProc()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create)
    result = await AsyncSubprocessExecutor().execute(("echo", "hi"))
    assert result.returncode == 0
    assert result.stdout == "output\n"
    assert result.stderr == "err\n"


# --- _capacity_deferred edge cases ------------------------------------------


async def test_capacity_deferred_returns_none_without_run_id(tmp_path: Path) -> None:
    process = ClaudeLoopProcess(
        executor=FakeExecutor(CommandResult(1, "", "no run id here\n")),
        max_turns=1,
        max_dollars=0.1,
    )
    with pytest.raises(RuntimeError, match="no run id here"):
        await process.run(spec(tmp_path))


async def test_capacity_deferred_returns_none_when_events_file_missing(tmp_path: Path) -> None:
    run_id = "20260814T120000Z-abcd1234"
    process = ClaudeLoopProcess(
        executor=FakeExecutor(CommandResult(1, "", f"Run id: {run_id}\nfailed")),
        max_turns=1,
        max_dollars=0.1,
    )
    with pytest.raises(RuntimeError, match="failed"):
        await process.run(spec(tmp_path))


async def test_capacity_deferred_skips_non_rate_limit_events(tmp_path: Path) -> None:
    run_id = "20260814T120000Z-abcd1234"
    run_dir = tmp_path / ".claudeloop" / "runs" / run_id
    run_dir.mkdir(parents=True)
    (run_dir / "events.jsonl").write_text(
        json.dumps({"event_type": "sdk.message", "payload": {"type": "Other"}})
        + "\n"
        + "not-json-line\n"
    )
    process = ClaudeLoopProcess(
        executor=FakeExecutor(CommandResult(1, "", f"Run id: {run_id}\nerror")),
        max_turns=1,
        max_dollars=0.1,
    )
    with pytest.raises(RuntimeError, match="error"):
        await process.run(spec(tmp_path))


async def test_capacity_deferred_skips_non_rejected_rate_limit(tmp_path: Path) -> None:
    run_id = "20260814T120000Z-abcd1234"
    run_dir = tmp_path / ".claudeloop" / "runs" / run_id
    run_dir.mkdir(parents=True)
    (run_dir / "events.jsonl").write_text(
        json.dumps(
            {
                "event_type": "sdk.message",
                "payload": {
                    "type": "RateLimitEvent",
                    "status": "accepted",
                    "resets_at": 1786738200,
                },
            }
        )
    )
    process = ClaudeLoopProcess(
        executor=FakeExecutor(CommandResult(1, "", f"Run id: {run_id}\nerror")),
        max_turns=1,
        max_dollars=0.1,
    )
    with pytest.raises(RuntimeError, match="error"):
        await process.run(spec(tmp_path))


# --- _last_response edge cases -----------------------------------------------


async def test_last_response_returns_empty_when_events_file_missing(tmp_path: Path) -> None:
    from vibey.infrastructure.engines.claudeloop_process import _last_response

    assert _last_response(tmp_path / "nonexistent.jsonl") == ""


async def test_last_response_skips_non_dict_payloads(tmp_path: Path) -> None:
    from vibey.infrastructure.engines.claudeloop_process import _last_response

    events_file = tmp_path / "events.jsonl"
    events_file.write_text(
        json.dumps({"event_type": "chatter.assistant", "payload": "string-not-dict"}) + "\n"
    )
    assert _last_response(events_file) == ""


async def test_last_response_returns_result_message(tmp_path: Path) -> None:
    from vibey.infrastructure.engines.claudeloop_process import _last_response

    events_file = tmp_path / "events.jsonl"
    events_file.write_text(
        json.dumps(
            {
                "event_type": "sdk.message",
                "payload": {"type": "ResultMessage", "result": "answer"},
            }
        )
    )
    assert _last_response(events_file) == "answer"


# --- _find_reusable_result edge cases ----------------------------------------


async def test_find_reusable_skips_non_dir_entries(tmp_path: Path) -> None:
    runs_root = tmp_path / ".claudeloop" / "runs"
    runs_root.mkdir(parents=True)
    (runs_root / "not-a-dir.txt").write_text("file not dir")
    executor = FakeExecutor(CommandResult(0, "", "Run id: new-run\n"))
    process = ClaudeLoopProcess(executor=executor, max_turns=1, max_dollars=0.1)
    new_run = tmp_path / ".claudeloop" / "runs" / "new-run"
    new_run.mkdir()
    (new_run / "events.jsonl").write_text(
        json.dumps({"event_type": "chatter.assistant", "payload": {"text": "{}"}})
    )
    await process.run(spec(tmp_path))
    assert len(executor.calls) == 1


async def test_find_reusable_skips_invalid_run_id_names(tmp_path: Path) -> None:
    runs_root = tmp_path / ".claudeloop" / "runs"
    runs_root.mkdir(parents=True)
    (runs_root / "!!!invalid").mkdir()
    executor = FakeExecutor(CommandResult(0, "", "Run id: new-run\n"))
    process = ClaudeLoopProcess(executor=executor, max_turns=1, max_dollars=0.1)
    new_run = runs_root / "new-run"
    new_run.mkdir()
    (new_run / "events.jsonl").write_text(
        json.dumps({"event_type": "chatter.assistant", "payload": {"text": "{}"}})
    )
    await process.run(spec(tmp_path))
    assert len(executor.calls) == 1


async def test_find_reusable_skips_missing_meta_json(tmp_path: Path) -> None:
    runs_root = tmp_path / ".claudeloop" / "runs"
    old_run = runs_root / "20260814T120000Z-abcd1234"
    old_run.mkdir(parents=True)
    (old_run / "events.jsonl").write_text(
        json.dumps({"event_type": "chatter.assistant", "payload": {"text": "{}"}})
    )
    executor = FakeExecutor(CommandResult(0, "", "Run id: 20260814T130000Z-abcd1234\n"))
    process = ClaudeLoopProcess(executor=executor, max_turns=1, max_dollars=0.1)
    new_run = runs_root / "20260814T130000Z-abcd1234"
    new_run.mkdir()
    (new_run / "events.jsonl").write_text(
        json.dumps({"event_type": "chatter.assistant", "payload": {"text": "{}"}})
    )
    await process.run(spec(tmp_path))
    assert len(executor.calls) == 1


# --- _looks_structured edge cases -------------------------------------------


def test_looks_structured_rejects_unclosed_fence() -> None:
    from vibey.infrastructure.engines.claudeloop_process import _looks_structured

    assert _looks_structured('```json\n{"a":1}') is False


def test_looks_structured_rejects_non_dict() -> None:
    from vibey.infrastructure.engines.claudeloop_process import _looks_structured

    assert _looks_structured("[1, 2, 3]") is False


def test_looks_structured_rejects_invalid_json() -> None:
    from vibey.infrastructure.engines.claudeloop_process import _looks_structured

    assert _looks_structured("not json at all") is False


def test_reported_run_id_skips_invalid_format() -> None:
    from vibey.infrastructure.engines.claudeloop_process import _reported_run_id

    stderr = "Run id: !!!invalid\nRun id: valid-20260814T120000Z\n"
    assert _reported_run_id(stderr) == "valid-20260814T120000Z"


async def test_find_reusable_skips_plan_outside_plans_root(tmp_path: Path) -> None:
    runs_root = tmp_path / ".claudeloop" / "runs"
    old_run = runs_root / "20260814T120000Z-abcd1234"
    old_run.mkdir(parents=True)
    outside_plan = tmp_path / "outside" / "plan.md"
    outside_plan.parent.mkdir(parents=True)
    outside_plan.write_text("# Bounded DESIGN research\n")
    (old_run / "meta.json").write_text(json.dumps({"plan_path": str(outside_plan)}))
    (old_run / "events.jsonl").write_text(
        json.dumps({"event_type": "chatter.assistant", "payload": {"text": "{}"}})
    )
    executor = FakeExecutor(CommandResult(0, "", "Run id: 20260814T130000Z-abcd1234\n"))
    process = ClaudeLoopProcess(executor=executor, max_turns=1, max_dollars=0.1)
    new_run = runs_root / "20260814T130000Z-abcd1234"
    new_run.mkdir()
    (new_run / "events.jsonl").write_text(
        json.dumps({"event_type": "chatter.assistant", "payload": {"text": "{}"}})
    )
    await process.run(spec(tmp_path))
    assert len(executor.calls) == 1
