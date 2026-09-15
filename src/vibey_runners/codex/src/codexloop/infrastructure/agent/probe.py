# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Ephemeral read-only ``codex exec`` capacity probe."""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path

from codexloop.application.dto import ProbeResult
from codexloop.domain.capacity import TransientBackendError
from codexloop.domain.classify import classify
from codexloop.domain.errors import CodexBinaryError
from codexloop.infrastructure.agent.argv import ExecOpts, build_probe_argv
from codexloop.infrastructure.agent.events import CodexEvent, JsonlParser
from codexloop.infrastructure.agent.gateway import RunCodex
from codexloop.infrastructure.agent.process import run_codex as default_run_codex
from codexloop.infrastructure.agent.translate import to_turn_signals

_DEFAULT_TIMEOUT_S = 300.0
_DEFAULT_MAX_LINE_BYTES = 1_048_576


class ExecCapacityProbe:
    """Capacity probe that never resumes and never writes a thread.

    Always uses :func:`build_probe_argv` (``--ephemeral``, read-only sandbox).
    Spawn failures become :class:`TransientBackendError` rather than raising.
    """

    def __init__(
        self,
        *,
        cwd: str | Path,
        env: Mapping[str, str] | None = None,
        opts: ExecOpts | None = None,
        now: datetime | None = None,
        run_codex: RunCodex | None = None,
        timeout: float = _DEFAULT_TIMEOUT_S,
        max_line_bytes: int = _DEFAULT_MAX_LINE_BYTES,
    ) -> None:
        self._cwd = Path(cwd)
        self._env = dict(env) if env is not None else None
        self._opts = opts if opts is not None else ExecOpts(prompt="")
        self._now = now
        self._run_codex = run_codex if run_codex is not None else default_run_codex
        self._timeout = timeout
        self._max_line_bytes = max_line_bytes

    async def probe(self) -> ProbeResult:
        argv = build_probe_argv(self._opts)
        env = self._env if self._env is not None else os.environ.copy()
        try:
            result = await self._run_codex(
                argv,
                cwd=self._cwd,
                env=env,
                timeout=self._timeout,
                max_line_bytes=self._max_line_bytes,
            )
        except (OSError, CodexBinaryError):
            return ProbeResult(outcome=TransientBackendError())
        events = self._parse_lines(result.stdout_lines)
        signals = to_turn_signals(
            events,
            exit_code=result.exit_code,
            stderr_tail=result.stderr_tail,
            now=self._now if self._now is not None else datetime.now(UTC),
        )
        return ProbeResult(outcome=classify(signals), snapshot=signals.plan_windows)

    def _parse_lines(self, lines: Sequence[str]) -> list[CodexEvent | None]:
        parser = JsonlParser(now=self._now if self._now is not None else datetime.now(UTC))
        return [parser.parse_line(line) for line in lines]
