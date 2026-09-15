# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for infrastructure/rundir.py — RunDirectory, RunMeta, and helpers."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from claudeloop.infrastructure.rundir import (
    RunDirectory,
    RunMeta,
    list_run_directories,
    resolve_run_directory,
    runs_root_for,
    validate_run_id,
)


class TestValidateRunId:
    def test_valid_simple(self) -> None:
        assert validate_run_id("my-run") == "my-run"

    def test_valid_with_dots_and_underscores(self) -> None:
        assert validate_run_id("run_1.2") == "run_1.2"

    def test_strips_whitespace(self) -> None:
        assert validate_run_id("  run1  ") == "run1"

    def test_rejects_empty(self) -> None:
        with pytest.raises(ValueError, match="invalid run id"):
            validate_run_id("")

    def test_rejects_dot_prefix(self) -> None:
        with pytest.raises(ValueError, match="invalid run id"):
            validate_run_id(".hidden")

    def test_rejects_path_traversal(self) -> None:
        with pytest.raises(ValueError, match="invalid run id"):
            validate_run_id("../etc")

    def test_rejects_slashes(self) -> None:
        with pytest.raises(ValueError, match="invalid run id"):
            validate_run_id("a/b")


class TestRunMeta:
    def test_to_dict(self) -> None:
        meta = RunMeta(
            run_id="r1",
            pid=123,
            cwd="/tmp",
            started_at="2024-01-01T00:00:00",
        )
        d = meta.to_dict()
        assert d["run_id"] == "r1"
        assert d["pid"] == 123
        assert d["status"] == "active"

    def test_from_dict_minimal(self) -> None:
        meta = RunMeta.from_dict(
            {
                "run_id": "r1",
                "pid": 123,
                "cwd": "/tmp",
                "started_at": "2024-01-01",
            }
        )
        assert meta.run_id == "r1"
        assert meta.attempt == 0
        assert meta.status == "active"

    def test_from_dict_full(self) -> None:
        meta = RunMeta.from_dict(
            {
                "run_id": "r1",
                "pid": 1,
                "cwd": "/",
                "started_at": "2024-01-01",
                "session_id": "s1",
                "plan_path": "/plan.md",
                "status": "finished",
                "phase": "done",
                "attempt": 3,
                "waiting_until": "2024-01-02",
                "model": "opus",
                "effort": "max",
                "preset": "high",
                "capacity": "ok",
            }
        )
        assert meta.session_id == "s1"
        assert meta.status == "finished"
        assert meta.attempt == 3
        assert meta.model == "opus"


class TestRunDirectory:
    def test_create_auto_id(self, tmp_path: Path) -> None:
        rd = RunDirectory.create(tmp_path / "runs", cwd=tmp_path)
        assert rd.root.is_dir()
        assert rd.inbox.is_dir()
        assert rd.events_path.is_file()
        assert rd.meta_path.is_file()
        meta = rd.read_meta()
        assert meta.pid == os.getpid()

    def test_create_with_explicit_id(self, tmp_path: Path) -> None:
        rd = RunDirectory.create(tmp_path / "runs", cwd=tmp_path, run_id="my-run")
        assert rd.root.name == "my-run"

    def test_create_duplicate_id_raises(self, tmp_path: Path) -> None:
        RunDirectory.create(tmp_path / "runs", cwd=tmp_path, run_id="dup")
        with pytest.raises(FileExistsError):
            RunDirectory.create(tmp_path / "runs", cwd=tmp_path, run_id="dup")

    def test_open_existing(self, tmp_path: Path) -> None:
        rd = RunDirectory.create(tmp_path / "runs", cwd=tmp_path, run_id="x")
        opened = RunDirectory.open_existing(rd.root)
        assert opened.read_meta().run_id == "x"

    def test_open_existing_not_a_run_dir(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match="not a claudeloop run"):
            RunDirectory.open_existing(tmp_path)

    def test_write_and_read_meta(self, tmp_path: Path) -> None:
        rd = RunDirectory.create(tmp_path / "runs", cwd=tmp_path)
        meta = rd.read_meta()
        meta.status = "finished"
        rd.write_meta(meta)
        reloaded = rd.read_meta()
        assert reloaded.status == "finished"

    def test_update_meta(self, tmp_path: Path) -> None:
        rd = RunDirectory.create(tmp_path / "runs", cwd=tmp_path)
        updated = rd.update_meta(status="stopped", attempt=5)
        assert updated.status == "stopped"
        assert updated.attempt == 5
        assert rd.read_meta().status == "stopped"

    def test_write_stop_summary(self, tmp_path: Path) -> None:
        rd = RunDirectory.create(tmp_path / "runs", cwd=tmp_path)
        path = rd.write_stop_summary("# Summary\nDone.")
        assert path.is_file()
        assert "Summary" in path.read_text(encoding="utf-8")

    def test_resources_and_snapshots_roots(self, tmp_path: Path) -> None:
        rd = RunDirectory.create(tmp_path / "runs", cwd=tmp_path)
        assert rd.resources_root.is_dir()
        assert rd.snapshots_root.is_dir()

    def test_subdirectories_created(self, tmp_path: Path) -> None:
        rd = RunDirectory.create(tmp_path / "runs", cwd=tmp_path)
        assert (rd.root / "resources").is_dir()
        assert (rd.root / "memories").is_dir()
        assert (rd.root / "artifacts").is_dir()
        assert (rd.root / "snapshots").is_dir()

    def test_plan_path_in_meta(self, tmp_path: Path) -> None:
        plan = tmp_path / "plan.md"
        plan.write_text("# Plan", encoding="utf-8")
        rd = RunDirectory.create(
            tmp_path / "runs",
            cwd=tmp_path,
            plan_path=plan,
        )
        meta = rd.read_meta()
        assert meta.plan_path is not None
        assert "plan.md" in meta.plan_path


