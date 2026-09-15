# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for cli/commands/resume.py — resume command error and success paths."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from typer.testing import CliRunner

from claudeloop.cli.app import app

runner = CliRunner()
_ENV = {"NO_COLOR": "1", "TERM": "dumb"}


class TestResumeSuccess:
    def test_resume_with_session_id(self, tmp_path: Path) -> None:
        mock_context = MagicMock()
        mock_context.run_id = "test-run-1"
        mock_context.trace_id = "test-trace-1"
        mock_context.run_dir = MagicMock()

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.reason = "done"

        with (
            patch("claudeloop.cli.commands.resume.load_config") as mock_config,
            patch("claudeloop.cli.commands.resume.configure_logging"),
            patch("claudeloop.cli.commands.resume.bootstrap") as mock_bootstrap,
            patch(
                "claudeloop.cli.commands.resume.resume_explicit", new_callable=AsyncMock
            ) as mock_resume,
        ):
            mock_config.return_value = MagicMock(
                log_file=None,
                log_level="INFO",
                done_marker=None,
            )
            mock_bootstrap.build_runner.return_value = mock_context
            mock_resume.return_value = mock_result

            result = runner.invoke(
                app,
                ["resume", "--session-id", "sess-123"],
                env=_ENV,
            )
            assert result.exit_code == 0
            assert "Done:" in result.output

    def test_resume_failure(self, tmp_path: Path) -> None:
        mock_context = MagicMock()
        mock_context.run_id = "test-run-1"
        mock_context.trace_id = "test-trace-1"
        mock_context.run_dir = MagicMock()

        mock_result = MagicMock()
        mock_result.success = False
        mock_result.reason = "credits exhausted"

        with (
            patch("claudeloop.cli.commands.resume.load_config") as mock_config,
            patch("claudeloop.cli.commands.resume.configure_logging"),
            patch("claudeloop.cli.commands.resume.bootstrap") as mock_bootstrap,
            patch(
                "claudeloop.cli.commands.resume.resume_explicit", new_callable=AsyncMock
            ) as mock_resume,
        ):
            mock_config.return_value = MagicMock(
                log_file=None,
                log_level="INFO",
                done_marker=None,
            )
            mock_bootstrap.build_runner.return_value = mock_context
            mock_resume.return_value = mock_result

            result = runner.invoke(
                app,
                ["resume", "--session-id", "sess-123"],
                env=_ENV,
            )
            assert result.exit_code == 1

    def test_resume_stopped(self, tmp_path: Path) -> None:
        mock_context = MagicMock()
        mock_context.run_id = "test-run-1"
        mock_context.trace_id = "test-trace-1"
        mock_context.run_dir = MagicMock()

        mock_result = MagicMock()
        mock_result.success = False
        mock_result.reason = "stopped by operator"

        with (
            patch("claudeloop.cli.commands.resume.load_config") as mock_config,
            patch("claudeloop.cli.commands.resume.configure_logging"),
            patch("claudeloop.cli.commands.resume.bootstrap") as mock_bootstrap,
            patch(
                "claudeloop.cli.commands.resume.resume_explicit", new_callable=AsyncMock
            ) as mock_resume,
        ):
            mock_config.return_value = MagicMock(
                log_file=None,
                log_level="INFO",
                done_marker=None,
            )
            mock_bootstrap.build_runner.return_value = mock_context
            mock_resume.return_value = mock_result

            result = runner.invoke(
                app,
                ["resume", "--session-id", "sess-123"],
                env=_ENV,
            )
            assert result.exit_code == 130

    def test_resume_auto_resolve_no_sessions(self) -> None:
        from claudeloop.domain.errors import InvalidSessionSelectorError

        with (
            patch("claudeloop.cli.commands.resume.load_config") as mock_config,
            patch("claudeloop.cli.commands.resume.configure_logging"),
            patch("claudeloop.cli.commands.resume.bootstrap") as mock_bootstrap,
            patch("claudeloop.cli.commands.resume.resolve_most_recent") as mock_resolve,
        ):
            mock_config.return_value = MagicMock(
                log_file=None,
                log_level="INFO",
                done_marker=None,
            )
            mock_bootstrap.build_session_catalog.return_value = MagicMock()
            mock_resolve.side_effect = InvalidSessionSelectorError("no sessions")

            result = runner.invoke(
                app,
                ["resume"],
                env=_ENV,
            )
            assert result.exit_code == 1
            assert "no sessions" in result.output

    def test_resume_auto_resolve_success(self, tmp_path: Path) -> None:
        """No --session-id and a resolvable session: prints the "most
        recent session" warning banner, then resumes it (lines 113-114)."""
        from datetime import datetime, timezone

        from claudeloop.domain.session import SessionRef

        mock_context = MagicMock()
        mock_context.run_id = "test-run-1"
        mock_context.trace_id = "test-trace-1"
        mock_context.run_dir = MagicMock()

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.reason = "done"

        ref = SessionRef(
            session_id="resolved-session",
            cwd=str(tmp_path),
            last_modified=datetime.now(timezone.utc),
        )

        with (
            patch("claudeloop.cli.commands.resume.load_config") as mock_config,
            patch("claudeloop.cli.commands.resume.configure_logging"),
            patch("claudeloop.cli.commands.resume.bootstrap") as mock_bootstrap,
            patch("claudeloop.cli.commands.resume.resolve_most_recent") as mock_resolve,
            patch(
                "claudeloop.cli.commands.resume.resume_explicit", new_callable=AsyncMock
            ) as mock_resume,
        ):
            mock_config.return_value = MagicMock(
                log_file=None,
                log_level="INFO",
                done_marker=None,
            )
            mock_bootstrap.build_session_catalog.return_value = MagicMock()
            mock_resolve.return_value = ref
            mock_bootstrap.build_runner.return_value = mock_context
            mock_resume.return_value = mock_result

            result = runner.invoke(
                app,
                ["resume"],
                env=_ENV,
            )
            assert result.exit_code == 0
            assert "WARNING" in result.output
            assert "resolved-session" in result.output
            assert "Done:" in result.output


