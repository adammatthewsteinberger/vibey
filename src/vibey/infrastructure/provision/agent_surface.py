# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Materializes the agent-guidance router files into a BUILD worktree
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
there is no `vibey-skills` (formerly `vibe-engineering-skills`) marketplace available in this build
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


# Generated-artifact patterns registered alongside the router files in the
# shared .git/info/exclude. Engine sessions commit with broad adds; without
# these, compiled caches and coverage data land in item branches and their
# binary add/add merge conflicts send integration into repair storms --
# caught live in the greeter demo. The engines' own state dirs and vibey's
# worktree/context tree are machinery, never product.
_ARTIFACT_PATTERNS = (
    "__pycache__/",
    "*.pyc",
    ".coverage",
    "*.egg-info/",
    ".pytest_cache/",
    "htmlcov/",
    ".vibey/",
    ".claudeloop/",
    ".codexloop/",
    ".cursorloop/",
    ".agyloop/",
    ".qwenloop/",
)


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
            # First provision of a repo always writes routers, so the
            # artifact patterns ride along here -- preserving the
            # zero-git-calls property of an already-correct worktree.
            await self._exclude(
                worktree_path,
                [path.name for path in written] + list(_ARTIFACT_PATTERNS),
            )
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
