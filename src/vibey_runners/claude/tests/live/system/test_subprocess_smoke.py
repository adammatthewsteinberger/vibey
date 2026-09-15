# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Thin subprocess smoke: real claudeloop CLI + env-gated scripted agent."""

from __future__ import annotations

import json
import os
import subprocess  # nosec B404 - fixed argv lists only
import sys
import time
from pathlib import Path

import pytest

from claudeloop.infrastructure.agent.scripted import (
    ALLOW_TEST_AGENT_ENV,
    TEST_AGENT_SCRIPT_ENV,
)

pytestmark = pytest.mark.system

_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "agent_scripts"
_DONE = _FIXTURES / "done.json"
_WAIT = _FIXTURES / "wait_long.json"


def _env_with_script(script: Path) -> dict[str, str]:
    env = os.environ.copy()
    env[ALLOW_TEST_AGENT_ENV] = "1"
    env[TEST_AGENT_SCRIPT_ENV] = str(script)
    # Prefer the in-repo package under test
    src = str(Path(__file__).resolve().parents[3] / "src")
    env["PYTHONPATH"] = src + os.pathsep + env.get("PYTHONPATH", "")
    return env


def _claudeloop_bin() -> str:
    candidate = Path(sys.executable).parent / "claudeloop"
    if candidate.is_file():
        return str(candidate)
    return "claudeloop"


