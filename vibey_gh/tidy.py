# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The clean repo (sub-doctrine 9.a): technical clutter is drag; human messiness stays.

Surveys every way a repository — local clone and cloud forge alike — technically
accumulates machine-state mess, and cleans exactly the classes whose removal is
provably lossless. The doctrine's two halves are both load-bearing:

- **technically clean at all times, no exceptions**: merged-and-undeleted branches,
  closed-pull-request heads, gone-upstream locals, prunable worktrees, draft
  releases, and orphan tags do not accumulate;
- **human messiness is expressly welcome**: prose, discussions, imperfect words,
  work in progress — nothing here reads, judges, or touches the humans' material.

Losslessness governs `apply`, with two proofs because two merge styles exist:

- **ancestry** — a tip contained in a kept branch is preserved in history verbatim
  (merge-commit flows);
- **the forge's own deletion event** — squash and rebase merges rewrite SHAs, so a
  merged branch's tip is *never* an ancestor of anything kept; there, a local whose
  upstream is `[gone]` was deleted by the forge at merge time, and that event is the
  proof its content landed. `trust_forge_deletions` (default true) admits this
  proof; set it false in flows where remote branches die for other reasons.

Everything else (drafts, orphan tags, stashes, untracked files) is *reported* for
the human, never removed by a machine. Cleanup that could lose work is not cleanup;
it is the mess, wearing a uniform.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from vibey_gh.config import GhConfig

__all__ = ["TidyReport", "apply", "survey"]


@dataclass(frozen=True)
class TidyReport:
    # Provably-lossless deletions `apply` will perform:
    remote_merged: tuple[str, ...] = ()  # remote branches whose tips are in a kept branch
    local_merged: tuple[str, ...] = ()  # same, for the clone
    local_gone: tuple[str, ...] = ()  # locals whose upstream no longer exists
    prunable_worktrees: tuple[str, ...] = ()
    # Reported to the human, never machine-removed:
    draft_releases: tuple[str, ...] = ()
    orphan_tags: tuple[str, ...] = ()  # tags on commits no kept branch contains
    stashes: int = 0
    untracked: int = 0
    problems: tuple[str, ...] = field(default=())

    @property
    def deletable(self) -> int:
        return (
            len(self.remote_merged)
            + len(self.local_merged)
            + len(self.local_gone)
            + len(self.prunable_worktrees)
        )

    @property
    def clean(self) -> bool:
        """Cloud-and-clone technical cleanliness, the doctrine's bar."""
        return self.deletable == 0 and not self.draft_releases and not self.orphan_tags


def _git(root: Path, *args: str) -> str:
    run = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)
    return run.stdout if run.returncode == 0 else ""


def _gh_json(root: Path, *args: str) -> list | dict:
    run = subprocess.run(["gh", *args], cwd=root, capture_output=True, text=True, check=False)
    if run.returncode != 0:
        return []
    try:
        value = json.loads(run.stdout)
    except json.JSONDecodeError:
        return []
    if isinstance(value, (list, dict)):
        return value
    return []


def _kept(cfg: GhConfig) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys((cfg.integration_branch, cfg.release_branch, *cfg.tidy.keep_branches))
    )


def _open_pr_heads(root: Path) -> set[str]:
    prs = _gh_json(root, "pr", "list", "--json", "headRefName", "--limit", "200")
    return {p.get("headRefName", "") for p in prs if isinstance(p, dict)}


def _contained(root: Path, tip: str, kept_remote: list[str]) -> bool:
    for keeper in kept_remote:
        run = subprocess.run(
            ["git", "merge-base", "--is-ancestor", tip, keeper],
            cwd=root,
            capture_output=True,
            check=False,
        )
        if run.returncode == 0:
            return True
    return False


