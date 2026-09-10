# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from cursorloop.application.dto import RunResult
from cursorloop.cli.app import app
from cursorloop.cli.render import exit_code_for
from cursorloop.domain.handoff_marker import EXIT_WIND_DOWN
from cursorloop.infrastructure.doctor_env import Finding
from cursorloop.infrastructure.rundir import RunDirectory, runs_root_for

runner = CliRunner()


def _run_dir(tmp_path: Path) -> RunDirectory:
    return RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)


def test_exit_code_for_maps_known_reasons() -> None:
    ok = RunResult(
        success=True,
        reason="done",
        agent_id=None,
        turns_spent=1,
        tokens_spent=0,
        dollars_spent=0.0,
        cost_pending=True,
    )
    assert exit_code_for(ok) == 0
    base = {
        "success": False,
        "agent_id": None,
        "turns_spent": 0,
        "tokens_spent": 0,
        "dollars_spent": 0.0,
        "cost_pending": True,
    }
    assert exit_code_for(RunResult(reason="Authentication failed", **base)) == 3
    assert exit_code_for(RunResult(reason="max wait exceeded", **base)) == 4
    assert exit_code_for(RunResult(reason="wind-down: low headroom", **base)) == EXIT_WIND_DOWN
    assert exit_code_for(RunResult(reason="wind-down: operator request", **base)) == 75
    assert exit_code_for(RunResult(reason="stopped by operator", **base)) == 130
    assert exit_code_for(RunResult(reason="budget exhausted", **base)) == 1


def test_agents_usage_whoami_are_stubs() -> None:
    assert "live Cursor" in runner.invoke(app, ["agents"]).stdout
    assert "live Cursor" in runner.invoke(app, ["usage"]).stdout
    assert "whoami" in runner.invoke(app, ["whoami"]).stdout


def test_hooks_status_install_restore_diff_and_unknown(tmp_path: Path) -> None:
    cwd = str(tmp_path)
    status = runner.invoke(app, ["hooks", "status", "--cwd", cwd])
    assert status.exit_code == 0
    assert "not-installed" in status.stdout

    installed = runner.invoke(app, ["hooks", "install", "--cwd", cwd])
    assert installed.exit_code == 0
    assert "installed" in installed.stdout

    diff = runner.invoke(app, ["hooks", "diff", "--cwd", cwd])
    assert diff.exit_code == 0

    restored = runner.invoke(app, ["hooks", "restore", "--cwd", cwd])
    assert restored.exit_code == 0

    bad = runner.invoke(app, ["hooks", "nope", "--cwd", cwd])
    assert bad.exit_code == 2


def test_doctor_explain_error_success_and_failure(tmp_path: Path) -> None:
    good = tmp_path / "ok.json"
    good.write_text(
        json.dumps({"run_status": "error", "result_text": "add credits"}),
        encoding="utf-8",
    )
    ok = runner.invoke(app, ["doctor", "--explain-error", str(good)])
    assert ok.exit_code == 0
    assert "CreditsExhausted" in ok.stdout

    bad = tmp_path / "bad.json"
    bad.write_text("[]", encoding="utf-8")
    fail = runner.invoke(app, ["doctor", "--explain-error", str(bad)])
    assert fail.exit_code == 1


def test_doctor_offline_json_and_fail_exit(tmp_path: Path, monkeypatch: object) -> None:
    monkeypatch.delenv("CURSOR_API_KEY", raising=False)  # type: ignore[attr-defined]
    findings = [
        Finding(name="api_key", level="fail", detail="missing", remedy="export CURSOR_API_KEY"),
        Finding(name="git", level="pass", detail="ok"),
    ]
    with patch("cursorloop.cli.commands.doctor.run_doctor", return_value=findings):
        plain = runner.invoke(app, ["doctor", "--cwd", str(tmp_path), "--offline"])
        assert plain.exit_code == 1
        assert "[fail] api_key" in plain.stdout
        assert "remedy:" in plain.stdout

        as_json = runner.invoke(app, ["doctor", "--cwd", str(tmp_path), "--offline", "--json"])
        assert as_json.exit_code == 1
        assert '"api_key"' in as_json.stdout