def _claudeloop(
    args: list[str], *, cwd: Path, env: dict[str, str], timeout: float = 60
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # nosec B603
        [_claudeloop_bin(), *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def test_help_lists_ops_commands() -> None:
    result = _claudeloop(["--help"], cwd=Path.cwd(), env=os.environ.copy())
    assert result.returncode == 0
    for cmd in (
        "stop",
        "prompt",
        "logs",
        "status",
        "runs",
        "savepoints",
        "unwind",
        "watch",
        "permission-mode",
        "attach",
        "memory",
        "chat",
        "response",
        "cwd",
        "slash",
        "tool",
        "folder",
        "skill",
    ):
        assert cmd in result.stdout


def test_mid_run_permission_mode_via_cli(git_sandbox: Path) -> None:
    """Scripted wait run + mid-run permission-mode enqueue via real CLI."""
    plan = git_sandbox / "plan.md"
    plan.write_text("Wait then finish.\n", encoding="utf-8")
    env = _env_with_script(_WAIT)
    proc = subprocess.Popen(  # nosec B603
        [_claudeloop_bin(), "run", str(plan), "--max-turns", "5"],
        cwd=git_sandbox,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        run_id = None
        for _ in range(40):
            runs = list((git_sandbox / ".claudeloop" / "runs").glob("*"))
            if runs:
                run_id = runs[0].name
                break
            time.sleep(0.25)
        assert run_id is not None
        result = _claudeloop(
            ["permission-mode", "plan", "--run-id", run_id],
            cwd=git_sandbox,
            env=env,
        )
        assert result.returncode == 0, result.stderr + result.stdout
        note = git_sandbox / "n.txt"
        note.write_text("x\n", encoding="utf-8")
        result = _claudeloop(
            ["attach", str(note), "--run-id", run_id],
            cwd=git_sandbox,
            env=env,
        )
        assert result.returncode == 0, result.stderr + result.stdout
        _claudeloop(["stop", "--run-id", run_id], cwd=git_sandbox, env=env)
    finally:
        proc.wait(timeout=120)


def test_run_completes_with_scripted_agent(git_sandbox: Path) -> None:
    plan = git_sandbox / "plan.md"
    plan.write_text("Do the trivial scripted task.\n", encoding="utf-8")
    env = _env_with_script(_DONE)
    result = _claudeloop(["run", str(plan), "--max-turns", "3"], cwd=git_sandbox, env=env)
    assert result.returncode == 0, result.stderr + result.stdout
    assert "Done:" in result.stdout or "all done" in result.stdout + result.stderr
    runs = list((git_sandbox / ".claudeloop" / "runs").iterdir())
    assert runs
    events = (runs[0] / "events.jsonl").read_text(encoding="utf-8")
    assert "sk-ant-abcdefghijklmnopqrstuvwxyz012345" not in events
    # Dual console: human + JSON transport on stderr
    assert "run.started" in result.stderr or "run.finished" in result.stderr
    json_events = [
        json.loads(line)
        for line in result.stderr.splitlines()
        if line.startswith("{") and '"event"' in line
    ]
    assert any(e.get("transport") == "console_json" for e in json_events)
    names = {"run.started", "run.finished", "turn.completed"}
    assert any(e.get("event") in names for e in json_events)


def test_stop_during_wait_exits_130(git_sandbox: Path) -> None:
    plan = git_sandbox / "plan.md"
    plan.write_text("Wait forever until stopped.\n", encoding="utf-8")
    env = _env_with_script(_WAIT)
    proc = subprocess.Popen(  # nosec B603
        [_claudeloop_bin(), "run", str(plan), "--max-turns", "5"],
        cwd=git_sandbox,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    run_dir = None
    deadline = time.time() + 30
    while time.time() < deadline:
        root = git_sandbox / ".claudeloop" / "runs"
        if root.is_dir():
            kids = list(root.iterdir())
            if kids:
                status = kids[0] / "status.json"
                if status.is_file():
                    run_dir = kids[0]
                    break
        time.sleep(0.1)
    assert run_dir is not None, "run directory never appeared"
    # Wait until meta shows waiting or events mention waiting
    deadline = time.time() + 30
    while time.time() < deadline:
        meta = json.loads((run_dir / "meta.json").read_text(encoding="utf-8"))
        bus_path = run_dir / "bus.jsonl"
        bus = bus_path.read_text(encoding="utf-8") if bus_path.is_file() else ""
        if meta.get("waiting_until") or "waiting" in bus.lower() or "WAITING" in bus:
            break
        time.sleep(0.1)
    stop = _claudeloop(["stop", "--run-id", run_dir.name], cwd=git_sandbox, env=env)
    assert stop.returncode == 0, stop.stderr
    try:
        code = proc.wait(timeout=60)
    except subprocess.TimeoutExpired:
        proc.kill()
        raise
    out = proc.stdout.read() if proc.stdout else ""
    err = proc.stderr.read() if proc.stderr else ""
    assert code == 130, f"stdout={out!r} stderr={err!r}"
    assert (run_dir / "stop-summary.md").is_file()


def test_status_and_runs_after_complete(git_sandbox: Path) -> None:
    plan = git_sandbox / "plan.md"
    plan.write_text("Done script.\n", encoding="utf-8")
    env = _env_with_script(_DONE)
    done = _claudeloop(["run", str(plan)], cwd=git_sandbox, env=env)
    assert done.returncode == 0, done.stderr
    runs = _claudeloop(["runs"], cwd=git_sandbox, env=env)
    assert runs.returncode == 0
    assert runs.stdout.strip()
    status = _claudeloop(["status"], cwd=git_sandbox, env=env)
    assert status.returncode == 0
    logs = _claudeloop(["logs"], cwd=git_sandbox, env=env)
    assert logs.returncode == 0
    sps = _claudeloop(["savepoints"], cwd=git_sandbox, env=env)
    assert sps.returncode == 0


def test_script_without_allow_fails_loud(
    git_sandbox: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = git_sandbox / "plan.md"
    plan.write_text("x\n", encoding="utf-8")
    env = os.environ.copy()
    env.pop(ALLOW_TEST_AGENT_ENV, None)
    env[TEST_AGENT_SCRIPT_ENV] = str(_DONE)
    src = str(Path(__file__).resolve().parents[3] / "src")
    env["PYTHONPATH"] = src + os.pathsep + env.get("PYTHONPATH", "")
    result = _claudeloop(["run", str(plan)], cwd=git_sandbox, env=env, timeout=30)
    assert result.returncode != 0
    assert "ALLOW_TEST_AGENT" in result.stderr or "ALLOW_TEST_AGENT" in result.stdout
