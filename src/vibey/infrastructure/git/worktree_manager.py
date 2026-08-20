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

import shutil
from pathlib import Path

from vibey.domain.errors import VibeyError
from vibey.domain.worktree import branch_name, worktree_subpath
from vibey.infrastructure.git.clean_env import CleanGitEnvSubprocessExecutor
from vibey.infrastructure.interfaces import CommandExecutor


class WorktreeError(VibeyError):
    def __init__(self, argv: tuple[str, ...], stderr: str) -> None:
        self.argv = argv
        self.stderr = stderr
        super().__init__(f"{' '.join(argv)} failed: {stderr.strip()}")


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
        self._executor = executor or CleanGitEnvSubprocessExecutor()

    def path_for(self, item_id: str) -> Path:
        """No I/O, no mutation: where this item's worktree lives (or would
        live), for callers like build.verify that must operate on an
        already-created worktree without create()'s self-healing wipe."""
        return self._repo_root / worktree_subpath(self._cycle, item_id)

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
            # base_ref is a preference, not a hard requirement: callers ask
            # for the cycle's integration branch so item branches stack on
            # already-integrated code, but before the first integrate that
            # branch does not exist yet -- fall back to HEAD rather than
            # failing every early item.
            base = base_ref
            if base != "HEAD" and not await self._branch_exists(base):
                base = "HEAD"
            await self._git("worktree", "add", "-b", branch, str(path), base)
        return path

    async def ensure(self, item_id: str, *, base_ref: str = "HEAD") -> Path:
        """Like create(), but never wipes an already-registered worktree --
        for callers (the integration branch) that accumulate state across
        many calls and must not have create()'s self-healing wipe undo a
        prior successful merge."""
        path = self._repo_root / worktree_subpath(self._cycle, item_id)
        if path.exists() and path.resolve() in {
            Path(p).resolve() for p in await self._list_worktree_paths()
        }:
            return path
        return await self.create(item_id, base_ref=base_ref)

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
        # Removing/pruning worktrees can leave the primary checkout marked
        # core.bare=true (observed live during the expansion-13 build;
        # same class as scripts/fleet/land.sh's guard). The primary
        # checkout is never actually bare, so reasserting is always safe --
        # and _prune() runs inside every mutating path (create, ensure,
        # remove, reclaim_orphans), so no lifecycle escapes the guard.
        await self._git("config", "core.bare", "false")

    async def _git(self, *args: str) -> None:
        argv = ("git", "-C", str(self._repo_root), *args)
        result = await self._executor.execute(argv)
        if result.returncode != 0:
            raise WorktreeError(argv, result.stderr)
