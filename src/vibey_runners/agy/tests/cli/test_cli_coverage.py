# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from agyloop.application.dto import RunResult
from agyloop.application.usecases.doctor import DoctorCheck
from agyloop.cli.app import main
from agyloop.cli.render import render_classification, render_session_list
from agyloop.domain.capacity import WindowExhausted
from agyloop.domain.classify import Classification
from agyloop.domain.errors import (
    InvalidPlanError,
    InvalidSessionSelectorError,
)
from agyloop.domain.session import SessionRef
from agyloop.infrastructure.rundir import RunDirectory, runs_root_for
from tests.test_cli import _invoke


def test_main_invokes_app() -> None:
    with patch("agyloop.cli.app.app") as mock_app:
        main()
        mock_app.assert_called_once_with(prog_name="agyloop")


def test_attach_and_unattach(tmp_path: Path) -> None:
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello", encoding="utf-8")

    # Error when run directory does not exist
    res = _invoke("attach", str(test_file), "--cwd", str(tmp_path), "--run-id", "r1")
    assert res.exit_code == 1
    assert "not an agyloop run directory" in res.output or "No such run" in res.output

    res = _invoke("unattach", "test.txt", "--cwd", str(tmp_path), "--run-id", "r1")
    assert res.exit_code == 1

    # Create run directory
    directory = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    run_id = directory.read_meta().run_id

    res = _invoke("attach", str(test_file), "--cwd", str(tmp_path), "--run-id", run_id)
    assert res.exit_code == 0
    assert "Queued attach" in res.output

    res = _invoke("unattach", "test.txt", "--cwd", str(tmp_path), "--run-id", run_id)
    assert res.exit_code == 0
    assert "Queued unattach" in res.output


def test_status_file_not_found(tmp_path: Path) -> None:
    res = _invoke("status", "--cwd", str(tmp_path), "--run-id", "nonexistent")
    assert res.exit_code == 1
    assert "not an agyloop run directory" in res.output or "No such run" in res.output


def test_runs_and_sessions_empty(tmp_path: Path) -> None:
    with patch("agyloop.infrastructure.rundir.list_run_directories", return_value=[]):
        res = _invoke("runs", "--cwd", str(tmp_path))
        assert res.exit_code == 0
        assert "No runs found." in res.output

    with patch("agyloop.cli.commands.sessions.list_sessions", return_value=[]):
        res = _invoke("sessions", "--cwd", str(tmp_path))
        assert res.exit_code == 0
        assert "No agyloop runs found" in res.output

    # Test sessions callback when invoked_subcommand is not None
    mock_ctx = MagicMock()
    mock_ctx.invoked_subcommand = "sub"
    from agyloop.cli.commands.sessions import sessions as sessions_cb

    sessions_cb(mock_ctx, cwd=str(tmp_path))


def test_snapshot_no_bundle_path(tmp_path: Path) -> None:
    mock_ref = MagicMock()
    mock_ref.path = tmp_path / "actual_snap.json"
    mock_ref.digest = "sha256:abcd"
    mock_ref.bundle_path = None

    with patch("agyloop.bootstrap.emit_snapshot", return_value=mock_ref):
        res = _invoke("snapshot", "--cwd", str(tmp_path))
        assert res.exit_code == 0
        assert "bundle_path:" not in res.output


def test_resume_command_all_branches(tmp_path: Path) -> None:
    # Invalid gateway
    res = _invoke("resume", "--gateway", "invalid_gateway", "--cwd", str(tmp_path))
    assert res.exit_code == 1
    assert "unknown gateway" in res.output.lower()

    # Invalid session selector
    with patch(
        "agyloop.cli.commands.resume.resolve_last_run",
        side_effect=InvalidSessionSelectorError("no sessions"),
    ):
        res = _invoke("resume", "--last", "--cwd", str(tmp_path))
        assert res.exit_code == 1

    mock_context = MagicMock()
    mock_context.run_id = "r123"
    mock_context.runner = AsyncMock()

    # Explicit conversation ID without --last
    mock_success = RunResult(
        success=True, reason="completed", session_id="s1", turns_spent=1, dollars_spent=0.5
    )
    with (
        patch("agyloop.bootstrap.build_runner", return_value=mock_context),
        patch(
            "agyloop.cli.commands.resume.resume_explicit",
            new_callable=AsyncMock,
            return_value=mock_success,
        ),
    ):
        res = _invoke("resume", "--conversation", "c123", "--cwd", str(tmp_path))
        assert res.exit_code == 0
        assert "Done: completed" in res.output

    # No conversation ID (conversation is None) with default or --last
    mock_ref = SessionRef(
        session_id="last_s1",
        cwd=str(tmp_path),
        last_modified=datetime.now(UTC),
        first_prompt_preview="prompt",
    )
    with (
        patch("agyloop.cli.commands.resume.resolve_last_run", return_value=mock_ref),
        patch("agyloop.bootstrap.build_runner", return_value=mock_context),
        patch(
            "agyloop.cli.commands.resume.resume_explicit",
            new_callable=AsyncMock,
            return_value=mock_success,
        ),
    ):
        res = _invoke("resume", "--cwd", str(tmp_path))
        assert res.exit_code == 0
        assert "Done: completed" in res.output

    # Explicit conversation ID WITH --last
    with (
        patch("agyloop.cli.commands.resume.resolve_last_run", return_value=mock_ref),
        patch("agyloop.bootstrap.build_runner", return_value=mock_context),
        patch(
            "agyloop.cli.commands.resume.resume_explicit",
            new_callable=AsyncMock,
            return_value=mock_success,
        ),
    ):
        res = _invoke("resume", "--conversation", "c123", "--last", "--cwd", str(tmp_path))
        assert res.exit_code == 0
        assert "Done: completed" in res.output

    # Resume failure result
    failed_result = RunResult(
        success=False, reason="session dead", session_id="s1", turns_spent=1, dollars_spent=0.5
    )
    with (
        patch("agyloop.bootstrap.build_runner", return_value=mock_context),
        patch(
            "agyloop.cli.commands.resume.resume_explicit",
            new_callable=AsyncMock,
            return_value=failed_result,
        ),
    ):
        res = _invoke("resume", "--conversation", "c123", "--cwd", str(tmp_path))
        assert res.exit_code == 1
        assert "Run failed: session dead" in res.output


