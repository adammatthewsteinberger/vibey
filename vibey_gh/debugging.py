# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Opt-in, tamper-evident branch tracing without exposing application data.

The tracer records control-flow metadata only. It deliberately never serializes local
variables, arguments, return values, environment values, or exception messages.
"""

from __future__ import annotations

import dis
import hashlib
import json
import os
import sys
import threading
import time
import types
import uuid
from contextlib import ExitStack
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import IO, Any

SCHEMA = "vibey-gh.branch-trace.v1"
DEBUG_ENV = "VIBEY_GH_DEBUG"
LOG_ENV = "VIBEY_GH_DEBUG_LOG"
TRACE_ENV = "VIBEY_GH_TRACE_ID"


def _is_branch(instruction: dis.Instruction) -> bool:
    return instruction.opcode in dis.hasjabs or instruction.opcode in dis.hasjrel


def _unsupported_branch(instruction: dis.Instruction) -> bool:
    """Return True when the tracer cannot faithfully classify this branch's outcome.

    ``BranchTracer._resolve_pending`` decides "taken" vs. "fallthrough" by comparing
    the actual successor offset against ``instruction.argval``, which dis populates
    with the integer jump-target offset for every branch opcode it knows about. A
    branch whose ``argval`` is not an int is one this tracer cannot classify.
    """
    return _is_branch(instruction) and not isinstance(instruction.argval, int)


def _instructions(code: types.CodeType) -> dict[int, dis.Instruction]:
    return {instruction.offset: instruction for instruction in dis.get_instructions(code)}


def _code_objects(code: types.CodeType):
    yield code
    for constant in code.co_consts:
        if isinstance(constant, types.CodeType):
            yield from _code_objects(constant)


def branch_logging_problems(paths: list[Path]) -> list[str]:
    """Return Python sources whose branches cannot be represented by this tracer."""
    problems: list[str] = []
    for path in paths:
        if path.suffix != ".py":
            continue
        try:
            source = path.read_text(encoding="utf-8")
            root = compile(source, str(path), "exec")
        except (OSError, SyntaxError, UnicodeError) as exc:
            problems.append(f"{path}: cannot validate branch logging: {type(exc).__name__}")
            continue
        for code in _code_objects(root):
            for instruction in dis.get_instructions(code):
                if _unsupported_branch(instruction):
                    problems.append(
                        f"{path}:{instruction.starts_line or code.co_firstlineno}: "
                        f"unsupported branch opcode {instruction.opname}"
                    )
    return problems


@dataclass
class BranchTracer:
    """Trace executed control-flow edges into a correlated SHA-256 hash chain."""

    stream: IO[str]
    roots: tuple[Path, ...]
    trace_id: str = field(default_factory=lambda: os.environ.get(TRACE_ENV) or str(uuid.uuid4()))
    _sequence: int = 0
    _previous_hash: str = "0" * 64
    _pending: dict[int, tuple[dis.Instruction, str, str, int]] = field(default_factory=dict)
    _cache: dict[types.CodeType, dict[int, dis.Instruction]] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def __post_init__(self) -> None:
        self.roots = tuple(root.resolve() for root in self.roots)

    def _owned(self, filename: str) -> bool:
        path = Path(filename).resolve()
        return any(path == root or root in path.parents for root in self.roots)

    def _emit(self, event: dict[str, Any]) -> None:
        with self._lock:
            self._sequence += 1
            record = {
                "schema": SCHEMA,
                "trace_id": self.trace_id,
                "sequence": self._sequence,
                "timestamp": datetime.now(UTC).isoformat(),
                "monotonic_ns": time.monotonic_ns(),
                "pid": os.getpid(),
                "thread_id": threading.get_ident(),
                "github_run_id": os.environ.get("GITHUB_RUN_ID"),
                "github_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
                "git_sha": os.environ.get("GITHUB_SHA"),
                "previous_hash": self._previous_hash,
                **event,
            }
            canonical = json.dumps(record, sort_keys=True, separators=(",", ":"))
            record_hash = hashlib.sha256(canonical.encode()).hexdigest()
            record["event_hash"] = record_hash
            self._previous_hash = record_hash
            self.stream.write(json.dumps(record, sort_keys=True) + "\n")
            self.stream.flush()

    def _resolve_pending(self, frame, actual_offset: int) -> None:
        pending = self._pending.pop(id(frame), None)
        if pending is None:
            return
        instruction, source, function, line = pending
        target = instruction.argval if isinstance(instruction.argval, int) else None
        self._emit(
            {
                "event": "branch",
                "source": source,
                "function": function,
                "line": line,
                "offset": instruction.offset,
                "opcode": instruction.opname,
                "target_offset": target,
                "actual_offset": actual_offset,
                "outcome": "taken" if actual_offset == target else "fallthrough",
            }
        )

    def __call__(self, frame, event: str, arg):
        if event == "call":
            if not self._owned(frame.f_code.co_filename):
                return None
            # Line events provide the successor offset even when CPython fuses the
            # successor into RETURN_CONST and omits a distinct opcode callback.
            frame.f_trace_lines = True
            frame.f_trace_opcodes = True
            return self
        if event == "line":
            self._resolve_pending(frame, frame.f_lasti)
        elif event == "opcode":
            self._resolve_pending(frame, frame.f_lasti)
            instructions = self._cache.setdefault(frame.f_code, _instructions(frame.f_code))
            instruction = instructions.get(frame.f_lasti)
            if instruction is not None and _is_branch(instruction):
                source_path = Path(frame.f_code.co_filename).resolve()
                source = next(
                    (
                        str(source_path.relative_to(root))
                        for root in self.roots
                        if root in source_path.parents
                    ),
                    source_path.name,
                )
                self._emit(
                    {
                        "event": "branch_evaluated",
                        "source": source,
                        "function": frame.f_code.co_qualname,
                        "line": frame.f_lineno,
                        "offset": instruction.offset,
                        "opcode": instruction.opname,
                        "target_offset": (
                            instruction.argval if isinstance(instruction.argval, int) else None
                        ),
                    }
                )
                self._pending[id(frame)] = (
                    instruction,
                    source,
                    frame.f_code.co_qualname,
                    frame.f_lineno,
                )
        elif event in {"return", "exception"}:
            self._resolve_pending(frame, frame.f_lasti)
        return self


_active: BranchTracer | None = None
_owned_stream: IO[str] | None = None
_stream_stack = ExitStack()
_previous_trace: Any = None
_previous_thread_trace: Any = None


def enable(
    *, stream: IO[str] | None = None, roots: tuple[Path, ...] | None = None
) -> BranchTracer | None:
    """Enable tracing when requested, returning the active tracer for inspection."""
    global _active, _owned_stream, _previous_thread_trace, _previous_trace, _stream_stack
    if _active is not None:
        return _active
    if stream is None and os.environ.get(DEBUG_ENV, "").lower() not in {"1", "true", "yes", "on"}:
        return None
    if stream is None:
        destination = os.environ.get(LOG_ENV)
        if destination:
            _stream_stack = ExitStack()
            _owned_stream = _stream_stack.enter_context(
                Path(destination).open("a", encoding="utf-8")  # noqa: SIM115 - owned until disable
            )
            stream = _owned_stream
        else:
            stream = sys.stderr
    package_root = Path(__file__).resolve().parent
    _active = BranchTracer(stream, roots or (package_root,))
    _previous_trace = sys.gettrace()
    _previous_thread_trace = threading.gettrace()
    sys.settrace(_active)
    threading.settrace(_active)
    # Activate tracing immediately in the caller; otherwise CPython may defer the
    # first child call until the caller produces its next trace event.
    sys._getframe(1).f_trace = _active
    return _active


def disable() -> None:
    """Disable branch tracing and close only a stream opened by this module."""
    global _active, _owned_stream, _previous_thread_trace, _previous_trace
    if _active is None:
        return
    sys.settrace(_previous_trace)
    threading.settrace(_previous_thread_trace)
    _active = None
    _previous_trace = None
    _previous_thread_trace = None
    if _owned_stream is not None:
        _stream_stack.close()
        _owned_stream = None
