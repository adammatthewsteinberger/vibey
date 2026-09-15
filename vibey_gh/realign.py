# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Realign the integration branch with the release branch after a release.

When the release branch is REBASE-merged, its commits are rewritten copies with new SHAs,
so the integration branch's tip is never an ancestor of it and a fast-forward is
impossible. Yet a ruleset with a strict up-to-date policy treats the integration branch as
behind, which blocks the next promotion. It has to be realigned.

The guard is TREE EQUALITY, not ancestry: this runs only when a diff between the two
branches is empty, so it converges two identical contents onto one history and cannot
discard work. If the integration branch has anything the release branch does not, it is
left alone and says so.
"""

from __future__ import annotations

import subprocess

from vibey_gh import reconcile
from vibey_gh.config import GhConfig, load_config


def _git(cfg: GhConfig, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cfg.root, capture_output=True, text=True, check=False)


def realign(cfg: GhConfig | None = None) -> tuple[bool, str]:
    """(changed, message). Raises nothing; the caller decides whether a refusal is fatal."""
    cfg = cfg or load_config()
    dev, rel = f"origin/{cfg.integration_branch}", f"origin/{cfg.release_branch}"
    _git(cfg, "fetch", "--quiet", "origin", cfg.integration_branch, cfg.release_branch)

    if _git(cfg, "diff", "--quiet", rel, dev).returncode != 0:
        return False, (
            f"{cfg.integration_branch} has content {cfg.release_branch} does not; "
            "left untouched. Promote it with a pull request."
        )

    before = _git(cfg, "rev-parse", dev).stdout.strip()
    if before == _git(cfg, "rev-parse", rel).stdout.strip():
        return False, f"{cfg.integration_branch} already matches {cfg.release_branch}"

    # --force-with-lease pinned to the SHA just read: anything landing in between refuses
    # the push rather than being silently overwritten.
    push = _git(
        cfg,
        "push",
        f"--force-with-lease=refs/heads/{cfg.integration_branch}:{before}",
        "origin",
        f"{rel}:refs/heads/{cfg.integration_branch}",
    )
    if push.returncode == 0:
        message = (
            f"{cfg.integration_branch} realigned to {cfg.release_branch} — "
            "identical trees, histories converged"
        )
        # The rewrite just replaced commits that open topic branches may be built on, so
        # reconcile them here rather than leaving each one to discover a conflict it did
        # not cause. Doing it inside `realign` means every adopter gets it wherever they
        # already call this, with no workflow change.
        try:
            for outcome in reconcile.reconcile(cfg):
                message += f"\n  {outcome['pr']} ({outcome['branch']}): {outcome['action']}"
        except (OSError, RuntimeError) as exc:
            # The realign itself has already succeeded and must stand. Reconciliation is a
            # follow-up that needs GitHub credentials this context may not have, and a
            # branch left unreconciled is a nuisance, not a reason to report the realign
            # as failed and leave the caller believing the branches never converged.
            message += f"\n  branches were not reconciled: {exc}"
        return True, message
    raise RuntimeError(
        f"could not realign {cfg.integration_branch}, so it is now divergent and the next "
        f"promotion will be blocked. If the token lacks the admin role the push is refused "
        f"by the ruleset. By hand: git push --force-with-lease origin "
        f"{cfg.release_branch}:{cfg.integration_branch}\n{push.stderr.strip()}"
    )