def test_logs_command(tmp_path: Path) -> None:
    # Error when run not found
    res = _invoke("logs", "--cwd", str(tmp_path), "--run-id", "r1")
    assert res.exit_code == 1

    directory = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    run_id = directory.read_meta().run_id

    with patch("agyloop.bootstrap.tail_events") as mock_tail:
        res = _invoke("logs", "--cwd", str(tmp_path), "--run-id", run_id, "--chatter")
        assert res.exit_code == 0
        mock_tail.assert_called_once_with(
            tmp_path.resolve(), run_id=run_id, follow=False, chatter_only=True
        )

    with patch("agyloop.bootstrap.tail_events", side_effect=KeyboardInterrupt):
        res = _invoke("logs", "--cwd", str(tmp_path), "--run-id", run_id)
        assert res.exit_code == 0


def test_model_and_preset_errors(tmp_path: Path) -> None:
    # Error when run not found
    res = _invoke("model", "gemini-2.5-pro", "--cwd", str(tmp_path), "--run-id", "r1")
    assert res.exit_code == 1

    res = _invoke("preset", "high", "--cwd", str(tmp_path), "--run-id", "r1")
    assert res.exit_code == 1

    # Create run directory and test invalid preset
    directory = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    run_id = directory.read_meta().run_id

    res = _invoke("preset", "invalid_preset", "--cwd", str(tmp_path), "--run-id", run_id)
    assert res.exit_code == 1

    # Valid preset
    res = _invoke("preset", "high", "--cwd", str(tmp_path), "--run-id", run_id)
    assert res.exit_code == 0
    assert "Queued set_preset" in res.output


def test_watch_command(tmp_path: Path) -> None:
    # Error when run not found
    res = _invoke("watch", "--cwd", str(tmp_path), "--run-id", "r1")
    assert res.exit_code == 1

    directory = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    run_id = directory.read_meta().run_id

    with patch("agyloop.bootstrap.watch_bus") as mock_watch:
        res = _invoke("watch", "--cwd", str(tmp_path), "--run-id", run_id, "--no-follow")
        assert res.exit_code == 0
        mock_watch.assert_called_once_with(tmp_path.resolve(), run_id=run_id, follow=False)

    with patch("agyloop.bootstrap.watch_bus", side_effect=KeyboardInterrupt):
        res = _invoke("watch", "--cwd", str(tmp_path), "--run-id", run_id)
        assert res.exit_code == 0

    with patch("agyloop.bootstrap.watch_bus", side_effect=RuntimeError("bus error")):
        res = _invoke("watch", "--cwd", str(tmp_path), "--run-id", run_id)
        assert res.exit_code == 1

    with patch("agyloop.bootstrap.run_stream_ui") as mock_ui:
        res = _invoke("watch", "--cwd", str(tmp_path), "--run-id", run_id, "--stream")
        assert res.exit_code == 0
        mock_ui.assert_called_once_with(
            tmp_path.resolve(), run_id=run_id, follow=True, replay=False, speed=1.0
        )


def test_savepoints_command(tmp_path: Path) -> None:
    # Error when run not found
    res = _invoke("savepoints", "--cwd", str(tmp_path), "--run-id", "r1")
    assert res.exit_code == 1

    with patch("agyloop.bootstrap.list_savepoints", return_value=[]):
        res = _invoke("savepoints", "--cwd", str(tmp_path))
        assert res.exit_code == 0
        assert "No save points." in res.output

    mock_points = [
        {
            "n": 1,
            "sha": "1234567890abcdef",
            "label": "turn-1",
            "at": "2026-08-13T12:00:00Z",
            "ref": "refs/agyloop/savepoints/1",
        }
    ]
    with patch("agyloop.bootstrap.list_savepoints", return_value=mock_points):
        res = _invoke("savepoints", "--cwd", str(tmp_path))
        assert res.exit_code == 0
        assert "#1" in res.output
        assert "1234567890ab" in res.output


