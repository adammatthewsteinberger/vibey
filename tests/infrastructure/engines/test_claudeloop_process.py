import json
from pathlib import Path
from uuid import UUID

import pytest

from vibey.application.dto import RunSpec
from vibey.domain.effort import Effort
from vibey.domain.engine import IsolationLevel
from vibey.infrastructure.engines.claudeloop_process import (
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


def spec(tmp_path: Path) -> RunSpec:
    return RunSpec(
        run_id=UUID("00000000-0000-0000-0000-000000000123"),
        worktree_path=tmp_path,
        prompt="# Bounded DESIGN research\n",
        effort=Effort.STANDARD,
        isolation=IsolationLevel.WORKTREE,
    )


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
        json.dumps({"event_type": "chatter.assistant", "payload": {"text": "recovered"}})
    )
    executor = FakeExecutor(CommandResult(0, "", "should not run"))
    process = ClaudeLoopProcess(executor=executor, max_turns=1, max_dollars=0.1)

    result = await process.run(spec(tmp_path))

    assert result.response == "recovered"
    assert result.run_dir == run_dir
    assert executor.calls == []


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
