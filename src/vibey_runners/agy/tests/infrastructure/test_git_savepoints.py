# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Git save-point store: refs/agyloop, ignore .agyloop/, no empty commits."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from agyloop.infrastructure.git_savepoints import GitSavePointStore
from agyloop.infrastructure.rundir import RunDirectory, runs_root_for


def _git(cwd: Path, *args: str) -> str:
    result = subprocess.run(  # nosec B603
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _init_repo(tmp_path: Path) -> Path:
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "agyloop@example.test")
    _git(tmp_path, "config", "user.name", "agyloop")
    (tmp_path / "README.md").write_text("hello\n", encoding="utf-8")
    _git(tmp_path, "add", "README.md")
    _git(tmp_path, "commit", "-m", "init")
    return tmp_path


def test_create_commits_worktree_and_ignores_agyloop_dir(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    run_dir = RunDirectory.create(runs_root_for(repo), cwd=repo)
    (repo / "src.txt").write_text("work\n", encoding="utf-8")
    store = GitSavePointStore(cwd=repo, index_path=run_dir.savepoints_path)
    run_id = run_dir.read_meta().run_id
    point = store.create(run_id=run_id, label="turn", attempt=1, summary="did work")
    assert point is not None
    assert point.committed is True
    assert point.ref.startswith("refs/agyloop/")
    subject = _git(repo, "log", "-1", "--format=%s")
    assert subject.startswith("chore(agyloop):")
    assert ".agyloop" not in _git(repo, "ls-tree", "-r", "--name-only", "HEAD")
    listed = store.list_points(run_dir.read_meta().run_id)
    assert len(listed) == 1
    assert listed[0].sha == point.sha


def test_create_skips_pycache_and_bytecode(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    run_dir = RunDirectory.create(runs_root_for(repo), cwd=repo)
    (repo / "pkg").mkdir()
    (repo / "pkg" / "mod.py").write_text("x = 1\n", encoding="utf-8")
    pycache = repo / "pkg" / "__pycache__"
    pycache.mkdir()
    (pycache / "mod.cpython-312.pyc").write_bytes(b"\0pyc")
    (repo / "pkg" / "mod.pyo").write_bytes(b"\0pyo")
    store = GitSavePointStore(cwd=repo, index_path=run_dir.savepoints_path)
    run_id = run_dir.read_meta().run_id
    point = store.create(run_id=run_id, label="turn", attempt=1, summary="code")
    assert point is not None
    assert point.committed is True
    names = _git(repo, "ls-tree", "-r", "--name-only", "HEAD")
    assert "pkg/mod.py" in names
    assert "__pycache__" not in names
    assert "mod.pyo" not in names


def test_unchanged_tree_is_ref_only_no_empty_commit(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    run_dir = RunDirectory.create(runs_root_for(repo), cwd=repo)
    store = GitSavePointStore(cwd=repo, index_path=run_dir.savepoints_path)
    run_id = run_dir.read_meta().run_id
    first = store.create(run_id=run_id, label="a", attempt=1)
    assert first is not None
    head_before = _git(repo, "rev-parse", "HEAD")
    second = store.create(run_id=run_id, label="b", attempt=2)
    assert second is not None
    assert second.committed is False
    assert second.sha == head_before
    assert _git(repo, "rev-parse", "HEAD") == head_before


def test_unwind_and_changes_since(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    run_dir = RunDirectory.create(runs_root_for(repo), cwd=repo)
    store = GitSavePointStore(cwd=repo, index_path=run_dir.savepoints_path)
    run_id = run_dir.read_meta().run_id
    (repo / "one.txt").write_text("one\n", encoding="utf-8")
    first = store.create(run_id=run_id, label="one", message="first savepoint")
    assert first is not None
    (repo / "two.txt").write_text("two\n", encoding="utf-8")
    second = store.create(run_id=run_id, label="two", attempt=2)
    assert second is not None

    # changes_since
    changes = store.changes_since(first.sha)
    assert "two" in changes or "chore(agyloop)" in changes

    # unwind with backup=False by label
    res = store.unwind(run_id=run_id, to="one", backup=False)
    assert res.restored_sha == first.sha
    assert res.backup_ref is None

    # unwind by ref
    res_ref = store.unwind(run_id=run_id, to=first.ref, backup=True)
    assert res_ref.restored_sha == first.sha

    # unwind by integer n
    res_n = store.unwind(run_id=run_id, to="1", backup=False)
    assert res_n.to.n == 1

    # unwind by invalid target
    with pytest.raises(ValueError, match="no save point numbered 99"):
        store.unwind(run_id=run_id, to="99", backup=False)
    with pytest.raises(ValueError, match="no save point matching 'nonexistent'"):
        store.unwind(run_id=run_id, to="nonexistent", backup=False)


def test_savepoint_index_filtering_and_changes_since(tmp_path: Path) -> None:
    git_repo = _init_repo(tmp_path)
    index_file = git_repo / ".agyloop" / "savepoints.jsonl"
    index_file.parent.mkdir(parents=True, exist_ok=True)

    # Write blank lines, run_id mismatch, and valid line
    index_file.write_text(
        "\n\n"
        + json.dumps(
            {
                "run_id": "other_run",
                "n": 1,
                "ref": "refs/agyloop/other_run/1",
                "sha": "1234567890abcdef",
                "label": "other",
                "at": "2026-08-15T00:00:00Z",
                "committed": False,
            }
        )
        + "\n"
        + json.dumps(
            {
                "run_id": "my_run",
                "n": 1,
                "ref": "refs/agyloop/my_run/1",
                "sha": "abcdef1234567890",
                "label": "mine",
                "at": "2026-08-15T00:00:00Z",
                "committed": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    store = GitSavePointStore(cwd=git_repo, index_path=index_file)
    points = store.list_points("my_run")
    assert len(points) == 1
    assert points[0].label == "mine"

    # changes_since when dirty working directory exists
    (git_repo / "dirty.txt").write_text("modified", encoding="utf-8")
    changes = store.changes_since(None)
    assert "dirty.txt" in changes


def test_non_git_repo(tmp_path: Path) -> None:
    non_git = tmp_path / "not_git"
    non_git.mkdir()
    index_file = non_git / "index.jsonl"
    store = GitSavePointStore(cwd=non_git, index_path=index_file)
    assert store.create(run_id="r1", label="l") is None
    assert store.changes_since(None) == ""

    # list_points when index file does not exist
    assert store.list_points("r1") == []


def test_changes_since_falls_through_to_status_when_log_empty(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    run_dir = RunDirectory.create(runs_root_for(repo), cwd=repo)
    store = GitSavePointStore(cwd=repo, index_path=run_dir.savepoints_path)
    head = _git(repo, "rev-parse", "HEAD")
    # No new commits since HEAD, but dirty file exists
    (repo / "dirty_uncommitted.txt").write_text("dirty")
    changes = store.changes_since(head)
    assert "dirty_uncommitted.txt" in changes
