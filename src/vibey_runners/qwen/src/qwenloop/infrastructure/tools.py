# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Constrained local tool execution."""

import asyncio
import os
from pathlib import Path


class SandboxTools:
    def __init__(self, worktree: Path, *, allow_network: bool = False) -> None:
        self.worktree = worktree.resolve()
        self.allow_network = allow_network

    async def execute(self, name: str, arguments: dict[str, object]) -> dict[str, object]:
        if name == "read_file":
            path = self._path(str(arguments.get("path", "")))
            try:
                return {"content": path.read_text(encoding="utf-8")[:200_000]}
            except (OSError, UnicodeDecodeError) as exc:
                return {"error": str(exc)}
        if name == "write_file":
            path = self._path(str(arguments.get("path", "")))
            content = str(arguments.get("content", ""))
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            except OSError as exc:
                return {"error": str(exc)}
            return {"written": len(content)}
        if name == "shell":
            argv = arguments.get("argv")
            if not isinstance(argv, list) or not argv or not all(isinstance(x, str) for x in argv):
                return {"error": "argv must be a non-empty string list"}
            if argv[0] in {"sudo", "rm", "shutdown", "reboot"}:
                return {"error": "command denied by policy"}
            env = {
                key: value
                for key, value in os.environ.items()
                if "KEY" not in key and "TOKEN" not in key
            }
            if not self.allow_network:
                env["QWENLOOP_NETWORK"] = "disabled"
            try:
                process = await asyncio.create_subprocess_exec(
                    *argv,
                    cwd=self.worktree,
                    env=env,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    start_new_session=True,
                )
            except OSError as exc:
                return {"error": str(exc)}
            try:
                output, _ = await asyncio.wait_for(process.communicate(), timeout=120)
            except TimeoutError:
                process.kill()
                await process.wait()
                return {"error": "command timed out"}
            return {
                "exit_code": process.returncode,
                "output": output.decode(errors="replace")[-100_000:],
            }
        return {"error": f"unknown tool {name!r}"}

    def _path(self, raw: str) -> Path:
        target = (self.worktree / raw).resolve()
        if target != self.worktree and self.worktree not in target.parents:
            raise ValueError("path escapes the worktree")
        return target
