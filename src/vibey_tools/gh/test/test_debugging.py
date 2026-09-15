# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Advanced branch logging is complete, correlated, and tamper-evident."""

from __future__ import annotations

import dis
import hashlib
import io
import json
import sys
import threading
from types import SimpleNamespace

import pytest

from vibey_gh import debugging


@pytest.fixture(autouse=True)
def tracing_is_reset(monkeypatch):
    debugging.disable()
    monkeypatch.delenv(debugging.DEBUG_ENV, raising=False)
    monkeypatch.delenv(debugging.LOG_ENV, raising=False)
    monkeypatch.delenv(debugging.TRACE_ENV, raising=False)
    yield
    debugging.disable()


def _records(stream: io.StringIO) -> list[dict]:
    return [json.loads(line) for line in stream.getvalue().splitlines()]


def test_branch_validation_checks_every_python_code_object(tmp_path):
    plain = tmp_path / "README.md"
    plain.write_text("not Python")
    valid = tmp_path / "valid.py"
    valid.write_text("def choose(value):\n    return 1 if value else 0\n")
    broken = tmp_path / "broken.py"
    broken.write_text("if:\n")

    problems = debugging.branch_logging_problems([plain, valid, broken])
    assert len(problems) == 1
    assert "SyntaxError" in problems[0]


def test_branch_validation_flags_a_branch_the_tracer_cannot_classify(tmp_path, monkeypatch):
    valid = tmp_path / "valid.py"
    valid.write_text("def choose(value):\n    return 1 if value else 0\n")
    root = compile(valid.read_text(), str(valid), "exec")
    branch = next(
        instruction
        for code in debugging._code_objects(root)
        for instruction in dis.get_instructions(code)
        if debugging._is_branch(instruction)
    )
    assert not debugging._unsupported_branch(branch)

    # A branch opcode dis cannot resolve to an integer offset (e.g. a dynamic or
    # computed target) is one this tracer's outcome classification cannot represent.
    synthetic = branch._replace(argval="dynamic-target")
    assert debugging._unsupported_branch(synthetic)

    monkeypatch.setattr(debugging, "_code_objects", lambda code: [code])
    monkeypatch.setattr(debugging.dis, "get_instructions", lambda code: [synthetic])
    problems = debugging.branch_logging_problems([valid])
    expected = (
        f"{valid}:{synthetic.starts_line or root.co_firstlineno}: "
        f"unsupported branch opcode {synthetic.opname}"
    )
    assert problems == [expected]


def test_branch_trace_records_outcomes_and_a_verifiable_hash_chain(tmp_path):
    stream = io.StringIO()
    source = tmp_path / "decision.py"
    source.write_text(
        "def choose(value):\n"
        "    if value:\n"
        "        result = 1\n"
        "    else:\n"
        "        result = 0\n"
        "    return result\n"
    )
    namespace: dict = {}
    root_code = compile(source.read_text(), str(source), "exec")
    exec(root_code, namespace)  # noqa: S102 - execute a fixed local test fixture
    code = namespace["choose"].__code__
    instructions = debugging._instructions(code)
    branch = next(
        instruction for instruction in instructions.values() if debugging._is_branch(instruction)
    )
    successors = [offset for offset in instructions if offset > branch.offset]
    fallthrough = next(offset for offset in successors if offset != branch.argval)
    frame = SimpleNamespace(
        f_code=code,
        f_lasti=branch.offset,
        f_lineno=2,
        f_trace_lines=False,
        f_trace_opcodes=False,
    )

    tracer = debugging.BranchTracer(stream, (tmp_path,))
    assert tracer(frame, "call", None) is tracer
    assert frame.f_trace_lines and frame.f_trace_opcodes
    outsider = SimpleNamespace(f_code=compile("pass", "/outside.py", "exec"))
    assert tracer(outsider, "call", None) is None

    tracer(frame, "opcode", None)
    frame.f_lasti = int(branch.argval)
    tracer(frame, "line", None)
    frame.f_lasti = branch.offset
    tracer(frame, "opcode", None)
    frame.f_lasti = fallthrough
    tracer(frame, "opcode", None)
    frame.f_lasti = 9999
    tracer(frame, "opcode", None)
    tracer(frame, "return", None)
    tracer(frame, "exception", None)
    tracer(frame, "unknown", None)

    # A root used as the synthetic filename exercises the safe basename fallback.
    fallback_code = compile("if value:\n    value = 2\n", str(tmp_path), "exec")
    fallback_branch = next(
        instruction
        for instruction in debugging._instructions(fallback_code).values()
        if debugging._is_branch(instruction)
    )
    fallback = SimpleNamespace(
        f_code=fallback_code,
        f_lasti=fallback_branch.offset,
        f_lineno=1,
        f_trace_lines=False,
        f_trace_opcodes=False,
    )
    tracer(fallback, "opcode", None)
    tracer._pending[id(fallback)] = (fallback_branch._replace(argval="dynamic"), "x", "f", 1)
    tracer._resolve_pending(fallback, 0)

    records = _records(stream)
    evaluated = [record for record in records if record["event"] == "branch_evaluated"]
    branch_records = [record for record in records if record["event"] == "branch"]
    assert len(evaluated) == 3
    assert {record["outcome"] for record in branch_records} == {"taken", "fallthrough"}
    assert {record["source"] for record in branch_records} == {"decision.py", "x"}
    assert [record["sequence"] for record in records] == list(range(1, len(records) + 1))
    assert all(record["trace_id"] == tracer.trace_id for record in records)
    assert records[0]["previous_hash"] == "0" * 64
    for index, record in enumerate(records):
        event_hash = record.pop("event_hash")
        canonical = json.dumps(record, sort_keys=True, separators=(",", ":"))
        assert event_hash == hashlib.sha256(canonical.encode()).hexdigest()
        if index:
            assert record["previous_hash"] == records[index - 1]["event_hash"]
        record["event_hash"] = event_hash


def test_enable_is_opt_in_and_supports_stderr_and_file_sinks(tmp_path, monkeypatch, capsys):
    assert debugging.enable() is None

    trace_calls = []
    thread_calls = []
    caller = SimpleNamespace(f_trace=None)
    monkeypatch.setattr(sys, "gettrace", lambda: "previous")
    monkeypatch.setattr(sys, "settrace", trace_calls.append)
    monkeypatch.setattr(sys, "_getframe", lambda depth: caller)
    monkeypatch.setattr(threading, "gettrace", lambda: "previous-thread")
    monkeypatch.setattr(threading, "settrace", thread_calls.append)

    monkeypatch.setenv(debugging.DEBUG_ENV, "yes")
    monkeypatch.setenv(debugging.TRACE_ENV, "trace-from-operator")
    tracer = debugging.enable(roots=(tmp_path,))
    assert tracer is not None and tracer.trace_id == "trace-from-operator"
    assert debugging.enable(roots=(tmp_path,)) is tracer
    assert caller.f_trace is tracer
    assert tracer._owned(str(tmp_path))
    assert not tracer._owned(str(tmp_path.parent / "elsewhere.py"))
    debugging.disable()
    assert trace_calls[-1] == "previous"
    assert thread_calls[-1] == "previous-thread"
    assert capsys.readouterr().err == ""

    destination = tmp_path / "trace.jsonl"
    monkeypatch.setenv(debugging.LOG_ENV, str(destination))
    tracer = debugging.enable(roots=(tmp_path,))
    assert tracer is not None
    debugging.disable()
    assert destination.read_text() == ""

    explicit = io.StringIO()
    tracer = debugging.enable(stream=explicit, roots=(tmp_path,))
    assert tracer is not None
    debugging.disable()
