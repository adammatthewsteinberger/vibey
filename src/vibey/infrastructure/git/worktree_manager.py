"""Real git-worktree lifecycle for BUILD work items (M6 task 6.2).

Every mutating call is preceded by a self-healing step (`git worktree
prune` plus removing any leftover directory at the target path) rather than
trusting prior state, because the property that matters is: a `create()`
call always succeeds in leaving a clean, usable worktree, even if the
previous attempt for the same item was killed mid-operation. That is what
makes "SIGKILL mid-create leaves no orphan worktree" true -- not a
best-effort cleanup step someone has to remember to call, but every create
healing whatever it finds first.
"""

import asyncio
import os
import shutil
from pathlib import Path

from vibey.domain.errors import VibeyError
from vibey.domain.worktree import branch_name, worktree_subpath
from vibey.infrastructure.engines.claudeloop_process import CommandExecutor, CommandResult


class WorktreeError(VibeyError):
    def __init__(self, argv: tuple[str, ...], stderr: str) -> None:
        self.argv = argv
        self.stderr = stderr
        super().__init__(f"{' '.join(argv)} failed: {stderr.strip()}")


class _CleanEnvSubprocessExecutor:
    """Like AsyncSubprocessExecutor, but strips GIT_* environment variables.

    A caller running inside a git hook (pre-commit, itself invoked from
    `git commit`) has GIT_DIR/GIT_INDEX_FILE/GIT_WORK_TREE etc. set in its
    own environment, pointing at *that* repository's plumbing. Subprocesses
    inherit the parent environment by default, so an unfiltered `git -C
    <other repo> ...` call silently operates against the wrong repository
    instead of the one -C names -- GIT_DIR overrides discovery outright.
    Only this manager's own git invocations need this; the shared
    AsyncSubprocessExecutor (used for ClaudeLoop, which is never itself a
    nested git invocation) is left untouched.
    """

    async def execute(self, argv: tuple[str, ...]) -> CommandResult:
        env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        process = await asyncio.create_subprocess_exec(
            *argv,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        try:
            stdout, stderr = await process.communicate()
        except asyncio.CancelledError:
            process.terminate()
            await process.wait()
            raise
        return CommandResult(process.returncode or 0, stdout.decode(), stderr.decode())


class GitWorktreeManager:
    def __init__(
        self,
        repo_root: Path,
        *,
        cycle: int,
        executor: CommandExecutor | None = None,
    ) -> None:
        self._repo_root = repo_root
        self._cycle = cycle
        self._executor = executor or _CleanEnvSubprocessExecutor()

    async def create(self, item_id: str, *, base_ref: str = "HEAD") -> Path:
        path = self._repo_root / worktree_subpath(self._cycle, item_id)
        branch = branch_name(self._cycle, item_id)

        if path.exists():
            shutil.rmtree(path)
        await self._prune()

        path.parent.mkdir(parents=True, exist_ok=True)
        if await self._branch_exists(branch):
            await self._git("worktree", "add", str(path), branch)
        else:
            await self._git("worktree", "add", "-b", branch, str(path), base_ref)
        return path

    async def remove(self, item_id: str) -> None:
        path = self._repo_root / worktree_subpath(self._cycle, item_id)
        if path.exists():
            await self._git("worktree", "remove", str(path), "--force")
        await self._prune()

    async def reclaim_orphans(self) -> tuple[Path, ...]:
        """Prunes stale git administrative state, then removes any directory
        under this cycle's managed worktree root that git no longer
        recognizes as a registered worktree -- the leftover of a create that
        died before `git worktree add` completed, or a remove that died
        after git dropped its registration but before the directory was
        deleted."""
        await self._prune()
        registered = {Path(p).resolve() for p in await self._list_worktree_paths()}

        managed_root = self._repo_root / ".vibey" / "worktrees" / str(self._cycle)
        if not managed_root.exists():
            return ()

        removed = []
        for entry in sorted(managed_root.iterdir()):
            if entry.resolve() not in registered:
                shutil.rmtree(entry, ignore_errors=True)
                removed.append(entry)
        return tuple(removed)

    async def _branch_exists(self, branch: str) -> bool:
        result = await self._executor.execute(
            ("git", "-C", str(self._repo_root), "rev-parse", "--verify", "--quiet", branch)
        )
        return result.returncode == 0

    async def _list_worktree_paths(self) -> tuple[str, ...]:
        result = await self._executor.execute(
            ("git", "-C", str(self._repo_root), "worktree", "list", "--porcelain")
        )
        if result.returncode != 0:
            raise WorktreeError(("worktree", "list", "--porcelain"), result.stderr)
        return tuple(
            line.removeprefix("worktree ")
            for line in result.stdout.splitlines()
            if line.startswith("worktree ")
        )

    async def _prune(self) -> None:
        await self._git("worktree", "prune")

    async def _git(self, *args: str) -> None:
        argv = ("git", "-C", str(self._repo_root), *args)
        result = await self._executor.execute(argv)
        if result.returncode != 0:
            raise WorktreeError(argv, result.stderr)