class TestHelpers:
    def test_runs_root_for(self, tmp_path: Path) -> None:
        result = runs_root_for(tmp_path)
        assert result == tmp_path / ".claudeloop" / "runs"

    def test_list_run_directories_empty(self, tmp_path: Path) -> None:
        assert list_run_directories(tmp_path) == []

    def test_list_run_directories(self, tmp_path: Path) -> None:
        runs = tmp_path / ".claudeloop" / "runs"
        RunDirectory.create(runs, cwd=tmp_path, run_id="a")
        RunDirectory.create(runs, cwd=tmp_path, run_id="b")
        dirs = list_run_directories(tmp_path)
        assert len(dirs) == 2

    def test_resolve_run_directory_explicit(self, tmp_path: Path) -> None:
        runs = runs_root_for(tmp_path)
        rd = RunDirectory.create(runs, cwd=tmp_path, run_id="target")
        resolved = resolve_run_directory(tmp_path, run_id="target")
        assert resolved.root == rd.root

    def test_resolve_run_directory_no_runs_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match="no claudeloop runs"):
            resolve_run_directory(tmp_path)

    def test_resolve_run_directory_latest_fallback(self, tmp_path: Path) -> None:
        """With no active run, the fallback is the last entry in
        ``list_run_directories`` -- directory-name sort order, not creation
        order. Names are chosen to sort the same way either scheme would put
        them, so the assertion cannot pass for the wrong reason."""
        runs = runs_root_for(tmp_path)
        rd1 = RunDirectory.create(runs, cwd=tmp_path, run_id="a-run")
        rd1.update_meta(status="finished")
        rd2 = RunDirectory.create(runs, cwd=tmp_path, run_id="b-run")
        rd2.update_meta(status="finished")
        resolved = resolve_run_directory(tmp_path)
        assert resolved.root.name == "b-run"

    def test_handoff_marker_path(self, tmp_path: Path) -> None:
        runs = runs_root_for(tmp_path)
        rd = RunDirectory.create(runs, cwd=tmp_path)
        marker_path = rd.handoff_marker_path
        assert marker_path.parent == rd.root
        assert marker_path.name == "handoff.json"

    def test_write_handoff_marker(self, tmp_path: Path) -> None:
        from datetime import datetime, timezone

        from claudeloop.domain.handoff_marker import HandoffMarker

        runs = runs_root_for(tmp_path)
        rd = RunDirectory.create(runs, cwd=tmp_path)
        marker = HandoffMarker(
            run_id=rd.read_meta().run_id,
            reason="rate_limit_window",
            produced_at=datetime.now(timezone.utc),
        )
        written = rd.write_handoff_marker(marker)
        assert written == rd.handoff_marker_path
        assert written.is_file()
        # Atomic tmp-then-replace: no leftover .json.tmp file.
        assert not written.with_suffix(".json.tmp").exists()
        assert marker.run_id in written.read_text(encoding="utf-8")


class TestPidAlive:
    def test_negative_pid_returns_false(self) -> None:
        from claudeloop.infrastructure.rundir import _pid_alive

        assert _pid_alive(-1) is False

    def test_zero_pid_returns_false(self) -> None:
        from claudeloop.infrastructure.rundir import _pid_alive

        assert _pid_alive(0) is False

    def test_current_pid_returns_true(self) -> None:
        import os

        from claudeloop.infrastructure.rundir import _pid_alive

        assert _pid_alive(os.getpid()) is True

    def test_nonexistent_pid_returns_false(self) -> None:
        from claudeloop.infrastructure.rundir import _pid_alive

        # Use a very high PID that's unlikely to exist
        assert _pid_alive(999999999) is False


class TestResolveRunDirectoryWithActivePid:
    def test_resolves_to_active_run(self, tmp_path: Path) -> None:
        import os

        runs = runs_root_for(tmp_path)
        # Create an inactive run
        rd1 = RunDirectory.create(runs, cwd=tmp_path, run_id="inactive")
        rd1.update_meta(status="finished")
        # Create an active run with current PID
        rd2 = RunDirectory.create(runs, cwd=tmp_path, run_id="active")
        rd2.update_meta(status="active", pid=os.getpid())

        resolved = resolve_run_directory(tmp_path)
        assert resolved.root.name == "active"