def test_stop_prompt_status_logs_runs_watch_snapshot_reset(tmp_path: Path) -> None:
    directory = _run_dir(tmp_path)
    directory.audit_path.write_text('{"event":"x"}\n', encoding="utf-8")
    directory.events_path.write_text('{"type":"status"}\n', encoding="utf-8")
    cwd = str(tmp_path)
    run_id = directory.read_meta().run_id

    stop = runner.invoke(app, ["stop", "--cwd", cwd, "--run-id", run_id])
    assert stop.exit_code == 0
    assert run_id in stop.stdout

    prompt = runner.invoke(app, ["prompt", "hello", "--cwd", cwd, "--run-id", run_id])
    assert prompt.exit_code == 0

    status = runner.invoke(app, ["status", "--cwd", cwd, "--run-id", run_id])
    assert status.exit_code == 0
    assert run_id in status.stdout

    logs = runner.invoke(app, ["logs", "--cwd", cwd, "--run-id", run_id])
    assert logs.exit_code == 0
    assert "event" in logs.stdout

    runs = runner.invoke(app, ["runs", "--cwd", cwd])
    assert runs.exit_code == 0
    assert run_id in runs.stdout

    watch = runner.invoke(app, ["watch", "--cwd", cwd, "--run-id", run_id])
    assert watch.exit_code == 0
    assert "status" in watch.stdout

    with patch("cursorloop.cli.commands.control_cmds.StreamUiApp") as ui_cls:
        ui = ui_cls.return_value
        ui_watch = runner.invoke(app, ["watch", "--cwd", cwd, "--run-id", run_id, "--ui"])
        assert ui_watch.exit_code == 0
        ui.run.assert_called_once()

    snap = runner.invoke(app, ["snapshot", "--cwd", cwd, "--run-id", run_id])
    assert snap.exit_code == 0

    reset = runner.invoke(app, ["reset", "--cwd", cwd])
    assert reset.exit_code == 0
    assert "restore" in reset.stdout.lower() or "nothing" in reset.stdout.lower()


def test_stop_file_not_found_exits_one(tmp_path: Path) -> None:
    with patch(
        "cursorloop.cli.commands.control_cmds.run_control.enqueue_stop",
        side_effect=FileNotFoundError("no cursorloop runs found"),
    ):
        result = runner.invoke(app, ["stop", "--cwd", str(tmp_path)])
    assert result.exit_code == 1
    combined = (result.stdout or "") + (result.stderr or "")
    assert "no cursorloop runs" in combined


def test_wind_down_enqueues_command_with_reason(tmp_path: Path) -> None:
    run_dir = _run_dir(tmp_path)
    result = runner.invoke(app, ["wind-down", "--reason", "test reason", "--cwd", str(tmp_path)])
    assert result.exit_code == 0
    assert "Wind-down requested" in result.stdout
    assert run_dir.read_meta().run_id in result.stdout
    inbox_files = list(run_dir.inbox.glob("*.cmd.json"))
    assert len(inbox_files) == 1
    payload = json.loads(inbox_files[0].read_text(encoding="utf-8"))
    assert payload["type"] == "wind_down"
    assert payload["reason"] == "test reason"


def test_wind_down_file_not_found_exits_one(tmp_path: Path) -> None:
    with patch(
        "cursorloop.cli.commands.control_cmds.run_control.enqueue_wind_down",
        side_effect=FileNotFoundError("no cursorloop runs found"),
    ):
        result = runner.invoke(app, ["wind-down", "--cwd", str(tmp_path)])
    assert result.exit_code == 1
    combined = (result.stdout or "") + (result.stderr or "")
    assert "no cursorloop runs" in combined


def test_doctor_offline_all_pass_exits_zero(tmp_path: Path, monkeypatch: object) -> None:
    monkeypatch.delenv("CURSOR_API_KEY", raising=False)  # type: ignore[attr-defined]
    findings = [Finding(name="git", level="pass", detail="ok")]
    with patch("cursorloop.cli.commands.doctor.run_doctor", return_value=findings):
        result = runner.invoke(app, ["doctor", "--cwd", str(tmp_path), "--offline"])
    assert result.exit_code == 0
    assert "[pass] git" in result.stdout


