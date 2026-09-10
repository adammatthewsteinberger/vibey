# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for cli/render.py — output formatting for CLI commands."""

from __future__ import annotations

from datetime import datetime, timezone

from claudeloop.application.usecases.doctor import DoctorCheck
from claudeloop.cli.render import render_doctor_checks, render_session_list, render_session_warning
from claudeloop.domain.session import SessionRef


def test_render_doctor_checks_with_all_passing() -> None:
    """render_doctor_checks shows checkmarks for passing checks."""
    checks = [
        DoctorCheck(name="Python version", passed=True, detail="3.12.0"),
        DoctorCheck(name="Git installed", passed=True, detail="git version 2.39.0"),
    ]
    output = render_doctor_checks(checks)
    assert "✓" in output
    assert "Python version: 3.12.0" in output
    assert "Git installed: git version 2.39.0" in output
    assert "✗" not in output


def test_render_doctor_checks_with_failures() -> None:
    """render_doctor_checks shows X marks for failing checks."""
    checks = [
        DoctorCheck(name="Python version", passed=True, detail="3.12.0"),
        DoctorCheck(name="API key", passed=False, detail="not found"),
    ]
    output = render_doctor_checks(checks)
    assert "✓ Python version: 3.12.0" in output
    assert "✗ API key: not found" in output


def test_render_doctor_checks_empty_list() -> None:
    """render_doctor_checks handles empty check list."""
    output = render_doctor_checks([])
    assert output == ""


def test_render_doctor_checks_multiline_format() -> None:
    """Each check appears on its own line with consistent indentation."""
    checks = [
        DoctorCheck(name="Check1", passed=True, detail="ok"),
        DoctorCheck(name="Check2", passed=False, detail="fail"),
        DoctorCheck(name="Check3", passed=True, detail="ok"),
    ]
    output = render_doctor_checks(checks)
    lines = output.split("\n")
    assert len(lines) == 3
    for line in lines:
        assert line.startswith("  ")  # Each line has 2-space indent


def test_render_session_list_empty() -> None:
    """render_session_list shows message when no sessions exist."""
    output = render_session_list([])
    assert output == "No sessions found."


def test_render_session_list_single_session() -> None:
    """render_session_list formats a single session correctly."""
    ref = SessionRef(
        session_id="sess-abc",
        cwd="/path/to/project",
        last_modified=datetime(2026, 8, 15, 10, 30, 0, tzinfo=timezone.utc),
        git_branch=None,
        first_prompt_preview=None,
    )
    output = render_session_list([ref])
    assert "sess-abc" in output
    assert "2026-08-15T10:30:00+00:00" in output
    assert "/path/to/project" in output


def test_render_session_list_with_git_branch() -> None:
    """render_session_list includes git branch when present."""
    ref = SessionRef(
        session_id="sess-xyz",
        cwd="/repo",
        last_modified=datetime(2026, 8, 15, 12, 0, 0, tzinfo=timezone.utc),
        git_branch="feature/test",
        first_prompt_preview=None,
    )
    output = render_session_list([ref])
    assert "[feature/test]" in output


def test_render_session_list_without_git_branch() -> None:
    """render_session_list omits git branch when not set."""
    ref = SessionRef(
        session_id="sess-123",
        cwd="/repo",
        last_modified=datetime(2026, 8, 15, 12, 0, 0, tzinfo=timezone.utc),
        git_branch=None,
        first_prompt_preview=None,
    )
    output = render_session_list([ref])
    assert "[" not in output or "[]" not in output


def test_render_session_list_handles_missing_modified_time() -> None:
    """render_session_list shows 'unknown' when last_modified is None."""
    ref = SessionRef(
        session_id="sess-old",
        cwd="/old/path",
        last_modified=None,
        git_branch=None,
        first_prompt_preview=None,
    )
    output = render_session_list([ref])
    assert "unknown" in output
    assert "sess-old" in output


def test_render_session_list_multiple_sessions() -> None:
    """render_session_list formats multiple sessions, one per line."""
    refs = [
        SessionRef(
            session_id="sess-1",
            cwd="/path1",
            last_modified=datetime(2026, 8, 15, 10, 0, 0, tzinfo=timezone.utc),
            git_branch="main",
            first_prompt_preview=None,
        ),
        SessionRef(
            session_id="sess-2",
            cwd="/path2",
            last_modified=datetime(2026, 8, 15, 11, 0, 0, tzinfo=timezone.utc),
            git_branch=None,
            first_prompt_preview=None,
        ),
    ]
    output = render_session_list(refs)
    lines = output.split("\n")
    assert len(lines) == 2
    assert "sess-1" in lines[0]
    assert "sess-2" in lines[1]


def test_render_session_warning_contains_all_key_elements() -> None:
    """render_session_warning includes all required warning elements."""
    ref = SessionRef(
        session_id="sess-warned",
        cwd="/project",
        last_modified=datetime(2026, 8, 15, 14, 30, 0, tzinfo=timezone.utc),
        git_branch="develop",
        first_prompt_preview="Implement feature X",
    )
    output = render_session_warning(ref, cwd="/project")
    assert "WARNING" in output
    assert "sess-warned" in output
    # render_session_warning interpolates the datetime with str(), not
    # isoformat() -- space-separated, not "T"-separated.
    assert "2026-08-15 14:30:00+00:00" in output
    assert "develop" in output
    assert "Implement feature X" in output
    assert "/project" in output
    assert "Ctrl-C" in output


def test_render_session_warning_has_banner_lines() -> None:
    """render_session_warning starts and ends with banner of exclamation marks."""
    ref = SessionRef(
        session_id="sess-test",
        cwd="/test",
        last_modified=datetime.now(timezone.utc),
        git_branch=None,
        first_prompt_preview=None,
    )
    output = render_session_warning(ref, cwd="/test")
    lines = output.split("\n")
    # First and last lines should be 78 exclamation marks
    assert lines[0] == "!" * 78
    assert lines[-1] == "!" * 78


def test_render_session_warning_without_git_branch() -> None:
    """render_session_warning omits git branch line when not set."""
    ref = SessionRef(
        session_id="sess-no-git",
        cwd="/nogit",
        last_modified=datetime.now(timezone.utc),
        git_branch=None,
        first_prompt_preview=None,
    )
    output = render_session_warning(ref, cwd="/nogit")
    assert "git branch" not in output


def test_render_session_warning_with_git_branch() -> None:
    """render_session_warning includes git branch line when set."""
    ref = SessionRef(
        session_id="sess-git",
        cwd="/git",
        last_modified=datetime.now(timezone.utc),
        git_branch="feature/new",
        first_prompt_preview=None,
    )
    output = render_session_warning(ref, cwd="/git")
    assert "git branch      : feature/new" in output


def test_render_session_warning_without_prompt_preview() -> None:
    """render_session_warning omits first prompt line when not set."""
    ref = SessionRef(
        session_id="sess-no-prompt",
        cwd="/np",
        last_modified=datetime.now(timezone.utc),
        git_branch=None,
        first_prompt_preview=None,
    )
    output = render_session_warning(ref, cwd="/np")
    assert "first prompt" not in output


def test_render_session_warning_with_prompt_preview() -> None:
    """render_session_warning includes first prompt line when set."""
    ref = SessionRef(
        session_id="sess-prompt",
        cwd="/p",
        last_modified=datetime.now(timezone.utc),
        git_branch=None,
        first_prompt_preview="Fix bug in auth",
    )
    output = render_session_warning(ref, cwd="/p")
    assert "first prompt    : Fix bug in auth" in output
