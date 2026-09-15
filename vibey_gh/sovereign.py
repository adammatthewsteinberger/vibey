# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Sovereign readiness (doctrine 8.a): is the free path actually able to take this?

Doctrine 8.a makes the 100% sovereign path the *preferred* way to run, not the
fallback of last resort. Acting on that safely needs one fact a workflow cannot
otherwise learn: whether a runner carrying the sovereign label is online **now**.

Without that fact the compliant-looking change is a trap, and it is worth naming
because it has already cost this project a production outage in another costume.
`review-fallback` runs on a self-hosted runner. Disabled, the job *skips*, and a
skipped job counts as completed. Enabled with no runner online, it **queues** — not
failed, not cancelled, simply pending. The job that publishes the required
`PR automation / gate` check needs it and is guarded by `always()`, which waits for
needs to *complete*. So switching the sovereign lane on by default, with no probe,
blocks every pull request permanently and silently, with no red check to point at.

**Asking GitHub is not the answer**, and not only because it is unavailable: the
runners API needs `administration: read`, which `GITHUB_TOKEN` cannot be granted at
all. Depending on a privileged forge API to discover whether one's *own* machine is
up would also invert 8.a — it makes the sovereign lane's availability contingent on
a counterparty's capability, which is precisely what doctrine 10.a warns about.

So the machine says so itself, in the plainest artifact both sides already share: a
git ref. The operator's supervisor calls `beat()` on a timer, which pushes an empty
commit to a ref outside `refs/heads/` — no branch, nothing for doctrine 9.a's tidy
pass to find. Any job with ordinary `contents: read` fetches that ref and reads its
timestamp. Fresh means ready.

The failure direction is deliberate: anything unreadable, unparseable, or stale
reports **not ready**. A missing heartbeat costs a sovereign review; a false
positive costs every gate in the repository.
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass

__all__ = ["Readiness", "beat", "probe"]


@dataclass(frozen=True)
class Readiness:
    """Whether the sovereign lane may be scheduled, and why."""

    ready: bool
    reason: str
    age_seconds: int | None = None


def _run(*cmd: str, cwd: str | None = None) -> tuple[int, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False, cwd=cwd)
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""
    return proc.returncode, proc.stdout.strip()


def beat(ref: str, *, remote: str = "origin", cwd: str | None = None) -> Readiness:
    """Publish a heartbeat: the operator's machine saying "I am up" to the forge.

    An empty commit pushed to a ref outside `refs/heads/`, so it is not a branch and
    never becomes something a human or a tidy pass has to reason about. Force-pushed
    because a heartbeat has no history worth keeping — only its most recent instant
    means anything.

    `--no-verify` is load-bearing, not a shortcut. A pre-push gate exists to judge code
    on its way off the machine, and this pushes an **empty tree with no parents** —
    there is no diff to lint, nothing to type-check, no dependency set to audit. Paying
    that gate anyway is not merely wasteful: measured against a real project whose
    pre-push stage runs the test suite, then a coverage pass that runs the suite a
    second time, then a network dependency audit, a heartbeat ran past two minutes
    without finishing, against **1.2 seconds** with the gate skipped. A timer that cannot
    finish inside its own interval is not a heartbeat, and in a loop over several
    repositories it stalls every repository queued behind it too.
    """
    code, tree = _run("git", "hash-object", "-t", "tree", "/dev/null", cwd=cwd)
    if code != 0 or not tree:
        return Readiness(False, "could not write the empty tree object; is this a git repository?")
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    code, commit = _run("git", "commit-tree", tree, "-m", f"sovereign heartbeat {stamp}", cwd=cwd)
    if code != 0 or not commit:
        return Readiness(False, "could not create the heartbeat commit")
    code, _ = _run("git", "push", "--force", "--no-verify", remote, f"{commit}:{ref}", cwd=cwd)
    if code != 0:
        return Readiness(False, f"could not push the heartbeat to {remote} {ref}")
    return Readiness(True, f"heartbeat published to {ref} at {stamp}", age_seconds=0)


def probe(
    ref: str,
    *,
    max_age_minutes: int,
    remote: str = "origin",
    cwd: str | None = None,
    now: float | None = None,
) -> Readiness:
    """Read the heartbeat and decide whether the sovereign lane may be scheduled.

    Every failure path answers "not ready" rather than raising: a probe that throws
    inside a workflow step is a red job, and a red job here would be a *worse* outcome
    than the absent sovereign review it is reporting.
    """
    code, _ = _run("git", "fetch", "--depth=1", remote, ref, cwd=cwd)
    if code != 0:
        return Readiness(False, f"no sovereign heartbeat at {ref} — the local lane is not offered")
    code, raw = _run("git", "log", "-1", "--format=%ct", "FETCH_HEAD", cwd=cwd)
    if code != 0 or not raw.isdigit():
        return Readiness(False, "the heartbeat ref carries no readable timestamp")
    age = int((time.time() if now is None else now) - int(raw))
    if age < 0:
        return Readiness(False, "the heartbeat is dated in the future; refusing to trust it", age)
    if age > max_age_minutes * 60:
        return Readiness(
            False,
            f"the sovereign heartbeat is {age // 60}m old, past the {max_age_minutes}m"
            " window — treating the runner as offline",
            age,
        )
    return Readiness(True, f"sovereign runner heartbeat is {age}s old", age)
