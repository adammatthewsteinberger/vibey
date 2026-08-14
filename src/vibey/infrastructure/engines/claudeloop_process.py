"""Bounded ClaudeLoop subprocess boundary for live DESIGN work.

Every invocation has explicit turn and dollar ceilings and disables automatic
model escalation.  The executor is injected so command construction and run
artifact parsing can be verified without launching or paying for a model run.
"""

import asyncio
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from vibey.application.dto import RunSpec
from vibey.infrastructure.engines.argv import build_argv
from vibey.infrastructure.engines.descriptors import CLAUDELOOP
from vibey.infrastructure.engines.plan_writer import write_plan

_RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


@dataclass(frozen=True, slots=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


class CommandExecutor(Protocol):
    async def execute(self, argv: tuple[str, ...]) -> CommandResult: ...


class AsyncSubprocessExecutor:
    async def execute(self, argv: tuple[str, ...]) -> CommandResult:
        process = await asyncio.create_subprocess_exec(
            *argv,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        return CommandResult(process.returncode or 0, stdout.decode(), stderr.decode())


@dataclass(frozen=True, slots=True)
class ClaudeLoopResult:
    run_id: str
    run_dir: Path
    response: str


class ClaudeLoopProcess:
    def __init__(self, *, executor: CommandExecutor, max_turns: int, max_dollars: float) -> None:
        if max_turns < 1 or not 0 < max_dollars <= 10:
            raise ValueError("live runs require a positive turn cap and a dollar cap at most 10")
        self._executor = executor
        self._max_turns = max_turns
        self._max_dollars = max_dollars

    async def run(self, spec: RunSpec, *, web_search: bool = False) -> ClaudeLoopResult:
        reusable = _find_reusable_result(spec)
        if reusable is not None:
            return reusable
        write_plan(spec)
        argv = (
            *build_argv(CLAUDELOOP, spec),
            "--max-turns",
            str(self._max_turns),
            "--max-dollars",
            format(self._max_dollars, "g"),
            "--no-auto-model",
            *(("--web-search",) if web_search else ()),
        )
        completed = await self._executor.execute(argv)
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip()
            raise RuntimeError(f"claudeloop failed with exit {completed.returncode}: {detail}")
        run_id = _reported_run_id(completed.stderr)
        run_dir = spec.worktree_path / CLAUDELOOP.state_dir / "runs" / run_id
        return ClaudeLoopResult(run_id, run_dir, _last_response(run_dir / "events.jsonl"))


def _reported_run_id(stderr: str) -> str:
    for line in stderr.splitlines():
        if line.startswith("Run id:"):
            run_id = line.partition(":")[2].strip()
            if _RUN_ID.fullmatch(run_id):
                return run_id
    raise RuntimeError("claudeloop did not report a run id")


def _last_response(events_path: Path) -> str:
    if not events_path.is_file():
        return ""
    for line in reversed(events_path.read_text().splitlines()):
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        payload = record.get("payload")
        if not isinstance(payload, dict):
            continue
        event_type = record.get("event_type")
        if event_type == "chatter.assistant" and isinstance(payload.get("text"), str):
            return str(payload["text"])
        if (
            event_type == "sdk.message"
            and payload.get("type") == "ResultMessage"
            and isinstance(payload.get("result"), str)
        ):
            return str(payload["result"])
    return ""


def _find_reusable_result(spec: RunSpec) -> ClaudeLoopResult | None:
    runs_root = spec.worktree_path / CLAUDELOOP.state_dir / "runs"
    plans_root = (spec.worktree_path / ".vibey" / "plans").resolve()
    if not runs_root.is_dir():
        return None
    for run_dir in sorted(runs_root.iterdir(), reverse=True):
        if not run_dir.is_dir() or not _RUN_ID.fullmatch(run_dir.name):
            continue
        try:
            meta = json.loads((run_dir / "meta.json").read_text())
            plan = Path(str(meta["plan_path"])).resolve()
            if not plan.is_relative_to(plans_root) or plan.read_text() != spec.prompt:
                continue
        except (FileNotFoundError, KeyError, json.JSONDecodeError, OSError):
            continue
        response = _last_response(run_dir / "events.jsonl")
        if response.strip():
            return ClaudeLoopResult(run_dir.name, run_dir, response)
    return None