def test_logs_without_audit_file_is_silent(tmp_path: Path) -> None:
    directory = _run_dir(tmp_path)
    directory.audit_path.unlink(missing_ok=True)
    result = runner.invoke(
        app, ["logs", "--cwd", str(tmp_path), "--run-id", directory.read_meta().run_id]
    )
    assert result.exit_code == 0


def test_watch_without_events_file(tmp_path: Path) -> None:
    directory = _run_dir(tmp_path)
    directory.events_path.unlink(missing_ok=True)
    result = runner.invoke(
        app, ["watch", "--cwd", str(tmp_path), "--run-id", directory.read_meta().run_id]
    )
    assert result.exit_code == 0


def test_snapshot_none_ref_is_silent(tmp_path: Path) -> None:
    directory = _run_dir(tmp_path)
    with patch("cursorloop.cli.commands.control_cmds.FileRunSnapshotSink") as sink_cls:
        sink_cls.return_value.emit.return_value = None
        result = runner.invoke(
            app, ["snapshot", "--cwd", str(tmp_path), "--run-id", directory.read_meta().run_id]
        )
    assert result.exit_code == 0
    assert result.stdout == ""


def test_savepoints_and_unwind(tmp_path: Path) -> None:
    directory = _run_dir(tmp_path)
    cwd = str(tmp_path)
    run_id = directory.read_meta().run_id
    point = SimpleNamespace(n=1, sha="abcdef1234567890", label="t1")

    with patch("cursorloop.cli.commands.control_cmds.GitSavePointStore") as store_cls:
        store = store_cls.return_value
        store.list_points.return_value = [point]
        listed = runner.invoke(app, ["savepoints", "--cwd", cwd, "--run-id", run_id])
        assert listed.exit_code == 0
        assert "abcdef123456" in listed.stdout

        unwound = runner.invoke(
            app, ["unwind", "--to", "abcdef1234567890", "--cwd", cwd, "--run-id", run_id]
        )
        assert unwound.exit_code == 0
        store.unwind.assert_called_once()


def test_resume_success_and_failure(tmp_path: Path) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text("# plan\n\nDo the thing.\n", encoding="utf-8")

    result_ok = RunResult(
        success=True,
        reason="finished",
        agent_id="a1",
        turns_spent=1,
        tokens_spent=0,
        dollars_spent=0.0,
        cost_pending=True,
    )
    result_fail = RunResult(
        success=False,
        reason="authentication failed",
        agent_id="a1",
        turns_spent=0,
        tokens_spent=0,
        dollars_spent=0.0,
        cost_pending=True,
    )

    async def _ok_run(_prompt: str) -> RunResult:
        return result_ok

    async def _fail_run(_prompt: str) -> RunResult:
        return result_fail

    built = MagicMock()
    built.runner.run = _ok_run
    built.close = MagicMock()

    with (
        patch("cursorloop.cli.commands.resume.bootstrap.build_runner", return_value=built),
        patch(
            "cursorloop.cli.commands.resume.run_from_plan_file",
            return_value=result_ok,
        ),
    ):
        ok = runner.invoke(
            app,
            ["resume", "--agent-id", "agent-1", "--plan", str(plan), "--cwd", str(tmp_path)],
        )
    assert ok.exit_code == 0
    assert "Done:" in ok.stdout

    built_fail = MagicMock()
    built_fail.runner.run = _fail_run
    built_fail.close = MagicMock()
    with patch("cursorloop.cli.commands.resume.bootstrap.build_runner", return_value=built_fail):
        fail = runner.invoke(app, ["resume", "--agent-id", "agent-1", "--cwd", str(tmp_path)])
    assert fail.exit_code == 3
    combined = (fail.stdout or "") + (fail.stderr or "")
    assert "Run failed" in combined or "authentication" in combined.lower()
