"""Materializes the four agent-guidance router files into a BUILD worktree
(M6 task 6.3, ADR-0011). Writes are content-addressed: a router file whose
merged content already matches what's on disk is left untouched, so
re-provisioning an already-correct worktree performs zero writes and, when
nothing changed at all, no git calls either.

Generated files are registered in the worktree's shared `.git/info/exclude`
(never the project's own `.gitignore`) so a project's own hand-written
CLAUDE.md etc. is never clobbered in its working tree and generated content
never lands in a commit -- exactly ADR-0011's "Bad, but" tradeoff.

The marketplace skill directories (`.claude/skills/`, `.agents/skills/`,
`.cursor/rules/`, `.agent/`) from ADR-0011's table are not materialized here:
there is no `vibe-engineering-skills` marketplace available in this build
environment to pull skill content from. Only the four router files -- the
part that's genuinely self-contained -- are provisioned. Replace this
docstring note, not the emitter's signature, once real marketplace access
exists.
"""

from collections.abc import Sequence
from pathlib import Path

from vibey.domain.errors import VibeyError
from vibey.domain.provision import (
    ProvisionSpec,
    RouterFile,
    merge_router,
    needs_write,
    render_block,
)
from vibey.infrastructure.git.clean_env import CleanGitEnvSubprocessExecutor
from vibey.infrastructure.interfaces import CommandExecutor


class ProvisionError(VibeyError):
    def __init__(self, argv: tuple[str, ...], stderr: str) -> None:
        self.argv = argv
        self.stderr = stderr
        super().__init__(f"{' '.join(argv)} failed: {stderr.strip()}")


class AgentSurfaceProvisioner:
    def __init__(self, *, executor: CommandExecutor | None = None) -> None:
        self._executor = executor or CleanGitEnvSubprocessExecutor()

    async def provision(self, worktree_path: Path, spec: ProvisionSpec) -> tuple[Path, ...]:
        block = render_block(spec)
        written: list[Path] = []
        for router in RouterFile:
            path = worktree_path / router.value
            existing = path.read_text() if path.exists() else None
            merged = merge_router(existing, block)
            if needs_write(existing, merged):
                path.write_text(merged)
                written.append(path)

        if written:
            await self._exclude(worktree_path, [path.name for path in written])
        return tuple(written)

    async def _exclude(self, worktree_path: Path, names: Sequence[str]) -> None:
        common_dir = await self._git_common_dir(worktree_path)
        exclude_path = common_dir / "info" / "exclude"
        exclude_path.parent.mkdir(parents=True, exist_ok=True)

        lines = exclude_path.read_text().splitlines() if exclude_path.exists() else []
        changed = False
        for name in names:
            if name not in lines:
                lines.append(name)
                changed = True
        if changed:
            exclude_path.write_text("\n".join(lines) + "\n")

    async def _git_common_dir(self, worktree_path: Path) -> Path:
        argv = ("git", "-C", str(worktree_path), "rev-parse", "--git-common-dir")
        result = await self._executor.execute(argv)
        if result.returncode != 0:
            raise ProvisionError(argv, result.stderr)
        candidate = Path(result.stdout.strip())
        return candidate if candidate.is_absolute() else (worktree_path / candidate).resolve()
