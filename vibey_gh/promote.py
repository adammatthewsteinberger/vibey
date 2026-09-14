# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Promote the integration branch to the release branch.

This is the half of the flow that was missing. The merge train fills the integration
branch; something has to move it to the release branch, and doing that by hand is how a
release ends up on the wrong branch — or how an unbumped version publishes nothing.

Three things it gets right that a hand-written workflow usually does not:

**It compares by CONTENT, not by commit count.** The release branch is rebase-merged, so
its commits are rewritten copies with different SHAs; the integration branch will always
look "ahead" by some number of commits even when the two trees are identical. A diff
between them is the only honest test of whether there is anything to release.

**It derives the version before opening anything.** A PyPI upload with `skip-existing`
turns an unbumped promotion into a green run that publishes nothing, silently. `none` is a
legitimate answer — docs and CI changes reach no installed user — and the promotion still
proceeds; it just does not publish.

**It waits for the checks.** A pull request opened seconds ago has no results yet, and
merging blind is how a red build reaches the release branch.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field

from vibey_gh import versioning
from vibey_gh.config import GhConfig, load_config

DEFAULT_METHOD = "rebase"
CHECK_TIMEOUT_SECONDS = 1800


@dataclass
class Promotion:
    """What happened, in a shape a caller can print or assert on."""

    changed_files: int = 0
    version: str = ""
    bumped: str | None = None  # the derived version, or None when nothing was due
    pull_request: int | None = None
    merged: bool = False
    bypassed: bool = False
    notes: list[str] = field(default_factory=list)

    def say(self, note: str) -> None:
        self.notes.append(note)


def _git(cfg: GhConfig, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cfg.root, capture_output=True, text=True, check=False)


def _gh(cfg: GhConfig, *args: str) -> tuple[bool, str]:
    r = subprocess.run(["gh", *args], cwd=cfg.root, capture_output=True, text=True, check=False)
    return r.returncode == 0, (r.stdout or "").strip()


def open_pull_request(cfg: GhConfig) -> int | None:
    """The open promotion pull request, if there already is one."""
    ok, out = _gh(
        cfg,
        "pr",
        "list",
        "--base",
        cfg.release_branch,
        "--head",
        cfg.integration_branch,
        "--state",
        "open",
        "--json",
        "number",
        "--jq",
        '.[0].number // ""',
    )
    return int(out) if ok and out.isdigit() else None


def create_pull_request(cfg: GhConfig, body: str) -> int | None:
    ok, out = _gh(
        cfg,
        "pr",
        "create",
        "--base",
        cfg.release_branch,
        "--head",
        cfg.integration_branch,
        "--title",
        f"chore(release): {versioning.read_version(cfg)}",
        "--body",
        body,
    )
    if not ok:
        return None
    digits = "".join(c for c in out.rsplit("/", 1)[-1] if c.isdigit())
    return int(digits) if digits else None


def checks_pass(cfg: GhConfig, number: int) -> bool:
    """Block until the checks settle. `--watch` exits non-zero if any of them fail."""
    ok, _ = _gh(cfg, "pr", "checks", str(number), "--watch", "--interval", "30")
    return ok


def merge(cfg: GhConfig, number: int, method: str = DEFAULT_METHOD) -> tuple[bool, bool]:
    """(merged, bypassed). Plain merge first: a ruleset's approving-review requirement
    refuses it even for an admin's token, because bypassing is opt-in per call."""
    base = ["pr", "merge", str(number), f"--{method}"]
    if _gh(cfg, *base)[0]:
        return True, False
    return _gh(cfg, *base, "--admin")[0], True


def promote(
    cfg: GhConfig | None = None,
    *,
    dry_run: bool = False,
    method: str = DEFAULT_METHOD,
    wait: bool = False,
) -> Promotion:
    cfg = cfg or load_config()
    result = Promotion()
    integration, release = cfg.integration_branch, cfg.release_branch

    _git(cfg, "fetch", "--quiet", "origin", integration, release)
    if _git(cfg, "diff", "--quiet", f"origin/{release}", f"origin/{integration}").returncode == 0:
        result.say(f"{integration} and {release} have identical trees; nothing to promote")
        return result

    changed = _git(cfg, "diff", "--name-only", f"origin/{release}", f"origin/{integration}")
    result.changed_files = len([line for line in changed.stdout.splitlines() if line])

    # Derive the version on the integration branch, where the release will be cut from.
    _git(cfg, "checkout", "--quiet", "-B", integration, f"origin/{integration}")
    new, why = versioning.decide(cfg, f"origin/{release}")
    result.bumped = new
    result.say(f"version: {why}")

    if new and not dry_run:
        written = versioning.apply_version(cfg, new)
        _git(cfg, "add", *written)
        _git(
            cfg,
            "commit",
            "--quiet",
            "-m",
            # A Conventional Commit, because this subject does not stay on the release
            # branch: any topic branch that later merges the integration branch in pulls it
            # into its own commit range, where the provenance gate reads it like any other
            # commit and rejects it. `Release 1.23.0` blocked a pull request that way, and
            # the repair could not fix it by editing files because the problem was history.
            f"chore(release): {new}",
            "-m",
            "Version derived from what changed since the last release, so the "
            "promotion actually publishes.",
            "-m",
            cfg.trailer,
        )
        push = _git(cfg, "push", "--quiet", "origin", integration)
        if push.returncode != 0:
            # Not a warning. An unpushed bump means the promotion publishes nothing. The
            # stderr goes into the message because git names the actual refusal — hiding
            # it once turned a token-scope problem into an afternoon of guessing.
            detail = " ".join(((push.stderr or push.stdout) or "").split())[:300]
            raise RuntimeError(
                f"could not push the version bump to {integration}; promoting it would "
                "publish nothing" + (f" — {detail}" if detail else "")
            )
        result.say(f"bumped to {new} and pushed to {integration}")
        _git(cfg, "fetch", "--quiet", "origin", integration)
    elif new:
        result.say(f"dry run — would bump to {new}")
        _git(cfg, "checkout", "--quiet", "--", *cfg.version_files)

    result.version = versioning.read_version(cfg)

    if dry_run:
        result.say("dry run — stopping before opening the pull request")
        return result

    number = open_pull_request(cfg)
    if number is None:
        number = create_pull_request(cfg, _body(cfg, result))
        if number is None:
            raise RuntimeError("could not open the promotion pull request")
        result.say(f"opened #{number}")
    else:
        result.say(f"reusing #{number}")
    result.pull_request = number

    if not wait:
        result.say(f"#{number} will be merged by the event-driven PR automation gate")
        return result

    if not checks_pass(cfg, number):
        result.say(f"checks did not pass on #{number}; leaving it open")
        return result

    merged, bypassed = merge(cfg, number, method)
    result.merged, result.bypassed = merged, bypassed
    if merged:
        result.say(
            f"#{number} {method}-merged into {release}"
            + (" (review requirement bypassed)" if bypassed else "")
        )
    else:
        result.say(f"could not merge #{number}; it is open and green for a human")
    return result


def _body(cfg: GhConfig, result: Promotion) -> str:
    return (
        f"Promotion opened by `vibey-gh promote`.\n\n"
        f"{result.changed_files} file(s) differ from `{cfg.release_branch}`. The package "
        f"version is `{result.version}` — merging publishes it, and an upload skips a "
        f"version the index already holds, so a promotion nobody bumped publishes "
        f"nothing.\n\n"
        f"Merged with `--{DEFAULT_METHOD}`, which is the only method consistent with a "
        f"linear-history rule."
    )
