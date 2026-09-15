# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Local-authority mode: keep remotes tracking green local state (#206).

When the paid review lane is capped, the operator's machine becomes the source of
truth, and every clean, provenance-green local branch that is ahead of its upstream
should reach the remote without a human typing pushes. This module is that loop as a
first-class command — the shell daemon's semantics, made generic and testable:

- repositories come from explicit paths or from scanning a root for git work trees
  that carry a `.vibey-gh.toml` (any adopter's fleet, nothing hardcoded);
- protected branches (default: the config's own integration and release branches)
  are never touched from here — permanent refs move only through the reviewed paths;
- a dirty tree is never pushed; a branch failing the provenance check is HELD and
  reported, never pushed; `--force-with-lease` refuses to clobber unseen remote work.

Recovery needs nothing from this loop: the workflows try the paid lane first on every
evaluation, so when the human adds credits, the next evaluation simply succeeds. A
repository with nothing ahead is a no-op, which is why the loop is safe to leave
running in healthy periods too.
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

__all__ = ["SyncOutcome", "discover", "run", "sync_repo"]


@dataclass(frozen=True)
class SyncOutcome:
    repo: str
    branch: str
    action: str  # pushed | held | refused | skipped
    detail: str = ""
    ahead: int = 0

    def __str__(self) -> str:
        suffix = f" ({self.detail})" if self.detail else ""
        ahead = f" ahead={self.ahead}" if self.ahead else ""
        return f"{self.repo} [{self.branch}]: {self.action}{ahead}{suffix}"


def _git(path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(path), *args], capture_output=True, text=True, check=False
    )


def discover(root: Path) -> list[Path]:
    """Every direct child of `root` that is a git work tree carrying .vibey-gh.toml.

    The marker file is the scope rule: this loop only ever touches repositories that
    opted into this tooling, never whatever else happens to live under the root.
    """
    found = []
    for child in sorted(root.iterdir()) if root.is_dir() else []:
        if (child / ".git").exists() and (child / ".vibey-gh.toml").is_file():
            found.append(child)
    return found


def _default_protected(path: Path) -> tuple[str, ...]:
    """The repository's own permanent branches, read from its config."""
    from vibey_gh.config import load_config

    try:
        cfg = load_config(path)
    except (OSError, ValueError, KeyError, TypeError):
        # A broken or unreadable config must not widen what we push: fall back to
        # the conventional permanent-branch names rather than protecting nothing.
        return ("develop", "main")
    return (cfg.integration_branch, cfg.release_branch)


def sync_repo(
    path: Path,
    protected: tuple[str, ...] = (),
    check: bool = True,
) -> SyncOutcome:
    """One pass over one repository: push its current branch if it is safely green."""
    name = path.name
    branch = _git(path, "branch", "--show-current").stdout.strip()
    if not branch:
        return SyncOutcome(name, "-", "skipped", "detached or no branch")
    # The lease expectation is captured BEFORE the fetch. A fetch updates the
    # remote-tracking ref, and a bare --force-with-lease checks against that updated
    # ref — which silently defeats the lease and clobbers remote work this machine
    # has not integrated. The regression test proved it: with the bare form, "their"
    # commit was overwritten. The explicit lease pins the expectation to what we had
    # actually seen, so unseen remote work always refuses the push.
    lease = _git(path, "rev-parse", "@{u}").stdout.strip()
    _git(path, "fetch", "--quiet", "origin")
    guarded = protected or _default_protected(path)
    if branch in guarded:
        return SyncOutcome(name, branch, "skipped", "protected branch")
    if _git(path, "status", "--porcelain").stdout.strip():
        return SyncOutcome(name, branch, "skipped", "dirty working tree")
    counted = _git(path, "rev-list", "--count", "@{u}..HEAD")
    ahead = int(counted.stdout.strip()) if counted.returncode == 0 else 0
    if ahead == 0:
        return SyncOutcome(name, branch, "skipped", "nothing ahead")
    if check:
        verdict = subprocess.run(
            ["vibey-gh", "check"], cwd=path, capture_output=True, text=True, check=False
        )
        if verdict.returncode != 0:
            return SyncOutcome(name, branch, "held", "provenance check failed", ahead)
    lease_arg = f"--force-with-lease=refs/heads/{branch}:{lease}" if lease else "--force-with-lease"
    pushed = _git(path, "push", lease_arg, "--quiet", "origin", branch)
    if pushed.returncode == 0:
        return SyncOutcome(name, branch, "pushed", ahead=ahead)
    reason = " ".join((pushed.stderr or pushed.stdout).split())[:120]
    return SyncOutcome(name, branch, "refused", reason or "push rejected", ahead)


def run(
    paths: list[Path],
    interval: int = 120,
    once: bool = False,
    protected: tuple[str, ...] = (),
    check: bool = True,
    report=print,
    sleep=time.sleep,
) -> None:
    """The loop. `once` makes a single pass — for tests, cron, and CI smoke."""
    while True:
        for path in paths:
            outcome = sync_repo(path, protected=protected, check=check)
            if outcome.action != "skipped":
                report(str(outcome))
        if once:
            return
        sleep(interval)
