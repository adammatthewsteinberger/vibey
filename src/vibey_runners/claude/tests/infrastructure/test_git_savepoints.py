# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for infrastructure/git_savepoints.py — GitSavePointStore."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from claudeloop.infrastructure.git_savepoints import GitSavePointStore


def _init_repo(path: Path) -> Path:
    """Initialise a tiny git repo with one commit."""
    subprocess.run(["git", "init", str(path)], check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=path,
        check=True,
        capture_output=True,
    )
    (path / "README.md").write_text("# init\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "initial commit", "--no-verify"],
        cwd=path,
        check=True,
        capture_output=True,
    )
    return path


class TestGitSavePointStore:
    def test_create_savepoint_no_changes(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path / "repo")
        index = tmp_path / "index.jsonl"
        store = GitSavePointStore(cwd=repo, index_path=index)
        point = store.create(run_id="r1", label="turn-1")
        assert point is not None
        assert point.n == 1
        assert point.committed is False
        assert "r1" in point.ref

    def test_create_savepoint_with_changes(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path / "repo")
        index = tmp_path / "index.jsonl"
        store = GitSavePointStore(cwd=repo, index_path=index)
        (repo / "new_file.txt").write_text("hello", encoding="utf-8")
        point = store.create(run_id="r1", label="turn-1", message="add file")
        assert point is not None
        assert point.committed is True

    def test_list_points_empty(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path / "repo")
        index = tmp_path / "index.jsonl"
        store = GitSavePointStore(cwd=repo, index_path=index)
        assert store.list_points("r1") == []

    def test_list_points_after_create(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path / "repo")
        index = tmp_path / "index.jsonl"
        store = GitSavePointStore(cwd=repo, index_path=index)
        store.create(run_id="r1", label="turn-1")
        points = store.list_points("r1")
        assert len(points) == 1
        assert points[0].label == "turn-1"

    def test_list_points_filters_by_run_id(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path / "repo")
        index = tmp_path / "index.jsonl"
        store = GitSavePointStore(cwd=repo, index_path=index)
        store.create(run_id="r1", label="a")
        (repo / "f.txt").write_text("x", encoding="utf-8")
        store.create(run_id="r2", label="b")
        assert len(store.list_points("r1")) == 1
        assert len(store.list_points("r2")) == 1

    def test_unwind_to_numbered_point(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path / "repo")
        index = tmp_path / "index.jsonl"
        store = GitSavePointStore(cwd=repo, index_path=index)
        (repo / "f1.txt").write_text("first", encoding="utf-8")
        p1 = store.create(run_id="r1", label="turn-1", message="first")
        (repo / "f2.txt").write_text("second", encoding="utf-8")
        store.create(run_id="r1", label="turn-2", message="second")
        assert (repo / "f2.txt").exists()
        result = store.unwind(run_id="r1", to=str(p1.n), backup=False)
        assert result.restored_sha == p1.sha
        assert not (repo / "f2.txt").exists()

    def test_unwind_with_backup(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path / "repo")
        index = tmp_path / "index.jsonl"
        store = GitSavePointStore(cwd=repo, index_path=index)
        (repo / "f1.txt").write_text("data", encoding="utf-8")
        p1 = store.create(run_id="r1", label="turn-1", message="first")
        (repo / "f2.txt").write_text("more", encoding="utf-8")
        store.create(run_id="r1", label="turn-2", message="second")
        result = store.unwind(run_id="r1", to=str(p1.n), backup=True)
        assert result.backup_ref is not None
        assert "backup" in result.backup_ref

    def test_unwind_bad_target_raises(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path / "repo")
        index = tmp_path / "index.jsonl"
        store = GitSavePointStore(cwd=repo, index_path=index)
        store.create(run_id="r1", label="turn-1")
        with pytest.raises(ValueError, match="no save point"):
            store.unwind(run_id="r1", to="999", backup=False)

    def test_changes_since_no_git(self, tmp_path: Path) -> None:
        # cwd has to exist for the subprocess to spawn at all -- the case
        # under test is "exists but isn't a git repo", not "doesn't exist".
        not_a_repo = tmp_path / "not-a-repo"
        not_a_repo.mkdir()
        index = tmp_path / "index.jsonl"
        store = GitSavePointStore(cwd=not_a_repo, index_path=index)
        assert store.changes_since(None) == ""

    def test_changes_since_with_sha(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path / "repo")
        index = tmp_path / "index.jsonl"
        store = GitSavePointStore(cwd=repo, index_path=index)
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        (repo / "new.txt").write_text("x", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "second", "--no-verify"],
            cwd=repo,
            check=True,
            capture_output=True,
        )
        result = store.changes_since(sha)
        assert "second" in result

    def test_changes_since_head_sha_falls_through(self, tmp_path: Path) -> None:
        """When since_sha is HEAD itself, git log returns empty → falls
        through to git status (branch 135->137)."""
        repo = _init_repo(tmp_path / "repo")
        index = tmp_path / "index.jsonl"
        store = GitSavePointStore(cwd=repo, index_path=index)
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        result = store.changes_since(sha)
        assert isinstance(result, str)

    def test_changes_since_none_sha(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path / "repo")
        index = tmp_path / "index.jsonl"
        store = GitSavePointStore(cwd=repo, index_path=index)
        result = store.changes_since(None)
        assert isinstance(result, str)

    def test_create_returns_none_for_non_git(self, tmp_path: Path) -> None:
        not_repo = tmp_path / "not-repo"
        not_repo.mkdir()
        index = tmp_path / "index.jsonl"
        store = GitSavePointStore(cwd=not_repo, index_path=index)
        assert store.create(run_id="r1", label="x") is None

    def test_multiple_savepoints_increment_n(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path / "repo")
        index = tmp_path / "index.jsonl"
        store = GitSavePointStore(cwd=repo, index_path=index)
        p1 = store.create(run_id="r1", label="a")
        (repo / "x.txt").write_text("x", encoding="utf-8")
        p2 = store.create(run_id="r1", label="b", message="add x")
        assert p2.n == p1.n + 1

    def test_create_with_verdict_summary_remaining(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path / "repo")
        index = tmp_path / "index.jsonl"
        store = GitSavePointStore(cwd=repo, index_path=index)
        (repo / "z.txt").write_text("z", encoding="utf-8")
        point = store.create(
            run_id="r1",
            label="turn-3",
            attempt=3,
            verdict_name="Continue",
            summary="Added z",
            remaining_work=("task-a", "task-b"),
        )
        assert point is not None
        assert point.committed is True

    def test_resolve_target_by_label(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path / "repo")
        index = tmp_path / "index.jsonl"
        store = GitSavePointStore(cwd=repo, index_path=index)
        (repo / "a.txt").write_text("a", encoding="utf-8")
        store.create(run_id="r1", label="milestone")
        (repo / "b.txt").write_text("b", encoding="utf-8")
        store.create(run_id="r1", label="later", message="add b")
        store.unwind(run_id="r1", to="milestone", backup=False)
        assert not (repo / "b.txt").exists()

    def test_resolve_target_by_sha_prefix(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path / "repo")
        index = tmp_path / "index.jsonl"
        store = GitSavePointStore(cwd=repo, index_path=index)
        (repo / "a.txt").write_text("a", encoding="utf-8")
        p1 = store.create(run_id="r1", label="first", message="first")
        (repo / "b.txt").write_text("b", encoding="utf-8")
        store.create(run_id="r1", label="second", message="second")
        result = store.unwind(run_id="r1", to=p1.sha[:8], backup=False)
        assert result.restored_sha == p1.sha

    def test_list_points_when_index_exists_already(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path / "repo")
        index = tmp_path / "index.jsonl"
        # Pre-create the index file
        index.write_text("", encoding="utf-8")
        store = GitSavePointStore(cwd=repo, index_path=index)
        (repo / "a.txt").write_text("a", encoding="utf-8")
        store.create(run_id="r1", label="test")
        points = store.list_points("r1")
        assert len(points) == 1

    def test_list_points_skips_blank_lines(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path / "repo")
        index = tmp_path / "index.jsonl"
        store = GitSavePointStore(cwd=repo, index_path=index)
        (repo / "a.txt").write_text("a", encoding="utf-8")
        store.create(run_id="r1", label="test")
        # Manually add a blank line to the index
        index.write_text(index.read_text(encoding="utf-8") + "\n\n", encoding="utf-8")
        points = store.list_points("r1")
        assert len(points) == 1

    def test_staged_paths_returns_empty_on_no_staged(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path / "repo")
        index = tmp_path / "index.jsonl"
        store = GitSavePointStore(cwd=repo, index_path=index)
        paths = store._staged_paths()
        assert paths == ()

    def test_resolve_target_by_ref(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path / "repo")
        index = tmp_path / "index.jsonl"
        store = GitSavePointStore(cwd=repo, index_path=index)
        (repo / "a.txt").write_text("a", encoding="utf-8")
        p1 = store.create(run_id="r1", label="first")
        point = store._resolve_target(store.list_points("r1"), p1.ref)
        assert point.ref == p1.ref

    def test_list_points_missing_index_file_returns_empty(self, tmp_path: Path) -> None:
        """The constructor always touches the index file into existence, so
        to exercise the "not a file" branch of list_points() the file has to
        be removed again afterward."""
        repo = _init_repo(tmp_path / "repo")
        index = tmp_path / "index.jsonl"
        store = GitSavePointStore(cwd=repo, index_path=index)
        index.unlink()
        assert store.list_points("r1") == []

    def test_resolve_target_no_match_raises(self, tmp_path: Path) -> None:
        repo = _init_repo(tmp_path / "repo")
        index = tmp_path / "index.jsonl"
        store = GitSavePointStore(cwd=repo, index_path=index)
        (repo / "a.txt").write_text("a", encoding="utf-8")
        store.create(run_id="r1", label="first")
        with pytest.raises(ValueError, match="no save point matching"):
            store._resolve_target(store.list_points("r1"), "nonexistent-label")
