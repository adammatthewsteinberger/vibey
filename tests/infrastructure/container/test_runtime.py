from pathlib import Path

import pytest

from vibey.infrastructure.container import (
    ContainerConfig,
    ContainerResult,
    OciContainerExecutor,
)


def test_container_config_defaults() -> None:
    worktree = Path("/tmp/worktrees/item-1")
    config = ContainerConfig(
        image="vibey/runtime:latest",
        worktree_path=worktree,
    )

    assert config.image == "vibey/runtime:latest"
    assert config.worktree_path == worktree
    assert config.read_only_root is True
    assert "ALL" in config.drop_capabilities
    assert config.memory_limit == "4g"
    assert config.cpu_limit == "2.0"
    assert config.network_mode == "none"
    assert any(m.startswith("/tmp") for m in config.tmpfs_mounts)


def test_build_argv_hardened_flags() -> None:
    worktree = Path("/path/to/worktree")
    config = ContainerConfig(
        image="python:3.12-slim",
        worktree_path=worktree,
        container_worktree_path="/workspace",
        memory_limit="2g",
        cpu_limit="1.5",
        network_mode="none",
        read_only_root=True,
        drop_capabilities=("ALL",),
        tmpfs_mounts=("/tmp:rw,noexec,nosuid,size=256m",),
        env_vars={"CI": "1", "VIBEY_ISOLATION": "container"},
    )

    executor = OciContainerExecutor(runtime_binary="docker")
    argv = executor.build_argv(config, ["pytest", "tests"])

    assert argv[0] == "docker"
    assert "run" in argv
    assert "--rm" in argv
    assert "--read-only" in argv
    assert "--network=none" in argv
    assert "--memory=2g" in argv
    assert "--cpus=1.5" in argv
    assert "--cap-drop=ALL" in argv
    assert "--security-opt=no-new-privileges:true" in argv
    assert "-v" in argv
    assert f"{worktree.resolve()}:/workspace:rw" in argv
    assert "-w" in argv
    assert "/workspace" in argv
    assert "-e" in argv
    assert "CI=1" in argv
    assert "VIBEY_ISOLATION=container" in argv
    assert argv[-2:] == ["pytest", "tests"]


@pytest.mark.asyncio
async def test_container_executor_run_mocked() -> None:
    calls: list[list[str]] = []

    async def fake_runner(cmd: list[str]) -> tuple[int, str, str]:
        calls.append(cmd)
        return (0, "all 4 tests passed\n", "")

    executor = OciContainerExecutor(runner=fake_runner, runtime_binary="podman")
    config = ContainerConfig(
        image="node:20-alpine",
        worktree_path=Path("/tmp/node-app"),
    )

    result: ContainerResult = await executor.run(config, ["npm", "test"])
    assert result.exit_code == 0
    assert "all 4 tests passed" in result.stdout
    assert len(calls) == 1
    assert calls[0][0] == "podman"


def test_container_is_available() -> None:
    executor = OciContainerExecutor(runtime_binary="nonexistent_binary_xyz_123")
    assert executor.is_available() is False
