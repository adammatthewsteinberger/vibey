# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Optional AgentGateway that shells out to ``agent -p`` (never shell=True).

Primary path remains the Cursor Python SDK. This adapter exists so the
AgentGateway port is proven by three independent implementations and so
environments without the SDK bridge binary can still run.
"""

from __future__ import annotations

import json
import shutil
import subprocess  # nosec B404 — fixed argv, never shell=True
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from cursorloop.application.dto import TurnOutcome
from cursorloop.domain.classify import TurnSignals
from cursorloop.domain.completion import StructuredVerdict
from cursorloop.domain.model_profile import ModelProfile


def build_agent_argv(
    *,
    prompt: str,
    model: str,
    workspace: Path,
    force: bool = True,
) -> list[str]:
    """Build the argv for ``agent -p`` — never joined into a shell string."""
    argv = [
        "agent",
        "-p",
        prompt,
        "--trust",
        "--approve-mcps",
        "--output-format",
        "stream-json",
        "--stream-partial-output",
        "--model",
        model,
        "--workspace",
        str(workspace),
    ]
    if force:
        argv.insert(2, "--force")
    return argv


def parse_stream_json_lines(lines: Sequence[str]) -> TurnOutcome:
    """Fold stream-json lines into the same TurnOutcome shape as the SDK path."""
    text_parts: list[str] = []
    signals = TurnSignals()
    verdict: StructuredVerdict | None = None
    agent_id = "cli-fallback-agent"
    tokens = 0
    raw_events: list[dict[str, object]] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        try:
            event = json.loads(stripped)
        except json.JSONDecodeError:
            text_parts.append(stripped)
            continue
        if not isinstance(event, dict):
            continue
        raw_events.append({str(k): v for k, v in event.items()})
        etype = str(event.get("type", event.get("event", "")))
        if etype in {"assistant", "text", "message"}:
            content = event.get("content") or event.get("text") or event.get("delta")
            if isinstance(content, str):
                text_parts.append(content)
        if etype in {"error", "result"} and event.get("error"):
            err = event["error"]
            if isinstance(err, dict):
                signals = TurnSignals(
                    error_type=str(err.get("type", err.get("name", "Error"))),
                    error_message=str(err.get("message", "")),
                    error_code=None if err.get("code") is None else str(err.get("code")),
                    is_retryable=bool(err.get("is_retryable", False)),
                    http_status=(None if err.get("status") is None else int(str(err["status"]))),
                )
        if "verdict" in event and isinstance(event["verdict"], dict):
            v = event["verdict"]
            remaining = v.get("remaining_work", ())
            remaining_t = tuple(str(x) for x in remaining) if isinstance(remaining, list) else ()
            blocked = v.get("blocked_on")
            verdict = StructuredVerdict(
                complete=bool(v.get("complete", False)),
                remaining_work=remaining_t,
                blocked_on=None if blocked is None else str(blocked),
                summary=str(v.get("summary", "")),
            )
        if event.get("agent_id"):
            agent_id = str(event["agent_id"])
        if event.get("tokens") is not None:
            tokens = int(str(event["tokens"]))

    output = "".join(text_parts)
    if verdict is None:
        verdict = _verdict_from_text(output)
    return TurnOutcome(
        signals=signals,
        verdict=verdict,
        output_text=output,
        agent_id=agent_id,
        tokens=tokens,
        raw_events=tuple(raw_events),
    )


def _verdict_from_text(text: str) -> StructuredVerdict | None:
    marker = "```cursorloop-verdict"
    start = text.find(marker)
    if start < 0:
        return None
    rest = text[start + len(marker) :]
    end = rest.find("```")
    if end < 0:
        return None
    try:
        raw = json.loads(rest[:end].strip())
    except json.JSONDecodeError:
        return None
    if not isinstance(raw, dict):
        return None
    remaining = raw.get("remaining_work", ())
    remaining_t = tuple(str(x) for x in remaining) if isinstance(remaining, list) else ()
    blocked = raw.get("blocked_on")
    return StructuredVerdict(
        complete=bool(raw.get("complete", False)),
        remaining_work=remaining_t,
        blocked_on=None if blocked is None else str(blocked),
        summary=str(raw.get("summary", "")),
    )


@dataclass
class CliFallbackGateway:
    """AgentGateway that invokes the Cursor ``agent`` CLI.

    ``runner`` is injectable for tests — production uses subprocess.run.
    """

    workspace: Path
    model: str = "composer-2.5"
    agent_binary: str = "agent"
    runner: Any = field(default=None)
    _profile: ModelProfile | None = field(default=None, init=False)
    _cwd: str = field(default="", init=False)
    closed: bool = field(default=False, init=False)
    _uses_default_runner: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self._cwd = str(self.workspace)
        if self.runner is None:
            self._uses_default_runner = True
            self.runner = self._default_runner

    def agent_id(self) -> str:
        return f"cli-fallback:{self.workspace.name}"

    async def set_profile(self, profile: ModelProfile) -> None:
        self._profile = profile
        self.model = profile.model_id

    async def set_cwd(self, cwd: str) -> None:
        self._cwd = cwd
        self.workspace = Path(cwd)

    async def cancel_active_run(self) -> bool:
        return False

    async def close(self) -> None:
        self.closed = True

    async def send_turn(self, prompt_text: str, *, force: bool = False) -> TurnOutcome:
        del force
        if shutil.which(self.agent_binary) is None and self._uses_default_runner:
            raise FileNotFoundError(
                f"{self.agent_binary!r} not found on PATH; install the Cursor "
                "agent CLI or use the SDK gateway"
            )
        argv = build_agent_argv(
            prompt=prompt_text,
            model=self.model,
            workspace=Path(self._cwd),
            force=True,
        )
        argv[0] = self.agent_binary
        completed = self.runner(argv)
        stdout = completed.stdout if hasattr(completed, "stdout") else str(completed)
        lines = stdout.splitlines() if isinstance(stdout, str) else []
        return parse_stream_json_lines(lines)

    def _default_runner(self, argv: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(  # nosec B603
            argv,
            cwd=self._cwd,
            capture_output=True,
            text=True,
            check=False,
        )
