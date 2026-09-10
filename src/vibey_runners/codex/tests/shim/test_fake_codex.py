# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Meta-tests for the fake `codex` shim and synthetic JSONL fixtures."""

from __future__ import annotations

import contextlib
import json
import os
import re
import signal
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path

import pytest

SHIM = Path(__file__).resolve().parent / "fake_codex.py"
JSONL = Path(__file__).resolve().parents[1] / "fixtures" / "jsonl"
HUGE_LINE_MIN_BYTES = 2 * 1024 * 1024
PID_LINE = re.compile(r"parent_pid=(\d+)\s+child_pid=(\d+)")

FIXTURE_NAMES = (
    "clean_completion",
    "tool_heavy",
    "turn_failed_429_window",
    "turn_failed_429_quota",
    "malformed_line",
    "huge_line",
    "truncated_stream",
)


def _run_shim(
    *,
    mode: str | None = None,
    script: Path | None = None,
    timeout: float = 8,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if mode is None:
        env.pop("FAKE_CODEX_MODE", None)
    else:
        env["FAKE_CODEX_MODE"] = mode
    if script is None:
        env.pop("FAKE_CODEX_SCRIPT", None)
    else:
        env["FAKE_CODEX_SCRIPT"] = str(script)
    return subprocess.run(
        [sys.executable, str(SHIM)],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
        check=False,
    )


def _load_jsonl(name: str) -> list[dict[str, object]]:
    path = JSONL / f"{name}.jsonl"
    events: list[dict[str, object]] = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        parsed = json.loads(line)
        assert isinstance(parsed, dict)
        events.append(parsed)
    return events


# --- Shim script contract -----------------------------------------------------


def test_shim_is_a_python3_script() -> None:
    assert SHIM.is_file(), f"expected shim at {SHIM}"
    first = SHIM.read_text(encoding="utf-8").splitlines()[0]
    assert first == "#!/usr/bin/env python3"


# --- Modes --------------------------------------------------------------------


def test_stream_mode_prints_fixture_to_stdout_and_exits_zero() -> None:
    script = JSONL / "clean_completion.jsonl"
    result = _run_shim(mode="stream", script=script)
    assert result.returncode == 0
    assert result.stdout == script.read_text(encoding="utf-8")
    assert result.stderr.strip() != ""
    assert "fake-codex" in result.stderr


def test_stream_is_the_default_mode() -> None:
    script = JSONL / "clean_completion.jsonl"
    result = _run_shim(mode=None, script=script)
    assert result.returncode == 0
    assert result.stdout == script.read_text(encoding="utf-8")


def test_exit_nonzero_prints_script_and_exits_two() -> None:
    script = JSONL / "clean_completion.jsonl"
    result = _run_shim(mode="exit_nonzero", script=script)
    assert result.returncode == 2
    assert result.stdout == script.read_text(encoding="utf-8")
    assert "fake-codex" in result.stderr


def test_huge_line_mode_emits_oversized_line_and_exits_zero() -> None:
    result = _run_shim(mode="huge_line")
    assert result.returncode == 0
    lines = result.stdout.splitlines()
    assert len(lines) == 1
    assert len(lines[0].encode("utf-8")) > HUGE_LINE_MIN_BYTES
    assert "fake-codex" in result.stderr


def test_hang_mode_stays_alive_until_killed() -> None:
    env = os.environ.copy()
    env["FAKE_CODEX_MODE"] = "hang"
    proc = subprocess.Popen(
        [sys.executable, str(SHIM)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    try:
        assert proc.stderr is not None
        line = proc.stderr.readline()
        assert "fake-codex" in line
        time.sleep(0.2)
        assert proc.poll() is None
    finally:
        proc.kill()
        proc.wait(timeout=5)


def test_orphan_child_mode_prints_parseable_pids() -> None:
    env = os.environ.copy()
    env["FAKE_CODEX_MODE"] = "orphan_child"
    proc = subprocess.Popen(
        [sys.executable, str(SHIM)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    child_pid: int | None = None
    try:
        assert proc.stderr is not None
        line = proc.stderr.readline()
        match = PID_LINE.search(line)
        assert match is not None, f"expected parseable pids in {line!r}"
        parent_pid = int(match.group(1))
        child_pid = int(match.group(2))
        assert parent_pid == proc.pid
        os.kill(child_pid, 0)
        assert proc.poll() is None
    finally:
        proc.kill()
        proc.wait(timeout=5)
        if child_pid is not None:
            with contextlib.suppress(ProcessLookupError):
                os.kill(child_pid, signal.SIGKILL)


# --- PATH fixture -------------------------------------------------------------


def test_fake_codex_on_path_installs_codex_executable(
    fake_codex_on_path: Path,
    configure_fake_codex: Callable[..., None],
) -> None:
    script = JSONL / "clean_completion.jsonl"
    configure_fake_codex(script=script, mode="stream")
    which = _which_codex()
    assert which is not None
    assert Path(which).name == "codex"
    assert Path(which).parent == fake_codex_on_path
    result = subprocess.run(
        ["codex", "exec", "--json", "ignored"],
        capture_output=True,
        text=True,
        timeout=8,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout == script.read_text(encoding="utf-8")
    assert "fake-codex" in result.stderr


def _which_codex() -> str | None:
    path = os.environ.get("PATH", "")
    for directory in path.split(os.pathsep):
        candidate = Path(directory) / "codex"
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


# --- JSONL fixtures -----------------------------------------------------------


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_jsonl_fixture_exists(name: str) -> None:
    path = JSONL / f"{name}.jsonl"
    assert path.is_file(), f"missing fixture {path}"


def test_fixtures_readme_marks_synthetic_with_todo() -> None:
    readme = JSONL / "README.md"
    assert readme.is_file()
    text = readme.read_text(encoding="utf-8")
    assert "SYNTHETIC" in text
    assert "TODO" in text


def test_clean_completion_fixture_shape() -> None:
    events = _load_jsonl("clean_completion")
    assert events[0]["type"] == "thread.started"
    assert events[0]["thread_id"]
    assert events[1]["type"] == "turn.started"
    completed_item = next(e for e in events if e["type"] == "item.completed")
    assert completed_item["item"]["type"] == "agent_message"
    assert completed_item["item"]["text"]
    turn_done = events[-1]
    assert turn_done["type"] == "turn.completed"
    usage = turn_done["usage"]
    assert "input_tokens" in usage
    assert "output_tokens" in usage


def test_tool_heavy_fixture_has_command_executions_then_turn_completed() -> None:
    events = _load_jsonl("tool_heavy")
    started = [e for e in events if e["type"] == "item.started"]
    completed = [e for e in events if e["type"] == "item.completed"]
    assert len(started) >= 2
    assert all(e["item"]["type"] == "command_execution" for e in started)
    assert any(e["item"]["type"] == "command_execution" for e in completed)
    assert events[-1]["type"] == "turn.completed"


def test_turn_failed_429_window_fixture_shape() -> None:
    events = _load_jsonl("turn_failed_429_window")
    failed = next(e for e in events if e["type"] == "turn.failed")
    error = failed["error"]
    assert error["code"] == "usage_limit_reached"
    assert error.get("status") == 429 or "429" in str(error)


def test_turn_failed_429_quota_fixture_shape() -> None:
    events = _load_jsonl("turn_failed_429_quota")
    failed = next(e for e in events if e["type"] == "turn.failed")
    error = failed["error"]
    assert error["code"] == "insufficient_quota"
    assert error.get("status") == 429 or "429" in str(error)


def test_malformed_line_fixture_mixes_valid_jsonl_and_non_json() -> None:
    raw = (JSONL / "malformed_line.jsonl").read_text(encoding="utf-8").splitlines()
    decoded: list[bool] = []
    for line in raw:
        if not line.strip():
            continue
        try:
            json.loads(line)
            decoded.append(True)
        except json.JSONDecodeError:
            decoded.append(False)
    assert True in decoded
    assert False in decoded


def test_huge_line_fixture_is_a_small_placeholder() -> None:
    path = JSONL / "huge_line.jsonl"
    assert path.stat().st_size < 10_000


def test_truncated_stream_fixture_has_no_turn_completed() -> None:
    events = _load_jsonl("truncated_stream")
    assert events[0]["type"] == "thread.started"
    assert all(e["type"] != "turn.completed" for e in events)
