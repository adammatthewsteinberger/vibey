# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Real-git integration tests -- no mocking of git, matching the rest of
infrastructure/git/'s tests."""

from pathlib import Path

import pytest

from vibey.domain.provision import ProvisionSpec, RouterFile
from vibey.infrastructure.git.clean_env import CleanGitEnvSubprocessExecutor
from vibey.infrastructure.git.worktree_manager import GitWorktreeManager
from vibey.infrastructure.provision.agent_surface import AgentSurfaceProvisioner


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


def spec() -> ProvisionSpec:
    return ProvisionSpec(
        non_negotiables=("no secrets in the repo",), plugins=("software-architecture",)
    )


async def test_provision_writes_all_four_router_files(repo: Path) -> None:
    worktree = await GitWorktreeManager(repo, cycle=1).create("item-1")

    written = await AgentSurfaceProvisioner().provision(worktree, spec())

    assert {path.name for path in written} == {member.value for member in RouterFile}
    for router in RouterFile:
        content = (worktree / router.value).read_text()
        assert "no secrets in the repo" in content
        assert "software-architecture" in content


async def test_provision_registers_generated_files_in_git_info_exclude(repo: Path) -> None:
    worktree = await GitWorktreeManager(repo, cycle=1).create("item-1")

    await AgentSurfaceProvisioner().provision(worktree, spec())

    exclude = (repo / ".git" / "info" / "exclude").read_text()
    for router in RouterFile:
        assert router.value in exclude
    status = await CleanGitEnvSubprocessExecutor().execute(
        ("git", "-C", str(worktree), "status", "--porcelain")
    )
    assert status.stdout.strip() == ""


async def test_reprovisioning_an_unchanged_worktree_writes_nothing(repo: Path) -> None:
    worktree = await GitWorktreeManager(repo, cycle=1).create("item-1")
    provisioner = AgentSurfaceProvisioner()
    first = await provisioner.provision(worktree, spec())
    assert first

    second = await provisioner.provision(worktree, spec())

    assert second == ()


async def test_reprovisioning_with_a_changed_spec_rewrites_only_the_vibey_block(
    repo: Path,
) -> None:
    worktree = await GitWorktreeManager(repo, cycle=1).create("item-1")
    provisioner = AgentSurfaceProvisioner()
    await provisioner.provision(worktree, spec())

    new_spec = ProvisionSpec(non_negotiables=("a new rule",), plugins=())
    written = await provisioner.provision(worktree, new_spec)

    assert {path.name for path in written} == {member.value for member in RouterFile}
    for router in RouterFile:
        content = (worktree / router.value).read_text()
        assert "a new rule" in content
        assert "no secrets in the repo" not in content


async def test_provision_error_raised_when_git_common_dir_fails(repo: Path) -> None:
    from vibey.infrastructure.engines.claudeloop_process import CommandResult
    from vibey.infrastructure.provision.agent_surface import ProvisionError

    class FailingExecutor:
        async def execute(self, argv: tuple[str, ...]) -> CommandResult:
            return CommandResult(128, "", "fatal: not a git repo\n")

    worktree = await GitWorktreeManager(repo, cycle=1).create("item-1")
    provisioner = AgentSurfaceProvisioner(executor=FailingExecutor())

    with pytest.raises(ProvisionError) as exc_info:
        await provisioner.provision(worktree, spec())

    assert exc_info.value.stderr == "fatal: not a git repo\n"
    assert "git" in exc_info.value.argv


async def test_provision_handles_relative_git_common_dir(repo: Path) -> None:
    from vibey.infrastructure.engines.claudeloop_process import CommandResult

    worktree = await GitWorktreeManager(repo, cycle=1).create("item-1")
    real_executor = CleanGitEnvSubprocessExecutor()

    class RelativePathExecutor:
        async def execute(self, argv: tuple[str, ...]) -> CommandResult:
            result = await real_executor.execute(argv)
            if "--git-common-dir" in argv:
                abs_path = Path(result.stdout.strip())
                try:
                    rel = abs_path.relative_to(worktree)
                    return CommandResult(0, str(rel) + "\n", "")
                except ValueError:
                    pass
            return result

    provisioner = AgentSurfaceProvisioner(executor=RelativePathExecutor())
    written = await provisioner.provision(worktree, spec())
    assert len(written) == len(RouterFile)


async def test_provision_preserves_hand_written_content_outside_the_vibey_block(
    repo: Path,
) -> None:
    worktree = await GitWorktreeManager(repo, cycle=1).create("item-1")
    (worktree / RouterFile.CLAUDE.value).write_text("# My project\n\nHand-written notes.\n")

    await AgentSurfaceProvisioner().provision(worktree, spec())

    content = (worktree / RouterFile.CLAUDE.value).read_text()
    assert "# My project" in content
    assert "Hand-written notes." in content
    assert "no secrets in the repo" in content


async def test_provision_excludes_generated_artifacts_from_every_worktree(repo: Path) -> None:
    """Engine sessions commit with broad adds; the shared exclude file must
    keep compiled caches, coverage data, and machinery dirs out of item
    branches -- their binary add/add conflicts caused real repair storms."""
    worktree = await GitWorktreeManager(repo, cycle=1).create("item-1")

    await AgentSurfaceProvisioner().provision(worktree, spec())

    exclude = (repo / ".git" / "info" / "exclude").read_text()
    for pattern in ("__pycache__/", "*.pyc", ".coverage", "*.egg-info/", ".vibey/"):
        assert pattern in exclude

    # Proof at the git level: generated artifacts are invisible to status.
    (worktree / "__pycache__").mkdir()
    (worktree / "__pycache__" / "x.cpython-312.pyc").write_bytes(b"\x00")
    (worktree / ".coverage").write_bytes(b"\x00")
    status = await CleanGitEnvSubprocessExecutor().execute(
        ("git", "-C", str(worktree), "status", "--porcelain")
    )
    assert status.stdout.strip() == ""