class TestResumeStreamUi:
    def test_resume_stream_ui_thread_runs_and_handles_runtime_error(self, tmp_path: Path) -> None:
        """--stream-ui spawns a daemon thread that runs the Textual app and
        swallows a RuntimeError (e.g. no TTY) — lines 129-144."""
        import threading as real_threading

        mock_context = MagicMock()
        mock_context.run_id = "test-run-1"
        mock_context.trace_id = "test-trace-1"
        mock_context.run_dir = MagicMock()
        mock_context.run_dir.events_path = tmp_path / "events.jsonl"

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.reason = "done"

        class _SyncThread:
            def __init__(self, target=None, daemon=None) -> None:
                self._target = target

            def start(self) -> None:
                if self._target is not None:
                    self._target()

        with (
            patch("claudeloop.cli.commands.resume.load_config") as mock_config,
            patch("claudeloop.cli.commands.resume.configure_logging"),
            patch("claudeloop.cli.commands.resume.bootstrap") as mock_bootstrap,
            patch(
                "claudeloop.cli.commands.resume.resume_explicit", new_callable=AsyncMock
            ) as mock_resume,
            patch(
                "claudeloop.cli.commands.resume.run_textual_app",
                side_effect=RuntimeError("no tty available"),
            ),
            patch.object(real_threading, "Thread", _SyncThread),
        ):
            mock_config.return_value = MagicMock(
                log_file=None,
                log_level="INFO",
                done_marker=None,
            )
            mock_bootstrap.build_runner.return_value = mock_context
            mock_resume.return_value = mock_result

            result = runner.invoke(
                app,
                ["resume", "--session-id", "sess-123", "--stream-ui"],
                env=_ENV,
            )
            assert result.exit_code == 0
            assert "no tty available" in result.output


class TestResumeErrors:
    def test_resume_invalid_wind_down_at(self) -> None:
        result = runner.invoke(
            app,
            ["resume", "--session-id", "sess-123", "--wind-down-at", "not-a-valid-time"],
            env=_ENV,
        )
        assert result.exit_code == 2
        assert "Invalid --wind-down-at" in result.output
