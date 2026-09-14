# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.system

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "agent_scripts"
REPO = Path(__file__).resolve().parents[3]


def test_subprocess_done_exits_0(tmp_path: Path) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text("# Goal\n\n- [x] finish the work\n", encoding="utf-8")
    env = {
        **os.environ,
        "CURSORLOOP_ALLOW_TEST_AGENT": "1",
        "CURSORLOOP_TEST_AGENT_SCRIPT": str(FIXTURES / "done.json"),
        "PYTHONPATH": str(REPO / "src"),
    }
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "cursorloop",
            "run",
            "--plan",
            str(plan),
            "--cwd",
            str(tmp_path),
            "--no-managed-hooks",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
        cwd=str(REPO),
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr


def test_subprocess_help_lists_control_ops() -> None:
    env = {**os.environ, "PYTHONPATH": str(REPO / "src")}
    proc = subprocess.run(
        [sys.executable, "-m", "cursorloop", "--help"],
        check=False,
        capture_output=True,
        text=True,
        env=env,
        cwd=str(REPO),
        timeout=30,
    )
    assert proc.returncode == 0
    for name in ("stop", "prompt", "status", "logs", "watch", "runs", "doctor"):
        assert name in proc.stdout


def test_subprocess_credits_exits_1_without_recovery_budget(tmp_path: Path) -> None:
    """With max-wait 0s, credits exhaustion fails closed rather than probing forever."""
    plan = tmp_path / "plan.md"
    plan.write_text("# Goal\n\n- [x] finish the work\n", encoding="utf-8")
    env = {
        **os.environ,
        "CURSORLOOP_ALLOW_TEST_AGENT": "1",
        "CURSORLOOP_TEST_AGENT_SCRIPT": str(FIXTURES / "credits_then_available.json"),
        "PYTHONPATH": str(REPO / "src"),
    }
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "cursorloop",
            "run",
            "--plan",
            str(plan),
            "--cwd",
            str(tmp_path),
            "--no-managed-hooks",
            "--max-wait",
            "0",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
        cwd=str(REPO),
        timeout=60,
    )
    assert proc.returncode in {1, 4}, (proc.stdout, proc.stderr)
