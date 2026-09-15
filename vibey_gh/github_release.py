# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Idempotent, immutable tagging and GitHub Release publication."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass

from vibey_gh.config import GhConfig
from vibey_gh.versioning import read_version


@dataclass(frozen=True)
class ReleaseResult:
    tag: str
    target: str
    tag_created: bool
    release_created: bool


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(args), cwd=None, capture_output=True, text=True, check=False)


def _repository() -> str:
    run = _run("gh", "repo", "view", "--json", "nameWithOwner")
    if run.returncode:
        raise RuntimeError(f"could not identify GitHub repository: {run.stderr.strip()}")
    return str(json.loads(run.stdout)["nameWithOwner"])


def publish(cfg: GhConfig, *, target: str, version: str | None = None) -> ReleaseResult:
    """Create, but never move or delete, the version tag and its GitHub Release.

    A release-branch push that carries no version bump already tags the exact same
    version at an earlier commit. That is a no-op, not a failure, unless
    `require_new_version` opts the adopting repository into treating it as one.
    """
    if not cfg.github_release.enabled:
        raise RuntimeError("GitHub Releases are disabled by [github_release]")
    version = version or read_version(cfg)
    tag = f"{cfg.github_release.tag_prefix}{version}"
    repository = _repository()

    existing = _run("gh", "api", f"repos/{repository}/git/ref/tags/{tag}")
    tag_created = False
    if existing.returncode == 0:
        tagged = str(json.loads(existing.stdout)["object"]["sha"])
        if tagged != target:
            if cfg.github_release.require_new_version:
                raise RuntimeError(f"refusing to move existing tag {tag}: {tagged} != {target}")
            return ReleaseResult(tag, tagged, False, False)
    else:
        create = _run(
            "gh",
            "api",
            f"repos/{repository}/git/refs",
            "--method",
            "POST",
            "--field",
            f"ref=refs/tags/{tag}",
            "--field",
            f"sha={target}",
        )
        if create.returncode:
            raise RuntimeError(f"could not create immutable tag {tag}: {create.stderr.strip()}")
        tag_created = True

    release = _run("gh", "release", "view", tag, "--repo", repository)
    release_created = False
    if release.returncode:
        command = [
            "gh",
            "release",
            "create",
            tag,
            "--repo",
            repository,
            "--target",
            target,
            "--title",
            tag,
        ]
        if cfg.github_release.generate_notes:
            command.append("--generate-notes")
        created = _run(*command)
        if created.returncode:
            raise RuntimeError(
                f"tag {tag} exists but GitHub Release creation failed: {created.stderr.strip()}"
            )
        release_created = True
    return ReleaseResult(tag, target, tag_created, release_created)
