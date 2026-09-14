# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Per-run control directory under `.agyloop/runs/<run_id>/`."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from agyloop.infrastructure.rundir import (
    RunDirectory,
    list_run_directories,
    resolve_run_directory,
    runs_root_for,
)


def test_runs_root_is_dot_agyloop(tmp_path: Path) -> None:
    assert runs_root_for(tmp_path) == tmp_path / ".agyloop" / "runs"


def test_create_writes_meta_without_conversation_id(tmp_path: Path) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text("- [ ] do it\n", encoding="utf-8")
    directory = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path, plan_path=plan)
    assert directory.meta_path.is_file()
    meta = directory.read_meta()
    assert meta.conversation_id is None
    assert meta.plan_path is not None
    assert Path(meta.plan_path).name == "plan.md"
    assert (directory.root / "plan.md").is_file()


def test_update_meta_persists_conversation_id_after_first_turn(tmp_path: Path) -> None:
    directory = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    directory.update_meta(conversation_id="c" * 32)
    assert directory.read_meta().conversation_id == "c" * 32
    directory.update_meta(session_id="from-runner")
    assert directory.read_meta().conversation_id == "from-runner"


def test_update_meta_preserves_conversation_id_when_session_id_is_none(
    tmp_path: Path,
) -> None:
    directory = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    original = "conv-resume-id"
    directory.update_meta(conversation_id=original)
    directory.update_meta(session_id=None, phase="WAITING", status="waiting")
    meta = directory.read_meta()
    assert meta.conversation_id == original
    assert meta.status == "waiting"


def test_write_meta_fsyncs(tmp_path: Path) -> None:
    synced: list[int] = []
    real_fsync = os.fsync

    def _spy(fd: int) -> None:
        synced.append(fd)
        real_fsync(fd)

    with patch("agyloop.infrastructure.rundir.os.fsync", side_effect=_spy):
        RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    assert synced


def test_list_run_directories_is_empty_when_missing(tmp_path: Path) -> None:
    assert list_run_directories(tmp_path) == []


def test_resolve_run_directory_prefers_explicit_id(tmp_path: Path) -> None:
    first = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    second = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    resolved = resolve_run_directory(tmp_path, run_id=first.read_meta().run_id)
    assert resolved.root == first.root
    latest = resolve_run_directory(tmp_path)
    assert latest.root == second.root


def test_resolve_run_directory_skips_newer_finished_run(tmp_path: Path) -> None:
    active = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    finished = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    finished.update_meta(status="finished")

    assert resolve_run_directory(tmp_path).root == active.root


def test_resolve_run_directory_refuses_explicit_finished_run(tmp_path: Path) -> None:
    finished = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    finished.update_meta(status="finished")

    with pytest.raises(FileNotFoundError, match="not active"):
        resolve_run_directory(tmp_path, run_id=finished.read_meta().run_id)


def test_resolve_run_directory_refuses_run_with_dead_pid(tmp_path: Path) -> None:
    directory = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)

    with (
        patch("agyloop.infrastructure.rundir.os.kill", side_effect=ProcessLookupError),
        pytest.raises(FileNotFoundError, match="not active"),
    ):
        resolve_run_directory(tmp_path, run_id=directory.read_meta().run_id)


def test_rundir_plan_text_and_pid_alive_and_resolve_any(tmp_path: Path) -> None:
    from agyloop.infrastructure.rundir import pid_alive, resolve_run_directory_any

    # 1. pid_alive with PermissionError
    with patch("os.kill", side_effect=PermissionError):
        assert pid_alive(1234) is True

    # 2. read_plan_text fallback when root plan.md deleted
    orig_plan = tmp_path / "original_plan.md"
    orig_plan.write_text("plan contents", encoding="utf-8")
    directory = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    directory.update_meta(plan_path=str(orig_plan))
    assert directory.read_plan_text() == "plan contents"

    # 3. Non-directory file inside runs root
    (runs_root_for(tmp_path) / "stray_file.txt").write_text("ignore me")
    dirs = list_run_directories(tmp_path)
    assert len(dirs) == 1

    # 4. resolve_run_directory_any
    # Explicit
    assert (
        resolve_run_directory_any(tmp_path, run_id=directory.read_meta().run_id).root
        == directory.root
    )
    # Return newest active when run_id is None
    active_dir = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    assert resolve_run_directory_any(tmp_path).root == active_dir.root
    # Fallback to newest when all inactive
    active_dir.update_meta(status="finished")
    directory.update_meta(status="finished")
    assert resolve_run_directory_any(tmp_path).root == active_dir.root

    # Empty
    empty_tmp = tmp_path / "empty_dir"
    empty_tmp.mkdir()
    with pytest.raises(FileNotFoundError, match="no agyloop runs found"):
        resolve_run_directory_any(empty_tmp)
