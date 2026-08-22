# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Real-git integration tests for IntegrationBranch -- no mocking, same
rule as the rest of infrastructure/git/'s tests."""

from pathlib import Path

import pytest

from vibey.domain.worktree import branch_name
from vibey.infrastructure.git.clean_env import CleanGitEnvSubprocessExecutor
from vibey.infrastructure.git.integration_branch import IntegrationBranch
from vibey.infrastructure.git.worktree_manager import GitWorktreeManager


async def _run(*argv: str) -> None:
    result = await CleanGitEnvSubprocessExecutor().execute(argv)
    assert result.returncode == 0, result.stderr


@pytest.fixture
async def repo(tmp_path: Path) -> Path:
    await _run("git", "-C", str(tmp_path), "init", "-q", "-b", "main")
    await _run("git", "-C", str(tmp_path), "config", "user.email", "test@example.com")
    await _run("git", "-C", str(tmp_path), "config", "user.name", "Test")
    (tmp_path / "README.md").write_text("hello\n")
    await _run("git", "-C", str(tmp_path), "add", "README.md")
    await _run("git", "-C", str(tmp_path), "commit", "-q", "-m", "initial")
    return tmp_path


async def _make_item_branch(repo: Path, cycle: int, item_id: str, filename: str) -> None:
    worktrees = GitWorktreeManager(repo, cycle=cycle)
    path = await worktrees.create(item_id)
    (path / filename).write_text(f"content from {item_id}\n")
    await _run("git", "-C", str(path), "add", filename)
    await _run("git", "-C", str(path), "commit", "-q", "-m", f"add {filename}")


async def test_merge_item_accumulates_multiple_non_conflicting_items(repo: Path) -> None:
    await _make_item_branch(repo, 1, "item-1", "a.txt")
    await _make_item_branch(repo, 1, "item-2", "b.txt")
    integration = IntegrationBranch(repo, cycle=1)

    first = await integration.merge_item("item-1")
    second = await integration.merge_item("item-2")

    assert first.ok
    assert second.ok
    path = await integration.ensure()
    assert (path / "a.txt").exists()
    assert (path / "b.txt").exists()


async def test_merge_item_detects_a_real_conflict_and_leaves_a_clean_worktree(repo: Path) -> None:
    await _make_item_branch(repo, 1, "item-1", "shared.txt")
    # item-2 branches from the same original HEAD and edits the same new
    # path differently -- a genuine conflict, not simulated.
    worktrees = GitWorktreeManager(repo, cycle=1)
    item_2_path = await worktrees.create("item-2")
    (item_2_path / "shared.txt").write_text("conflicting content from item-2\n")
    await _run("git", "-C", str(item_2_path), "add", "shared.txt")
    await _run("git", "-C", str(item_2_path), "commit", "-q", "-m", "add shared.txt differently")

    integration = IntegrationBranch(repo, cycle=1)
    first = await integration.merge_item("item-1")
    second = await integration.merge_item("item-2")

    assert first.ok
    assert not second.ok
    assert second.detail

    # the worktree is left clean -- no merge in progress -- so the next
    # merge_item() call (a repair, or the next item) isn't blocked by it.
    path = await integration.ensure()
    status = await CleanGitEnvSubprocessExecutor().execute(
        ("git", "-C", str(path), "status", "--porcelain=v1")
    )
    assert "UU" not in status.stdout
    merge_head = path / ".git"
    assert merge_head.exists()  # sanity: still a real worktree
    in_progress = await CleanGitEnvSubprocessExecutor().execute(
        ("git", "-C", str(path), "rev-parse", "--verify", "-q", "MERGE_HEAD")
    )
    assert in_progress.returncode != 0  # no merge in progress


async def test_ensure_does_not_wipe_prior_merges(repo: Path) -> None:
    await _make_item_branch(repo, 1, "item-1", "a.txt")
    integration = IntegrationBranch(repo, cycle=1)
    await integration.merge_item("item-1")

    path = await integration.ensure()

    assert (path / "a.txt").exists()


async def test_integration_branch_name_matches_the_domain_scheme(repo: Path) -> None:
    integration = IntegrationBranch(repo, cycle=3)
    path = await integration.ensure()

    branches = await CleanGitEnvSubprocessExecutor().execute(
        ("git", "-C", str(repo), "branch", "--list", branch_name(3, "integration"))
    )
    assert "vibey/3/integration" in branches.stdout
    assert path == repo / ".vibey" / "worktrees" / "3" / "integration"
