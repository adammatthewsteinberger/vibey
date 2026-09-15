# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""`gh` CLI access for storm-mode repo discovery and backlog reading."""

import json
import shutil
import subprocess  # nosec B404
from typing import Any

from qwenloop.domain.model import RepoItem

_TIMEOUT_SECONDS = 30


def _run_gh(argv: list[str]) -> list[Any] | None:
    """Run a `gh ... --json ...` command and parse its JSON array, or None on any failure.

    None means "could not read this" (gh missing, the call failed, the repo has issues
    disabled, ...); it is distinct from an empty list, which means gh succeeded and
    reported zero results.
    """
    gh = shutil.which("gh")
    if gh is None:
        return None
    try:
        # The executable is resolved to an absolute path; no shell is involved, and every
        # argument is either a fixed literal or a caller-supplied name passed as its own
        # argv entry, never interpolated into a shell string.
        result = subprocess.run(  # nosec B603
            [gh, *argv],
            check=True,
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_SECONDS,
        )
        payload = json.loads(result.stdout or "[]")
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    return payload if isinstance(payload, list) else None


def list_repo_names(owner: str) -> list[str] | None:
    """Non-archived, non-fork repo names `gh` reports under `owner`; None if the call failed."""
    payload = _run_gh(
        ["repo", "list", owner, "--no-archived", "--source", "--json", "name", "--limit", "1000"]
    )
    if payload is None:
        return None
    return [str(entry["name"]) for entry in payload if isinstance(entry, dict) and "name" in entry]


def _list_open_items(owner: str, repo: str, kind: str) -> list[RepoItem] | None:
    payload = _run_gh(
        [kind, "list", "-R", f"{owner}/{repo}", "--state", "open", "--json", "number,title,body"]
    )
    if payload is None:
        return None
    items: list[RepoItem] = []
    for entry in payload:
        if not isinstance(entry, dict) or "number" not in entry or "title" not in entry:
            continue
        items.append(
            RepoItem(
                number=int(entry["number"]),
                title=str(entry["title"]),
                body=str(entry.get("body") or ""),
            )
        )
    return items


def list_open_issues(owner: str, repo: str) -> list[RepoItem] | None:
    """Open issues on `owner/repo`; None if the call failed (including issues disabled)."""
    return _list_open_items(owner, repo, "issue")


def list_open_pull_requests(owner: str, repo: str) -> list[RepoItem] | None:
    """Open pull requests on `owner/repo`; None if the call failed."""
    return _list_open_items(owner, repo, "pr")