def survey(cfg: GhConfig, local: bool = True) -> TidyReport:
    """Enumerate the mess. `local=False` (CI) surveys only the cloud classes —
    an ephemeral runner's clone has no stashes or worktrees worth judging."""
    root = cfg.root
    kept = _kept(cfg)
    problems: list[str] = []
    _git(root, "fetch", "--prune", "--quiet", "origin")
    kept_remote = [f"origin/{b}" for b in kept if _git(root, "rev-parse", f"origin/{b}")]
    if not kept_remote:
        return TidyReport(problems=("no kept branch resolves on origin; refusing to judge",))
    pr_heads = _open_pr_heads(root)

    remote_merged: list[str] = []
    for line in _git(root, "branch", "-r", "--format=%(refname:short)").splitlines():
        name = line.strip()
        short = name.removeprefix("origin/")
        if not name.startswith("origin/") or "HEAD" in short:
            continue
        if short in kept or short in pr_heads:
            continue
        tip = _git(root, "rev-parse", name).strip()
        if tip and _contained(root, tip, kept_remote):
            remote_merged.append(short)

    drafts = [
        str(r.get("tagName") or r.get("name") or "")
        for r in _gh_json(
            root, "release", "list", "--json", "tagName,name,isDraft", "--limit", "100"
        )
        if isinstance(r, dict) and r.get("isDraft")
    ]

    orphan_tags: list[str] = []
    for tag in _git(root, "tag", "--list").splitlines():
        tag = tag.strip()
        if not tag:
            continue
        tip = _git(root, "rev-parse", f"{tag}^{{commit}}").strip()
        if tip and not _contained(root, tip, kept_remote):
            orphan_tags.append(tag)

    local_merged: list[str] = []
    local_gone: list[str] = []
    prunable: list[str] = []
    stashes = 0
    untracked = 0
    if local:
        current = _git(root, "branch", "--show-current").strip()
        fmt = "%(refname:short)\t%(upstream:track)"
        for line in _git(root, "branch", "--format=" + fmt).splitlines():
            name, _, track = line.partition("\t")
            name = name.strip()
            if not name or name == current or name in kept:
                continue
            if "[gone]" in track:
                local_gone.append(name)
                continue
            if name in pr_heads:
                continue
            tip = _git(root, "rev-parse", name).strip()
            if tip and _contained(root, tip, kept_remote):
                local_merged.append(name)
        main = str(Path(root).resolve())
        for block in _git(root, "worktree", "list", "--porcelain").strip().split("\n\n"):
            lines = block.splitlines()
            path = next(
                (
                    ln.removeprefix("worktree ").strip()
                    for ln in lines
                    if ln.startswith("worktree ")
                ),
                "",
            )
            if not path or path == main:
                continue
            if any(ln.startswith("prunable") for ln in lines):
                prunable.append(path)
        stashes = len(_git(root, "stash", "list").splitlines())
        untracked = len(
            _git(root, "status", "--porcelain", "--untracked-files=normal").splitlines()
        )

    return TidyReport(
        remote_merged=tuple(remote_merged),
        local_merged=tuple(local_merged),
        local_gone=tuple(local_gone),
        prunable_worktrees=tuple(prunable),
        draft_releases=tuple(drafts),
        orphan_tags=tuple(orphan_tags),
        stashes=stashes,
        untracked=untracked,
        problems=tuple(problems),
    )


def apply(cfg: GhConfig, report: TidyReport, run=subprocess.run) -> tuple[str, ...]:
    """Delete exactly the provably-lossless classes; return what was done."""
    root = cfg.root
    actions: list[str] = []
    for short in report.remote_merged:
        result = run(
            ["git", "push", "--quiet", "origin", "--delete", short],
            cwd=root,
            capture_output=True,
            check=False,
        )
        actions.append(
            f"deleted origin/{short}"
            if result.returncode == 0
            else f"could not delete origin/{short}"
        )
    gone = report.local_gone if cfg.tidy.trust_forge_deletions else ()
    for name in (*report.local_merged, *gone):
        result = run(
            ["git", "branch", "--quiet", "-D", name],
            cwd=root,
            capture_output=True,
            check=False,
        )
        actions.append(
            f"deleted local {name}" if result.returncode == 0 else f"could not delete {name}"
        )
    if report.prunable_worktrees:
        run(["git", "worktree", "prune"], cwd=root, capture_output=True, check=False)
        actions.append(f"pruned {len(report.prunable_worktrees)} worktree(s)")
    return tuple(actions)
