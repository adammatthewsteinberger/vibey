# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Real-git integration tests -- no mocking of git itself, per this
project's own rule about not faking the property that matters. Runs
against a real repo created fresh in tmp_path for every test."""

import asyncio
import os
from pathlib import Path

import pytest

from vibey.infrastructure.engines.claudeloop_process import CommandResult
from vibey.infrastructure.git.clean_env import CleanGitEnvSubprocessExecutor
from vibey.infrastructure.git.worktree_manager import GitWorktreeManager, WorktreeError


async def _run(*argv: str) -> CommandResult:
    return await CleanGitEnvSubprocessExecutor().execute(argv)


def _clean_env() -> dict[str, str]:
    return {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}


@pytest.fixture
async def repo(tmp_path: Path) -> Path:
    await _run("git", "-C", str(tmp_path), "init", "-q", "-b", "main")
    await _run("git", "-C", str(tmp_path), "config", "user.email", "test@example.com")
    await _run("git", "-C", str(tmp_path), "config", "user.name", "Test")
    (tmp_path / "README.md").write_text("hello\n")
    await _run("git", "-C", str(tmp_path), "add", "README.md")
    await _run("git", "-C", str(tmp_path), "commit", "-q", "-m", "initial")
    return tmp_path


async def test_create_adds_a_worktree_on_a_new_branch(repo: Path) -> None:
    manager = GitWorktreeManager(repo, cycle=1)

    path = await manager.create("item-1")

    assert path == repo / ".vibey" / "worktrees" / "1" / "item-1"
    assert path.exists()
    assert (path / "README.md").exists()
    listed = await _run("git", "-C", str(repo), "branch", "--list", "vibey/1/item-1")
    assert "vibey/1/item-1" in listed.stdout


async def test_create_is_idempotent_after_a_prior_successful_create(repo: Path) -> None:
    manager = GitWorktreeManager(repo, cycle=1)
    first = await manager.create("item-1")
    (first / "scratch.txt").write_text("uncommitted work")

    second = await manager.create("item-1")

    assert second == first
    assert second.exists()
    # create() self-heals by removing and recreating -- uncommitted scratch
    # files in an existing worktree do not survive a second create() for the
    # same item, which is the correct behavior for recovering from a bad
    # prior attempt, not a data-loss bug: nothing here was ever committed.
    assert not (second / "scratch.txt").exists()


async def test_create_recovers_from_a_dangling_branch_left_by_a_killed_attempt(repo: Path) -> None:
    manager = GitWorktreeManager(repo, cycle=1)
    # Simulate the branch half of a create() that died before `git worktree
    # add` finished: the branch exists, but no worktree or directory does.
    await _run("git", "-C", str(repo), "branch", "vibey/1/item-1")

    path = await manager.create("item-1")

    assert path.exists()
    assert (path / "README.md").exists()


async def test_create_removes_a_leftover_directory_with_no_git_registration(repo: Path) -> None:
    manager = GitWorktreeManager(repo, cycle=1)
    orphan_dir = repo / ".vibey" / "worktrees" / "1" / "item-1"
    orphan_dir.mkdir(parents=True)
    (orphan_dir / "partial-checkout-fragment").write_text("leftover from a killed create")

    path = await manager.create("item-1")

    assert path.exists()
    assert not (path / "partial-checkout-fragment").exists()
    assert (path / "README.md").exists()


async def test_remove_deletes_the_worktree_and_its_registration(repo: Path) -> None:
    manager = GitWorktreeManager(repo, cycle=1)
    path = await manager.create("item-1")
    assert path.exists()

    await manager.remove("item-1")

    assert not path.exists()
    listed = await _run("git", "-C", str(repo), "worktree", "list", "--porcelain")
    assert str(path) not in listed.stdout


async def test_remove_of_an_already_gone_worktree_is_a_no_op(repo: Path) -> None:
    manager = GitWorktreeManager(repo, cycle=1)
    await manager.remove("never-created")  # must not raise


async def test_reclaim_orphans_removes_directories_git_does_not_recognize(repo: Path) -> None:
    manager = GitWorktreeManager(repo, cycle=1)
    kept = await manager.create("item-1")
    orphan = repo / ".vibey" / "worktrees" / "1" / "item-2"
    orphan.mkdir(parents=True)
    (orphan / "junk").write_text("not a real worktree")

    removed = await manager.reclaim_orphans()

    assert removed == (orphan,)
    assert not orphan.exists()
    assert kept.exists()


async def test_reclaim_orphans_is_empty_when_nothing_is_orphaned(repo: Path) -> None:
    manager = GitWorktreeManager(repo, cycle=1)
    await manager.create("item-1")

    assert await manager.reclaim_orphans() == ()


async def test_reclaim_orphans_on_a_project_that_never_built_returns_empty(repo: Path) -> None:
    manager = GitWorktreeManager(repo, cycle=1)
    assert await manager.reclaim_orphans() == ()


async def test_sigkill_mid_create_leaves_no_orphan_and_the_next_create_succeeds(repo: Path) -> None:
    """The literal 6.2 exit condition: SIGKILL mid-create leaves no orphan
    worktree. We can't SIGKILL our own coroutine, so we simulate the
    observable effect directly -- `git worktree add` starts, is killed after
    it has written its administrative state but before it finishes the
    checkout -- by killing the real `git worktree add` subprocess ourselves,
    then proving the *next* create() for the same item heals it."""
    branch = "vibey/1/item-1"
    target = repo / ".vibey" / "worktrees" / "1" / "item-1"
    target.parent.mkdir(parents=True)

    process = await asyncio.create_subprocess_exec(
        "git",
        "-C",
        str(repo),
        "worktree",
        "add",
        "-b",
        branch,
        str(target),
        "HEAD",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=_clean_env(),
    )
    process.kill()
    await process.wait()

    manager = GitWorktreeManager(repo, cycle=1)
    path = await manager.create("item-1")

    assert path == target
    assert path.exists()
    assert (path / "README.md").exists()
    listed = await _run("git", "-C", str(repo), "worktree", "list", "--porcelain")
    assert str(target) in listed.stdout
    # exactly one registration for this path -- no duplicate/orphan entry
    assert listed.stdout.count(f"worktree {target}") == 1


async def test_git_failure_raises_worktree_error_with_argv_and_stderr(
    tmp_path: Path,
) -> None:
    # A directory that is not a git repository: every git call fails, and
    # the error must carry the argv and stderr for the operator. (A missing
    # base_ref is no longer an error -- create() falls back to HEAD.)
    not_a_repo = tmp_path / "not-a-repo"
    not_a_repo.mkdir()
    manager = GitWorktreeManager(not_a_repo, cycle=1)

    with pytest.raises(WorktreeError) as excinfo:
        await manager.create("item-1")

    assert excinfo.value.argv
    assert excinfo.value.stderr


async def test_ensure_creates_a_worktree_that_does_not_exist_yet(repo: Path) -> None:
    manager = GitWorktreeManager(repo, cycle=1)

    path = await manager.ensure("integration")

    assert path.exists()
    assert (path / "README.md").exists()


async def test_list_worktree_paths_failure_raises_worktree_error(repo: Path) -> None:
    manager = GitWorktreeManager(repo, cycle=1)
    path = await manager.create("item-1")
    assert path.exists()

    class FailingListExecutor:
        async def execute(self, argv: tuple[str, ...]) -> CommandResult:
            if "list" in argv and "--porcelain" in argv:
                return CommandResult(128, "", "fatal: unable to list worktrees\n")
            return await CleanGitEnvSubprocessExecutor().execute(argv)

    manager._executor = FailingListExecutor()
    with pytest.raises(WorktreeError, match="worktree"):
        await manager.ensure("item-1")


async def test_ensure_does_not_wipe_an_already_registered_worktree(repo: Path) -> None:
    manager = GitWorktreeManager(repo, cycle=1)
    first = await manager.create("integration")
    (first / "accumulated-state.txt").write_text("a prior merge's result")

    second = await manager.ensure("integration")

    assert second == first
    assert (second / "accumulated-state.txt").exists()


async def test_create_falls_back_to_head_when_base_ref_is_missing(repo: Path) -> None:
    """Item branches prefer the cycle's integration branch, which does not
    exist before the first integrate -- early items must still build."""
    manager = GitWorktreeManager(repo, cycle=1)

    worktree = await manager.create("early-item", base_ref="vibey/1/integration")

    assert worktree.exists()
    head = await CleanGitEnvSubprocessExecutor().execute(
        ("git", "-C", str(worktree), "rev-parse", "--abbrev-ref", "HEAD")
    )
    assert head.stdout.strip() == "vibey/1/early-item"


async def test_create_uses_the_base_ref_when_it_exists(repo: Path) -> None:
    executor = CleanGitEnvSubprocessExecutor()
    await executor.execute(("git", "-C", str(repo), "branch", "vibey/1/integration"))
    marker = repo / "integrated.txt"
    marker.write_text("integrated\n")
    await executor.execute(("git", "-C", str(repo), "add", "integrated.txt"))
    await executor.execute(("git", "-C", str(repo), "commit", "-q", "-m", "integrated state"))
    # The integration branch is BEHIND main now; a worktree from it must
    # not contain the marker, proving base_ref was honored over HEAD.
    manager = GitWorktreeManager(repo, cycle=1)

    worktree = await manager.create("late-item", base_ref="vibey/1/integration")

    assert not (worktree / "integrated.txt").exists()


async def test_lifecycle_reasserts_core_bare_false(repo: Path) -> None:
    """Live finding from the expansion-13 build: worktree removal/prune can
    leave the primary checkout marked core.bare=true, breaking git status,
    checkout, and commit hooks there. Every mutating lifecycle path must
    heal it -- the checkout is never actually bare."""
    manager = GitWorktreeManager(repo, cycle=1)
    await manager.create("item-1")

    await _run("git", "-C", str(repo), "config", "core.bare", "true")
    await manager.remove("item-1")

    result = await _run("git", "-C", str(repo), "config", "core.bare")
    assert result.stdout.strip() == "false"

    await _run("git", "-C", str(repo), "config", "core.bare", "true")
    await manager.create("item-2")

    result = await _run("git", "-C", str(repo), "config", "core.bare")
    assert result.stdout.strip() == "false"
