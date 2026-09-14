# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Free-tier live tests: exercise the real installed CLI and real local Claude
Code environment, but never send a prompt to the model. Opt in with:

    pytest -m live tests/live/test_free_tier.py

Safe to run repeatedly and in any environment with `claude` installed and
authenticated — no tokens are spent.
"""

from __future__ import annotations

import subprocess  # nosec B404 - fixed-argument calls only, never shell=True
import sys
from pathlib import Path

import pytest

from claudeloop import __version__

pytestmark = pytest.mark.live


@pytest.fixture(scope="module")
def installed_wheel_venv(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Build the sdist/wheel exactly as CI's `build` job does, install it
    into a brand-new venv, and hand back that venv's bin/ directory. This is
    the specific check whose absence let a broken [project.scripts] entry
    point ship in the first place — see docs/architecture/decisions/ and the
    M2 commit that fixed it."""
    repo_root = Path(__file__).resolve().parents[2]
    dist_dir = tmp_path_factory.mktemp("dist")
    subprocess.run(  # nosec B603
        [sys.executable, "-m", "build", "--outdir", str(dist_dir)],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    wheel = next(dist_dir.glob("*.whl"))

    venv_dir = tmp_path_factory.mktemp("venv")
    subprocess.run(  # nosec B603
        [sys.executable, "-m", "venv", str(venv_dir)], check=True, capture_output=True
    )
    pip = venv_dir / "bin" / "pip"
    subprocess.run(  # nosec B603
        [str(pip), "install", "-q", str(wheel)], check=True, capture_output=True, text=True
    )
    return venv_dir / "bin"


def test_installed_console_script_reports_the_right_version(installed_wheel_venv: Path) -> None:
    result = subprocess.run(  # nosec B603
        [str(installed_wheel_venv / "claudeloop"), "--version"],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert result.returncode == 0
    assert __version__ in result.stdout


def test_installed_console_script_help_renders_without_a_traceback(
    installed_wheel_venv: Path,
) -> None:
    result = subprocess.run(  # nosec B603
        [str(installed_wheel_venv / "claudeloop"), "--help"],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert result.returncode == 0
    assert "Traceback" not in result.stderr
    for command in (
        "run",
        "resume",
        "stop",
        "prompt",
        "logs",
        "status",
        "runs",
        "savepoints",
        "unwind",
        "watch",
        "sessions",
        "doctor",
        "api",
    ):
        assert command in result.stdout


def test_run_help_documents_max_buffer_size() -> None:
    result = subprocess.run(  # nosec B603 B607
        ["claudeloop", "run", "--help"],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert result.returncode == 0
    assert "max-buffer-size" in result.stdout
    assert "Traceback" not in result.stderr


def test_doctor_runs_against_the_real_environment_without_crashing() -> None:
    """Doesn't assert every check passes — this machine's auth/MCP state is
    whatever it is — only that doctor completes and produces the expected
    check names, which is what proves the real subprocess calls to `claude`
    work end to end."""
    result = subprocess.run(  # nosec B603 B607
        ["claudeloop", "doctor"],
        capture_output=True,
        text=True,
        timeout=90,  # claude mcp list health-checks every configured server
        check=False,
    )
    assert result.returncode in (0, 1)  # 1 means "some check failed", not "doctor crashed"
    for check_name in ("claude-cli", "authentication", "mcp-servers", "working-directory"):
        assert check_name in result.stdout


def test_sessions_lists_the_real_session_store_read_only(sandbox_repo: Path) -> None:
    """Read-only — must never create, modify, or drive a session. Run against
    the sandbox repo, which has no prior sessions, so the only thing this
    proves is that the real list_sessions() call succeeds and renders
    without error, not that it finds anything."""
    result = subprocess.run(  # nosec B603 B607
        ["claudeloop", "sessions", "--cwd", str(sandbox_repo)],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert result.returncode == 0
    assert "Traceback" not in result.stderr
