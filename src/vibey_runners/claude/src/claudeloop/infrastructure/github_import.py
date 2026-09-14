# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""GitHub issue / repo import helpers for run resources."""

from __future__ import annotations

import json
import os
import subprocess  # nosec B404 - fixed argv to `gh api`, no shell
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True, slots=True)
class ImportedIssue:
    owner: str
    repo: str
    number: int
    title: str
    body: str
    url: str

    def as_prompt_fragment(self) -> str:
        return (
            f"Imported GitHub issue {self.owner}/{self.repo}#{self.number}: {self.title}\n\n"
            f"{self.body}\n\nSource: {self.url}"
        )


def parse_issue_ref(ref: str) -> tuple[str, str, int]:
    """Parse OWNER/REPO#N."""
    raw = ref.strip()
    if "#" not in raw or "/" not in raw:
        raise ValueError(f"expected OWNER/REPO#N, got {ref!r}")
    repo_part, num_part = raw.rsplit("#", 1)
    owner, repo = repo_part.split("/", 1)
    if not owner or not repo or not num_part.isdigit():
        raise ValueError(f"expected OWNER/REPO#N, got {ref!r}")
    return owner, repo, int(num_part)


def parse_repo_ref(ref: str) -> tuple[str, str, str | None]:
    """Parse OWNER/REPO or OWNER/REPO@REF."""
    raw = ref.strip()
    at_ref: str | None = None
    if "@" in raw:
        raw, at_ref = raw.rsplit("@", 1)
    if "/" not in raw:
        raise ValueError(f"expected OWNER/REPO[@REF], got {ref!r}")
    owner, repo = raw.split("/", 1)
    if not owner or not repo:
        raise ValueError(f"expected OWNER/REPO[@REF], got {ref!r}")
    return owner, repo, at_ref or None


def import_github_issue(ref: str) -> ImportedIssue:
    owner, repo, number = parse_issue_ref(ref)
    # Prefer `gh` when available (uses user auth); fall back to API + token.
    try:
        proc = subprocess.run(  # nosec B603 B607 - fixed argv, no shell
            [
                "gh",
                "api",
                f"repos/{owner}/{repo}/issues/{number}",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        data = json.loads(proc.stdout)
    except (FileNotFoundError, subprocess.CalledProcessError, json.JSONDecodeError):
        data = _fetch_issue_api(owner, repo, number)
    return ImportedIssue(
        owner=owner,
        repo=repo,
        number=number,
        title=str(data.get("title") or ""),
        body=str(data.get("body") or ""),
        url=str(data.get("html_url") or f"https://github.com/{owner}/{repo}/issues/{number}"),
    )


def _fetch_issue_api(owner: str, repo: str, number: int) -> dict[str, object]:
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "claudeloop",
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(url, headers=headers)  # noqa: S310 - HTTPS GitHub API only
    try:
        with urlopen(req, timeout=60) as resp:  # nosec B310 - HTTPS api.github.com only
            parsed: dict[str, object] = json.loads(resp.read().decode("utf-8"))
            return parsed
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"failed to import {owner}/{repo}#{number}: {exc}. "
            "Install/authenticate `gh`, or set GITHUB_TOKEN / GH_TOKEN."
        ) from exc


def materialize_issue_attachment(issue: ImportedIssue, attachments_dir: Path) -> Path:
    attachments_dir.mkdir(parents=True, exist_ok=True)
    path = attachments_dir / f"github-issue-{issue.owner}-{issue.repo}-{issue.number}.md"
    path.write_text(
        f"# {issue.title}\n\n{issue.body}\n\nSource: {issue.url}\n",
        encoding="utf-8",
    )
    return path