def test_snapshot_command(tmp_path: Path) -> None:
    # Error when run not found
    res = _invoke("snapshot", "--cwd", str(tmp_path), "--run-id", "r1")
    assert res.exit_code == 1

    out_file = tmp_path / "snap.json"
    mock_ref = MagicMock()
    mock_ref.path = tmp_path / "actual_snap.json"
    mock_ref.digest = "sha256:abcd"
    mock_ref.bundle_path = tmp_path / "bundle.tar.gz"

    with patch("agyloop.bootstrap.emit_snapshot", return_value=mock_ref):
        res = _invoke("snapshot", "--cwd", str(tmp_path), "--out", str(out_file))
        assert res.exit_code == 0
        assert "snapshot_path:" in res.output
        assert "snapshot_digest:" in res.output
        assert "bundle_path:" in res.output
        assert "copied_to:" in res.output


def test_unwind_command(tmp_path: Path) -> None:
    # Error when run not found
    res = _invoke("unwind", "--to", "1", "--cwd", str(tmp_path), "--run-id", "r1")
    assert res.exit_code == 1

    with patch(
        "agyloop.bootstrap.unwind_savepoint",
        return_value={
            "to_n": 1,
            "restored_sha": "abcdef1234567890",
            "backup_ref": "refs/heads/backup",
        },
    ):
        res = _invoke("unwind", "--to", "1", "--cwd", str(tmp_path))
        assert res.exit_code == 0
        assert "Restored save point #1" in res.output
        assert "Backup ref:" in res.output

    with patch(
        "agyloop.bootstrap.unwind_savepoint",
        return_value={"to_n": 1, "restored_sha": "abcdef1234567890", "backup_ref": None},
    ):
        res = _invoke("unwind", "--to", "1", "--cwd", str(tmp_path))
        assert res.exit_code == 0
        assert "Restored save point #1" in res.output


def test_doctor_command_failing_and_subcommand(tmp_path: Path) -> None:
    failing_check = DoctorCheck(name="auth", passed=False, detail="missing key")
    with (
        patch("agyloop.bootstrap.build_doctor_environment"),
        patch("agyloop.application.usecases.doctor.run_doctor", return_value=[failing_check]),
    ):
        res = _invoke("doctor")
        assert res.exit_code == 1
        assert "[FAIL]" in res.output

    with patch("agyloop.bootstrap.repair_harness", return_value="harness repaired"):
        res = _invoke("doctor", "repair-harness")
        assert res.exit_code == 0
        assert "harness repaired" in res.output

    res = _invoke(
        "doctor",
        "explain-classify",
        "--retry-after",
        "10",
        "--error-code",
        "rate_limit_exceeded",
        "--exception-type",
        "ResourceExhausted",
        "--quota-metric",
        "rpm",
    )
    assert res.exit_code == 0
    assert "rung=" in res.output


def test_run_command_failure_and_invalid_gateway(tmp_path: Path) -> None:
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("# Plan", encoding="utf-8")

    # Invalid gateway
    res = _invoke("run", str(plan_file), "--gateway", "invalid_gateway", "--cwd", str(tmp_path))
    assert res.exit_code == 1
    assert "unknown gateway" in res.output.lower()

    # Invalid plan file
    with patch(
        "agyloop.cli.commands.run.parse_plan_file", side_effect=InvalidPlanError("bad plan")
    ):
        res = _invoke("run", str(plan_file), "--cwd", str(tmp_path))
        assert res.exit_code == 1
        assert "Invalid plan file" in res.output

    # Run failure result
    failed_result = RunResult(
        success=False, reason="budget blown", session_id="s1", turns_spent=1, dollars_spent=0.5
    )
    with patch(
        "agyloop.cli.commands.run.run_from_plan_file",
        new_callable=AsyncMock,
        return_value=failed_result,
    ):
        res = _invoke("run", str(plan_file), "--cwd", str(tmp_path))
        assert res.exit_code == 1
        assert "Run failed: budget blown" in res.output


def test_render_classification_and_session_list() -> None:
    # Classification with rate_limit_type and resets_at
    reset_dt = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)
    state = WindowExhausted(rate_limit_type="rpm", resets_at=reset_dt)
    classification = Classification(state=state, rung="rpm")
    rendered = render_classification(classification)
    assert "rate_limit_type=rpm" in rendered
    assert "resets_at=" in rendered

    # Session list empty vs non-empty
    assert "No agyloop runs found" in render_session_list([])

    ref = SessionRef(
        session_id="s1",
        cwd="/tmp",
        last_modified=datetime(2026, 8, 13, 12, 0, tzinfo=UTC),
        first_prompt_preview="hello world",
    )
    rendered_sessions = render_session_list([ref])
    assert "s1" in rendered_sessions
    assert "hello world" in rendered_sessions
