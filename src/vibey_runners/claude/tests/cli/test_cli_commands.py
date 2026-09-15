# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for CLI command modules — operator control commands.

Tests the thin Typer wrappers around bootstrap_ops, ensuring correct argument
routing and error handling without needing a live run.
"""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from claudeloop.cli.app import app

runner = CliRunner()
_ENV = {"NO_COLOR": "1", "TERM": "dumb", "FORCE_COLOR": "0"}


def _run_dir(tmp_path: Path):
    from claudeloop.infrastructure.rundir import RunDirectory, runs_root_for

    return RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)


class TestStopCommand:
    def test_stop_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(app, ["stop", "--run-id", run_id], env=_ENV)
        assert result.exit_code == 0
        assert "Stop requested" in result.output

    def test_stop_no_run_found(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["stop", "--run-id", "nonexistent"], env=_ENV)
        assert result.exit_code == 1


class TestPromptCommand:
    def test_prompt_needs_now_or_at_break(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["prompt", "hello"], env=_ENV)
        assert result.exit_code == 2
        assert "Specify exactly one" in result.output

    def test_prompt_both_now_and_at_break(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["prompt", "hello", "--now", "--at-break"],
            env=_ENV,
        )
        assert result.exit_code == 2

    def test_prompt_now_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(
            app,
            ["prompt", "hello", "--now", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0
        assert "Enqueued" in result.output

    def test_prompt_at_break(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(
            app,
            ["prompt", "hello", "--at-break", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0


class TestModelCommand:
    def test_model_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(app, ["model", "high", "--run-id", run_id], env=_ENV)
        assert result.exit_code == 0
        assert "set_model" in result.output

    def test_model_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["model", "high", "--run-id", "x"], env=_ENV)
        assert result.exit_code == 1


class TestEffortCommand:
    def test_effort_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(app, ["effort", "max", "--run-id", run_id], env=_ENV)
        assert result.exit_code == 0
        assert "set_effort" in result.output


class TestPresetCommand:
    def test_preset_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(app, ["preset", "high", "--run-id", run_id], env=_ENV)
        assert result.exit_code == 0
        assert "set_preset" in result.output


class TestSlashCommand:
    def test_slash_without_prefix_fails(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["slash", "no-prefix"], env=_ENV)
        assert result.exit_code == 2
        assert "must start with '/'" in result.output

    def test_slash_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(
            app,
            ["slash", "/help", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0
        assert "slash" in result.output.lower()

    def test_slash_no_run_found(self, tmp_path: Path, monkeypatch) -> None:
        """No matching run directory raises FileNotFoundError -> exit 1."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["slash", "/help", "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1


class TestWindDownCommand:
    def test_wind_down_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(
            app,
            ["wind-down", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0
        assert "Wind-down requested" in result.output

    def test_wind_down_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["wind-down", "--run-id", "nope"], env=_ENV)
        assert result.exit_code == 1


class TestLogsCommand:
    def test_logs_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["logs", "--run-id", "missing"], env=_ENV)
        assert result.exit_code == 1


class TestStatusCommand:
    def test_status_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(app, ["status", "--run-id", run_id], env=_ENV)
        assert result.exit_code == 0

    def test_status_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["status", "--run-id", "nope"], env=_ENV)
        assert result.exit_code == 1


