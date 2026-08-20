"""Runs build.verify's gate commands (and its `git diff`) as real
subprocesses in a work item's worktree. No shell=True: commands are already
split into argv by the caller, so there is no injection surface from a
decomposer-produced command string.

Strips GIT_* environment variables unconditionally, not just for the `git
diff` call -- infrastructure/git/clean_env.py's docstring explains why
(GIT_DIR et al. leak in from a `git commit` hook and override `-C`/`cwd`
entirely). A gate command here could itself invoke git indirectly (a test
that shells out, a pre-commit hook inside the worktree), so the same
sanitization applies to every command this runner executes, not only the
one this module happens to know is git."""

import asyncio
import os
from pathlib import Path

from vibey.application.build_verify_handler import GateResult


class SubprocessGateRunner:
    async def run(self, argv: tuple[str, ...], *, cwd: Path) -> GateResult:
        env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        try:
            process = await asyncio.create_subprocess_exec(
                *argv,
                cwd=str(cwd),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
        except (FileNotFoundError, NotADirectoryError, PermissionError) as exc:
            # The gate COMMAND is broken (engine wrote `python` on a box
            # that only has `python3`, greeter4 live finding #3) -- that is
            # a failing gate for the repair loop to fix, not a vibey
            # infrastructure failure to retry into a dead job. 127 is the
            # shell's command-not-found convention.
            return GateResult(127, "", f"gate command could not start: {exc}")
        stdout, stderr = await process.communicate()
        return GateResult(process.returncode or 0, stdout.decode(), stderr.decode())
