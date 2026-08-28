# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The integration branch/worktree that build.integrate merges verified work
items into, one at a time (M6 task 6.8). Reuses GitWorktreeManager's scheme
with a reserved item_id, "integration", rather than inventing a second
worktree mechanism -- it accumulates state across many merges the same way
create()/ensure() already distinguish "wipe and recreate" from "return what's
already there"."""

from pathlib import Path

from vibey.application.build_integrate_handler import MergeOutcome
from vibey.domain.worktree import branch_name
from vibey.infrastructure.git.clean_env import CleanGitEnvSubprocessExecutor
from vibey.infrastructure.git.worktree_manager import GitWorktreeManager
from vibey.infrastructure.interfaces import CommandExecutor

INTEGRATION_ITEM_ID = "integration"


class IntegrationBranch:
    def __init__(
        self,
        repo_root: Path,
        *,
        cycle: int,
        executor: CommandExecutor | None = None,
    ) -> None:
        self._cycle = cycle
        self._executor = executor or CleanGitEnvSubprocessExecutor()
        self._worktrees = GitWorktreeManager(repo_root, cycle=cycle, executor=self._executor)

    async def ensure(self, *, base_ref: str = "HEAD") -> Path:
        return await self._worktrees.ensure(INTEGRATION_ITEM_ID, base_ref=base_ref)

    async def merge_item(self, item_id: str) -> MergeOutcome:
        path = await self.ensure()
        branch = branch_name(self._cycle, item_id)
        result = await self._executor.execute(
            ("git", "-C", str(path), "merge", "--no-edit", branch)
        )
        if result.returncode == 0:
            return MergeOutcome(ok=True, detail="")

        # A merge conflict leaves the worktree mid-merge; abort so the next
        # attempt (this item's repair, or the next item entirely) starts
        # from a clean state rather than compounding on top of a half-merge.
        await self._executor.execute(("git", "-C", str(path), "merge", "--abort"))
        return MergeOutcome(ok=False, detail=(result.stderr.strip() or result.stdout.strip()))