class TestResetCommand:
    def test_reset_without_yes_fails(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["reset"], env=_ENV)
        assert result.exit_code == 1

    def test_reset_with_yes(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        # _run_dir defaults to status="active" with this test process's own
        # (live) pid, which is exactly the case reset_project_state refuses --
        # a --yes reset never overrides a live run. Mark it finished first.
        directory = _run_dir(tmp_path)
        directory.update_meta(status="finished")
        result = runner.invoke(app, ["reset", "--yes"], env=_ENV)
        assert result.exit_code == 0
        assert "Removed" in result.output


class TestRunsCommand:
    def test_runs_no_runs(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["runs"], env=_ENV)
        assert result.exit_code == 0
        assert "No runs" in result.output

    def test_runs_with_runs(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(app, ["runs"], env=_ENV)
        assert result.exit_code == 0
        assert run_id in result.output


class TestSessionsCommand:
    def test_sessions_no_sessions(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["sessions"], env=_ENV)
        assert result.exit_code == 0

    def test_sessions_returns_early_when_subcommand_invoked(self) -> None:
        """The callback exits before touching the catalog when a subcommand
        is already dispatching (invoke_without_command guard)."""
        import click

        from claudeloop.cli.commands.sessions import sessions

        ctx = click.Context(click.Command("sessions"))
        ctx.invoked_subcommand = "something"
        assert sessions(ctx, cwd=None) is None


class TestSavepointsCommand:
    def test_savepoints_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["savepoints", "--run-id", "nope"], env=_ENV)
        assert result.exit_code == 1

    def test_savepoints_empty(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(app, ["savepoints", "--run-id", run_id], env=_ENV)
        assert result.exit_code == 0
        assert "No save points" in result.output

    def test_savepoints_prints_each_point(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        import claudeloop.cli.commands.savepoints as savepoints_mod

        monkeypatch.setattr(
            savepoints_mod.bootstrap_ops,
            "list_savepoints",
            lambda cwd, run_id=None: [
                {
                    "n": 1,
                    "sha": "abcdef1234567890",
                    "label": "checkpoint",
                    "at": "2024-01-01T00:00:00",
                    "ref": "refs/claudeloop/savepoints/1",
                }
            ],
        )
        result = runner.invoke(app, ["savepoints", "--run-id", run_id], env=_ENV)
        assert result.exit_code == 0
        assert "#1" in result.output
        assert "checkpoint" in result.output
        assert "abcdef123456" in result.output


class TestUnwindCommand:
    def test_unwind_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["unwind", "--to", "1", "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1

    def test_unwind_success_with_backup(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        directory.update_meta(status="finished")
        run_id = directory.read_meta().run_id
        import claudeloop.cli.commands.unwind as unwind_mod

        monkeypatch.setattr(
            unwind_mod.bootstrap_ops,
            "unwind_savepoint",
            lambda cwd, to, *, backup=True, run_id=None: {
                "to_n": 1,
                "to_sha": "abc123456789",
                "backup_ref": "refs/claudeloop/backups/1",
                "restored_sha": "abc123456789",
            },
        )
        result = runner.invoke(app, ["unwind", "--to", "1", "--run-id", run_id], env=_ENV)
        assert result.exit_code == 0
        assert "Restored save point #1" in result.output
        assert "Backup ref:" in result.output

    def test_unwind_success_without_backup(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        directory.update_meta(status="finished")
        run_id = directory.read_meta().run_id
        import claudeloop.cli.commands.unwind as unwind_mod

        monkeypatch.setattr(
            unwind_mod.bootstrap_ops,
            "unwind_savepoint",
            lambda cwd, to, *, backup=True, run_id=None: {
                "to_n": 1,
                "to_sha": "abc123456789",
                "backup_ref": None,
                "restored_sha": "abc123456789",
            },
        )
        result = runner.invoke(
            app,
            ["unwind", "--to", "1", "--run-id", run_id, "--no-backup"],
            env=_ENV,
        )
        assert result.exit_code == 0
        assert "Restored save point #1" in result.output
        assert "Backup ref:" not in result.output


class TestChatCommands:
    def test_chat_list_empty(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["chat", "list"], env=_ENV)
        assert result.exit_code == 0
        assert "No chats" in result.output

    def test_chat_show(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["chat", "show", "test-session"], env=_ENV)
        assert result.exit_code == 0

    def test_chat_rename(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["chat", "rename", "s1", "new-name"], env=_ENV)
        assert result.exit_code == 0
        assert "Renamed" in result.output

    def test_chat_delete_missing(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["chat", "delete", "nonexistent"], env=_ENV)
        assert result.exit_code == 1

    def test_chat_pin_unpin(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["chat", "pin", "s1"], env=_ENV)
        assert result.exit_code == 0
        result = runner.invoke(app, ["chat", "unpin", "s1"], env=_ENV)
        assert result.exit_code == 0

    def test_chat_unread_read(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["chat", "unread", "s1"], env=_ENV)
        assert result.exit_code == 0
        result = runner.invoke(app, ["chat", "read", "s1"], env=_ENV)
        assert result.exit_code == 0

    def test_chat_project(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["chat", "project", "s1", "my-project"],
            env=_ENV,
        )
        assert result.exit_code == 0
        assert "project" in result.output.lower()


class TestConnectorCommands:
    def test_connector_add_url(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(
            app,
            ["connector", "add", "myconn", "http://localhost", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0

    def test_connector_add_invalid_json(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(
            app,
            ["connector", "add", "myconn", "{bad", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 2

    def test_connector_rm(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(
            app,
            ["connector", "rm", "myconn", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0

    def test_connector_list_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["connector", "list", "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1


class TestToolCommands:
    def test_tool_approve_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["tool", "approve", "req-1", "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1

    def test_tool_deny_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["tool", "deny", "req-1", "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1


class TestVoiceCommands:
    def test_voice_start(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["voice", "start"], env=_ENV)
        assert result.exit_code == 1

    def test_voice_stop(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["voice", "stop"], env=_ENV)
        assert result.exit_code == 1

    def test_voice_status(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["voice", "status"], env=_ENV)
        assert result.exit_code == 0
        assert "not running" in result.output.lower()

    def test_speak_no_tts(self, tmp_path: Path, monkeypatch) -> None:
        import shutil as _shutil

        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(_shutil, "which", lambda _: None)
        result = runner.invoke(app, ["speak", "hello"], env=_ENV)
        assert result.exit_code == 1

    def test_speak_macos_say(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        import claudeloop.cli.commands.voice_cmd as voice_mod

        monkeypatch.setattr(voice_mod.sys, "platform", "darwin")
        monkeypatch.setattr(
            voice_mod.shutil, "which", lambda cmd: "/usr/bin/say" if cmd == "say" else None
        )
        calls: list[object] = []
        monkeypatch.setattr(voice_mod.subprocess, "run", lambda *a, **kw: calls.append((a, kw)))
        result = runner.invoke(app, ["speak", "hello"], env=_ENV)
        assert result.exit_code == 0
        assert calls
        assert calls[0][0][0] == ["say", "hello"]

    def test_speak_espeak_fallback(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        import claudeloop.cli.commands.voice_cmd as voice_mod

        monkeypatch.setattr(voice_mod.sys, "platform", "linux")
        monkeypatch.setattr(
            voice_mod.shutil,
            "which",
            lambda cmd: "/usr/bin/espeak" if cmd == "espeak" else None,
        )
        calls: list[object] = []
        monkeypatch.setattr(voice_mod.subprocess, "run", lambda *a, **kw: calls.append((a, kw)))
        result = runner.invoke(app, ["speak", "hello"], env=_ENV)
        assert result.exit_code == 0
        assert calls
        assert calls[0][0][0] == ["espeak", "hello"]


class TestAttachCommand:
    def test_attach_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        f = tmp_path / "note.txt"
        f.write_text("hi", encoding="utf-8")
        result = runner.invoke(
            app,
            ["attach", str(f), "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1

    def test_unattach_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["unattach", "note.txt", "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1


class TestFolderCommands:
    def test_folder_add_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["folder", "add", str(tmp_path), "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1

    def test_folder_rm_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["folder", "rm", str(tmp_path), "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1


class TestSkillCommands:
    def test_skill_add_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["skill", "add", "s1", "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1

    def test_skill_rm_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["skill", "rm", "s1", "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1


class TestPluginCommands:
    def test_plugin_add_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["plugin", "add", "p1", "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1

    def test_plugin_rm_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["plugin", "rm", "p1", "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1


class TestMemoryCommands:
    def test_memory_list_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["memory", "list", "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1

    def test_memory_get_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["memory", "get", "note1", "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1

    def test_memory_set_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["memory", "set", "note1", "body", "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1

    def test_memory_rm_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["memory", "rm", "note1", "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1


class TestGithubCommands:
    def test_github_add_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["github", "add", "owner/repo", "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1

    def test_github_import_issue_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["github", "import-issue", "owner/repo#1", "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1


class TestArtifactCommands:
    def test_artifact_list_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["artifact", "list", "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1

    def test_artifact_get_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["artifact", "get", "thing", "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1

    def test_artifact_rm_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["artifact", "rm", "thing", "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1


class TestResearchCommands:
    def test_research_start_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["research", "start", "query", "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1

    def test_research_status_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["research", "status", "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1


class TestWebSearchCommand:
    def test_web_search_enable_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["web-search", "enable", "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1

    def test_web_search_disable_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["web-search", "disable", "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1


class TestPermissionModeCommand:
    def test_permission_mode_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["permission-mode", "manual", "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1


class TestCwdCommand:
    def test_cwd_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["cwd", str(tmp_path), "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1


class TestResponseCommand:
    def test_response_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["response", "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code != 0


class TestDoctorCommand:
    def test_doctor_help(self) -> None:
        result = runner.invoke(app, ["doctor", "--help"], env=_ENV)
        assert result.exit_code == 0
        assert "Pre-flight" in result.output or "Usage" in result.output

    def test_doctor_returns_early_when_subcommand_invoked(self) -> None:
        import click

        from claudeloop.cli.commands.doctor import doctor

        ctx = click.Context(click.Command("doctor"))
        ctx.invoked_subcommand = "something"
        assert doctor(ctx) is None

    def test_doctor_all_checks_pass(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        import claudeloop.cli.commands.doctor as doctor_mod
        from claudeloop.application.usecases.doctor import DoctorCheck

        monkeypatch.setattr(doctor_mod.bootstrap, "build_doctor_environment", lambda: object())
        monkeypatch.setattr(
            doctor_mod,
            "run_doctor",
            lambda env, cwd: [DoctorCheck(name="claude-cli", passed=True, detail="ok")],
        )
        result = runner.invoke(app, ["doctor"], env=_ENV)
        assert result.exit_code == 0

    def test_doctor_failing_check_exits_nonzero(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        import claudeloop.cli.commands.doctor as doctor_mod
        from claudeloop.application.usecases.doctor import DoctorCheck

        monkeypatch.setattr(doctor_mod.bootstrap, "build_doctor_environment", lambda: object())
        monkeypatch.setattr(
            doctor_mod,
            "run_doctor",
            lambda env, cwd: [DoctorCheck(name="claude-cli", passed=False, detail="missing")],
        )
        result = runner.invoke(app, ["doctor"], env=_ENV)
        assert result.exit_code == 1


class TestResumeCommand:
    def test_resume_help(self) -> None:
        result = runner.invoke(app, ["resume", "--help"], env=_ENV)
        assert result.exit_code == 0
        assert "session" in result.output.lower()


class TestRunCommand:
    def test_run_help(self) -> None:
        result = runner.invoke(app, ["run", "--help"], env=_ENV)
        assert result.exit_code == 0
        assert "plan" in result.output.lower() or "Usage" in result.output

    def test_run_nonexistent_plan(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["run", "nonexistent.md"], env=_ENV)
        assert result.exit_code == 2


class TestConnectorAddSuccess:
    def test_connector_add_json(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(
            app,
            ["connector", "add", "myconn", '{"url":"http://x"}', "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0
        assert "Queued" in result.output

    def test_connector_list_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(
            app,
            ["connector", "list", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0


class TestResponseSubcommands:
    def test_response_copy_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["response", "copy", "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1

    def test_response_good_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["response", "good", "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1

    def test_response_bad_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["response", "bad", "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1

    def test_response_retry_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["response", "retry", "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1

    def test_response_good_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(
            app,
            ["response", "good", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0
        assert "good feedback" in result.output.lower()

    def test_response_bad_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(
            app,
            ["response", "bad", "--note", "needs fix", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0
        assert "bad feedback" in result.output.lower()

    def test_response_retry_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(
            app,
            ["response", "retry", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0
        assert "retry" in result.output.lower()


class TestLogsSuccess:
    def test_logs_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(app, ["logs", "--run-id", run_id], env=_ENV)
        assert result.exit_code == 0


class TestWatchCommand:
    def test_watch_sys_stdout_isatty(self) -> None:
        from claudeloop.cli.commands.watch import sys_stdout_isatty

        result = sys_stdout_isatty()
        assert isinstance(result, bool)

    def test_watch_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["watch", "--no-follow", "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1

    def test_watch_help(self) -> None:
        result = runner.invoke(app, ["watch", "--help"], env=_ENV)
        assert result.exit_code == 0
        assert "follow" in result.output.lower()

    def test_watch_stream_invokes_textual_app(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        import claudeloop.cli.commands.watch as watch_mod

        calls: dict[str, object] = {}

        def fake_run_textual_app(*, events_path, follow, replay, speed):
            calls["events_path"] = events_path
            calls["follow"] = follow
            calls["replay"] = replay
            calls["speed"] = speed

        monkeypatch.setattr(watch_mod, "run_textual_app", fake_run_textual_app)
        result = runner.invoke(app, ["watch", "--stream", "--run-id", run_id], env=_ENV)
        assert result.exit_code == 0, result.output
        assert calls["replay"] is False

    def test_watch_replay_tty_invokes_textual_app(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        import claudeloop.cli.commands.watch as watch_mod

        monkeypatch.setattr(watch_mod, "sys_stdout_isatty", lambda: True)
        calls: dict[str, object] = {}

        def fake_run_textual_app(*, events_path, follow, replay, speed):
            calls["replay"] = replay

        monkeypatch.setattr(watch_mod, "run_textual_app", fake_run_textual_app)
        result = runner.invoke(app, ["watch", "--replay", "--run-id", run_id], env=_ENV)
        assert result.exit_code == 0, result.output
        assert calls["replay"] is True

    def test_watch_replay_non_tty_dumps_transcript(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        import claudeloop.cli.commands.watch as watch_mod

        monkeypatch.setattr(watch_mod, "sys_stdout_isatty", lambda: False)
        dumped: dict[str, object] = {}

        def fake_dump_transcript(events_path):
            dumped["events_path"] = events_path

        monkeypatch.setattr(watch_mod, "dump_transcript", fake_dump_transcript)
        result = runner.invoke(app, ["watch", "--replay", "--run-id", run_id], env=_ENV)
        assert result.exit_code == 0, result.output
        assert "events_path" in dumped

    def test_watch_bus_runtime_error(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        import claudeloop.cli.commands.watch as watch_mod

        def raise_runtime(*a, **kw):
            raise RuntimeError("boom")

        monkeypatch.setattr(watch_mod.bootstrap_ops, "watch_bus", raise_runtime)
        result = runner.invoke(app, ["watch", "--no-follow", "--run-id", run_id], env=_ENV)
        assert result.exit_code == 1
        assert "boom" in result.output


class TestToolCommandsSuccess:
    def test_tool_approve_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(
            app,
            ["tool", "approve", "req-1", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0

    def test_tool_deny_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(
            app,
            ["tool", "deny", "req-1", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0


class TestChatListWithData:
    def test_chat_list_with_pinned(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["chat", "pin", "s1"], env=_ENV)
        result = runner.invoke(app, ["chat", "list"], env=_ENV)
        assert result.exit_code == 0

    def test_chat_share(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["chat", "share", "test-session"], env=_ENV)
        assert result.exit_code == 0


class TestAttachSuccess:
    def test_attach_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        f = tmp_path / "note.txt"
        f.write_text("content", encoding="utf-8")
        result = runner.invoke(
            app,
            ["attach", str(f), "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0

    def test_unattach_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(
            app,
            ["unattach", "note.txt", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0


class TestFolderSuccess:
    def test_folder_add_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(
            app,
            ["folder", "add", str(tmp_path), "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0

    def test_folder_rm_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(
            app,
            ["folder", "rm", str(tmp_path), "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0


class TestSkillSuccess:
    def test_skill_add_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(
            app,
            ["skill", "add", "my-skill", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0

    def test_skill_rm_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(
            app,
            ["skill", "rm", "my-skill", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0


class TestPluginSuccess:
    def test_plugin_add_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(
            app,
            ["plugin", "add", "my-plugin", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0

    def test_plugin_rm_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(
            app,
            ["plugin", "rm", "my-plugin", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0


class TestMemorySuccess:
    def test_memory_set_and_list(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(
            app,
            ["memory", "set", "prefs", "be concise", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0
        result = runner.invoke(
            app,
            ["memory", "list", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0
        assert "prefs" in result.output

    def test_memory_get_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        runner.invoke(
            app,
            ["memory", "set", "note1", "body text", "--run-id", run_id],
            env=_ENV,
        )
        result = runner.invoke(
            app,
            ["memory", "get", "note1", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0
        assert "body text" in result.output

    def test_memory_rm_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        runner.invoke(
            app,
            ["memory", "set", "note1", "body", "--run-id", run_id],
            env=_ENV,
        )
        result = runner.invoke(
            app,
            ["memory", "rm", "note1", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0


class TestGithubSuccess:
    def test_github_add_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(
            app,
            ["github", "add", "owner/repo", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0


class TestArtifactSuccess:
    def test_artifact_list_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(
            app,
            ["artifact", "list", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0


class TestResearchSuccess:
    def test_research_start_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(
            app,
            ["research", "start", "my query", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0

    def test_research_status_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(
            app,
            ["research", "status", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0


class TestWebSearchSuccess:
    def test_web_search_enable_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(
            app,
            ["web-search", "enable", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0

    def test_web_search_disable_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(
            app,
            ["web-search", "disable", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0


class TestPermissionModeSuccess:
    def test_permission_mode_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(
            app,
            ["permission-mode", "plan", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0

    def test_permission_mode_manual(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(
            app,
            ["permission-mode", "manual", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0


class TestCwdSuccess:
    def test_cwd_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(
            app,
            ["cwd", str(tmp_path), "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0


class TestSavepointsSuccess:
    def test_savepoints_list(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(
            app,
            ["savepoints", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0


class TestEffortError:
    def test_effort_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["effort", "max", "--run-id", "nope"], env=_ENV)
        assert result.exit_code == 1


class TestPresetError:
    def test_preset_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["preset", "high", "--run-id", "nope"], env=_ENV)
        assert result.exit_code == 1


class TestPromptError:
    def test_prompt_now_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["prompt", "hello", "--now", "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1


class TestMemoryListEmpty:
    def test_memory_list_empty(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(
            app,
            ["memory", "list", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0
        assert "No memories" in result.output


class TestGithubImportIssueSuccess:
    def test_github_import_issue_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(
            app,
            ["github", "import-issue", "owner/repo#1", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0
        assert "import-issue" in result.output


class TestArtifactFullCoverage:
    def test_artifact_list_with_items(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        arts_dir = directory.root / "artifacts"
        arts_dir.mkdir(parents=True, exist_ok=True)
        (arts_dir / "file.txt").write_text("hi", encoding="utf-8")
        result = runner.invoke(
            app,
            ["artifact", "list", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0
        assert "file.txt" in result.output

    def test_artifact_get_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        arts_dir = directory.root / "artifacts"
        arts_dir.mkdir(parents=True, exist_ok=True)
        (arts_dir / "note.txt").write_text("artifact content", encoding="utf-8")
        result = runner.invoke(
            app,
            ["artifact", "get", "note.txt", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0
        assert "artifact content" in result.output

    def test_artifact_put_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        source = tmp_path / "src.txt"
        source.write_text("put content", encoding="utf-8")
        result = runner.invoke(
            app,
            ["artifact", "put", "dest.txt", str(source), "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0
        assert "Stored" in result.output

    def test_artifact_put_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        source = tmp_path / "src.txt"
        source.write_text("content", encoding="utf-8")
        result = runner.invoke(
            app,
            ["artifact", "put", "dest.txt", str(source), "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1

    def test_artifact_rm_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        arts_dir = directory.root / "artifacts"
        arts_dir.mkdir(parents=True, exist_ok=True)
        (arts_dir / "torm.txt").write_text("x", encoding="utf-8")
        result = runner.invoke(
            app,
            ["artifact", "rm", "torm.txt", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0
        assert "Removed" in result.output


class TestChatFlagsCoverage:
    def test_chat_list_with_pinned_and_unread(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["chat", "pin", "s1"], env=_ENV)
        runner.invoke(app, ["chat", "unread", "s1"], env=_ENV)
        result = runner.invoke(app, ["chat", "list"], env=_ENV)
        assert result.exit_code == 0
        assert "pinned" in result.output
        assert "unread" in result.output

    def test_chat_delete_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["chat", "pin", "s-to-delete"], env=_ENV)
        result = runner.invoke(app, ["chat", "delete", "s-to-delete"], env=_ENV)
        assert result.exit_code == 0
        assert "Deleted" in result.output


class TestConnectorErrorPaths:
    def test_connector_add_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["connector", "add", "myconn", "http://x", "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1

    def test_connector_rm_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["connector", "rm", "myconn", "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1

    def test_connector_list_with_connectors(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        import claudeloop.cli.commands.connector_cmd as conn_mod

        class _FakeStore:
            def list_connectors(self):
                return {"myconn": {"url": "http://x"}}

        monkeypatch.setattr(
            conn_mod.bootstrap_ops,
            "get_resource_store",
            lambda cwd, run_id=None: _FakeStore(),
        )
        result = runner.invoke(
            app,
            ["connector", "list", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0
        assert "myconn" in result.output


class TestResearchStatusWithItems:
    def test_research_status_with_rows(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        import claudeloop.cli.commands.research_cmd as research_mod

        monkeypatch.setattr(
            research_mod.bootstrap_ops,
            "research_status",
            lambda cwd, run_id=None: [{"query": "test", "status": "pending"}],
        )
        result = runner.invoke(
            app,
            ["research", "status", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0
        assert "test" in result.output


class TestResponseCopy:
    def test_response_copy_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        import claudeloop.cli.commands.response_cmd as resp_mod

        monkeypatch.setattr(
            resp_mod.bootstrap_ops,
            "copy_response",
            lambda cwd, run_id=None: "assistant response text",
        )
        result = runner.invoke(
            app,
            ["response", "copy", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0
        assert "assistant response text" in result.output

    def test_response_copy_empty(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        import claudeloop.cli.commands.response_cmd as resp_mod

        monkeypatch.setattr(
            resp_mod.bootstrap_ops,
            "copy_response",
            lambda cwd, run_id=None: "",
        )
        result = runner.invoke(
            app,
            ["response", "copy", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 1
        assert "No assistant response" in result.output


class TestArtifactPutGetRmSuccess:
    """Covers artifact_cmd.py's `put` command and the success paths of
    `list` (iterating names), `get` (echoing content), and `rm`."""

    def test_artifact_put_list_get_rm(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        source = tmp_path / "source.txt"
        source.write_text("artifact body", encoding="utf-8")

        put_result = runner.invoke(
            app,
            ["artifact", "put", "myartifact.txt", str(source), "--run-id", run_id],
            env=_ENV,
        )
        assert put_result.exit_code == 0
        assert "Stored artifact" in put_result.output

        list_result = runner.invoke(
            app,
            ["artifact", "list", "--run-id", run_id],
            env=_ENV,
        )
        assert list_result.exit_code == 0
        assert "myartifact.txt" in list_result.output

        get_result = runner.invoke(
            app,
            ["artifact", "get", "myartifact.txt", "--run-id", run_id],
            env=_ENV,
        )
        assert get_result.exit_code == 0
        assert "artifact body" in get_result.output

        rm_result = runner.invoke(
            app,
            ["artifact", "rm", "myartifact.txt", "--run-id", run_id],
            env=_ENV,
        )
        assert rm_result.exit_code == 0
        assert "Removed artifact" in rm_result.output

    def test_artifact_put_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        source = tmp_path / "source.txt"
        source.write_text("body", encoding="utf-8")
        result = runner.invoke(
            app,
            ["artifact", "put", "thing.txt", str(source), "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1


class TestChatCoverageExtra:
    """chat_cmd.py: the pinned=False/unread=True branch in `list`, and a
    successful `delete` of metadata that actually exists."""

    def test_chat_list_unread_only_hits_pinned_false_branch(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["chat", "unread", "s2"], env=_ENV)
        result = runner.invoke(app, ["chat", "list"], env=_ENV)
        assert result.exit_code == 0
        assert "unread" in result.output

    def test_chat_delete_success(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["chat", "pin", "s3"], env=_ENV)
        result = runner.invoke(app, ["chat", "delete", "s3"], env=_ENV)
        assert result.exit_code == 0
        assert "Deleted chat metadata" in result.output


class TestConnectorCoverageExtra:
    """connector_cmd.py: the error branches of `add`/`rm` when the run
    can't be resolved, and `list` with actual connectors present."""

    def test_connector_add_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["connector", "add", "myconn", "http://x", "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1

    def test_connector_rm_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["connector", "rm", "myconn", "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1

    def test_connector_list_with_items(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        from claudeloop import bootstrap_ops

        bootstrap_ops.get_resource_store(tmp_path, run_id).set_connector(
            "myconn", {"url": "http://x"}
        )
        result = runner.invoke(
            app,
            ["connector", "list", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0
        assert "myconn" in result.output


class TestEffortPresetNoRun:
    """effort_cmd.py / preset_cmd.py: the (FileNotFoundError, ValueError)
    except branch when the run can't be resolved."""

    def test_effort_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["effort", "high", "--run-id", "nope"], env=_ENV)
        assert result.exit_code == 1

    def test_preset_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["preset", "high", "--run-id", "nope"], env=_ENV)
        assert result.exit_code == 1


class TestMemoryListEmptySuccess:
    def test_memory_list_empty_with_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(
            app,
            ["memory", "list", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0
        assert "No memories" in result.output


class TestPromptNoRun:
    def test_prompt_now_no_run(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app,
            ["prompt", "hello", "--now", "--run-id", "nope"],
            env=_ENV,
        )
        assert result.exit_code == 1


class TestResearchStatusWithRows:
    def test_research_status_with_rows(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        from claudeloop import bootstrap_ops

        bootstrap_ops.get_resource_store(tmp_path, run_id).start_research("my query")
        result = runner.invoke(
            app,
            ["research", "status", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0
        assert "my query" in result.output


class TestResponseCopyCoverageExtra:
    """response_cmd.py's `copy`: the empty-text branch and the successful
    echo-of-text branch, neither reached by the existing no-run test."""

    def test_response_copy_empty(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        result = runner.invoke(
            app,
            ["response", "copy", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 1
        assert "No assistant response found" in result.output

    def test_response_copy_success(self, tmp_path: Path, monkeypatch) -> None:
        import json

        monkeypatch.chdir(tmp_path)
        directory = _run_dir(tmp_path)
        run_id = directory.read_meta().run_id
        record = {
            "event_type": "chatter.assistant",
            "payload": {"text": "hello from claude"},
        }
        with directory.events_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
        result = runner.invoke(
            app,
            ["response", "copy", "--run-id", run_id],
            env=_ENV,
        )
        assert result.exit_code == 0
        assert "hello from claude" in result.output
