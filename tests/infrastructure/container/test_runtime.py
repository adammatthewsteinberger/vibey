# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
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


# --- _detect_runtime coverage ------------------------------------------------


def test_detect_runtime_finds_docker(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("shutil.which", lambda c: "/usr/bin/docker" if c == "docker" else None)
    executor = OciContainerExecutor()
    assert executor._runtime_binary == "docker"


def test_detect_runtime_finds_podman_when_docker_is_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("shutil.which", lambda c: "/usr/bin/podman" if c == "podman" else None)
    executor = OciContainerExecutor()
    assert executor._runtime_binary == "podman"


def test_detect_runtime_falls_back_to_docker_when_neither_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("shutil.which", lambda c: None)
    executor = OciContainerExecutor()
    assert executor._runtime_binary == "docker"


# --- build_argv falsy config branches ----------------------------------------


def test_build_argv_omits_flags_when_config_values_are_falsy() -> None:
    config = ContainerConfig(
        image="test:latest",
        worktree_path=Path("/tmp/w"),
        read_only_root=False,
        network_mode="",
        memory_limit="",
        cpu_limit="",
        drop_capabilities=(),
        security_options=(),
        tmpfs_mounts=(),
    )
    executor = OciContainerExecutor(runtime_binary="docker")
    argv = executor.build_argv(config, ["echo", "hi"])

    assert "--read-only" not in argv
    assert not any(a.startswith("--network=") for a in argv)
    assert not any(a.startswith("--memory=") for a in argv)
    assert not any(a.startswith("--cpus=") for a in argv)


# --- run() real subprocess path -----------------------------------------------


@pytest.mark.asyncio
async def test_run_real_subprocess_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    import asyncio

    class FakeProc:
        returncode = 0

        async def communicate(self) -> tuple[bytes, bytes]:
            return b"hello\n", b""

    async def fake_create(*args: object, **kwargs: object) -> FakeProc:
        return FakeProc()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create)
    executor = OciContainerExecutor(runtime_binary="echo")
    config = ContainerConfig(image="test:latest", worktree_path=Path("/tmp/w"))
    result = await executor.run(config, ["hi"])
    assert result.exit_code == 0
    assert result.stdout == "hello\n"


@pytest.mark.asyncio
async def test_run_real_subprocess_error_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    import asyncio

    async def fake_create(*args: object, **kwargs: object) -> None:
        raise OSError("no such binary")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create)
    executor = OciContainerExecutor(runtime_binary="nonexistent")
    config = ContainerConfig(image="test:latest", worktree_path=Path("/tmp/w"))
    result = await executor.run(config, ["hi"])
    assert result.exit_code == 1
    assert result.stderr == "Container execution failed"
