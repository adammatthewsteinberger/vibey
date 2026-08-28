# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Hardened OCI container runtime wrapper for Docker / Podman execution (Milestone 9 task 9.1)."""

import asyncio
import shutil
from collections.abc import Awaitable, Callable, Sequence
from contextlib import suppress

from vibey.infrastructure.container.config import ContainerConfig, ContainerResult


class OciContainerExecutor:
    def __init__(
        self,
        *,
        runtime_binary: str | None = None,
        runner: Callable[[list[str]], Awaitable[tuple[int, str, str]]] | None = None,
    ) -> None:
        self._runtime_binary = runtime_binary or self._detect_runtime()
        self._runner = runner

    @staticmethod
    def _detect_runtime() -> str:
        for candidate in ("docker", "podman"):
            if shutil.which(candidate) is not None:
                return candidate
        return "docker"

    def is_available(self) -> bool:
        return shutil.which(self._runtime_binary) is not None

    def build_argv(self, config: ContainerConfig, inner_command: Sequence[str]) -> list[str]:
        argv: list[str] = [self._runtime_binary, "run", "--rm"]

        if config.read_only_root:
            argv.append("--read-only")

        if config.network_mode:
            argv.append(f"--network={config.network_mode}")

        if config.memory_limit:
            argv.append(f"--memory={config.memory_limit}")

        if config.cpu_limit:
            argv.append(f"--cpus={config.cpu_limit}")

        for cap in config.drop_capabilities:
            argv.append(f"--cap-drop={cap}")

        for sec_opt in config.security_options:
            argv.append(f"--security-opt={sec_opt}")

        for tmpfs in config.tmpfs_mounts:
            argv.extend(["--tmpfs", tmpfs])

        resolved_worktree = config.worktree_path.resolve()
        argv.extend(["-v", f"{resolved_worktree}:{config.container_worktree_path}:rw"])
        argv.extend(["-w", config.container_worktree_path])

        for k, v in config.env_vars.items():
            argv.extend(["-e", f"{k}={v}"])

        argv.append(config.image)
        argv.extend(inner_command)
        return argv

    async def run(
        self,
        config: ContainerConfig,
        inner_command: Sequence[str],
        timeout_seconds: float = 300.0,
    ) -> ContainerResult:
        cmd = self.build_argv(config, inner_command)

        if self._runner is not None:
            code, out, err = await self._runner(cmd)
            return ContainerResult(exit_code=code, stdout=out, stderr=err)

        with suppress(Exception):
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            out_bytes, err_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=timeout_seconds
            )
            return ContainerResult(
                exit_code=proc.returncode or 0,
                stdout=out_bytes.decode("utf-8", errors="replace"),
                stderr=err_bytes.decode("utf-8", errors="replace"),
            )

        return ContainerResult(exit_code=1, stdout="", stderr="Container execution failed")
