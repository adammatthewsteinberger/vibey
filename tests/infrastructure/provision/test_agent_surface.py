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
