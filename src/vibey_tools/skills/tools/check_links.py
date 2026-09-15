#!/usr/bin/env python3
# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Verify documentation links without touching the network.

Three surfaces render this project's Markdown, each against a different base URL:

    GitHub repo view   https://github.com/<slug>/blob/main/...   relative links work
    PyPI project page  https://pypi.org/project/<name>/          relative links BREAK
    Pages site         https://<org>.github.io/<name>/           relative links work in docs/

1.0.0 shipped `](.claude-plugin/marketplace.json)` in README.md, which PyPI resolved to
`https://pypi.org/project/<name>/.claude-plugin/marketplace.json` — a 404
that looked fine on GitHub. That class of bug is invisible to a human reviewer and to
`mkdocs build`, so it gets its own check.

Rules enforced:

  1. Root Markdown (README, CONTRIBUTING, CLAUDE, SECURITY, CODE_OF_CONDUCT) must contain
     NO relative links — PyPI and the Pages site cannot resolve them.
  2. Every absolute URL into this repo (`/blob/main/<p>` or `/tree/main/<p>`) must name a
     path that actually exists, and blob-vs-tree must match file-vs-directory.
  3. Relative links inside docs/ must resolve on disk (mkdocs --strict also covers this,
     but this runs without installing mkdocs).
  4. No link may reference the former publishing org (the project was developed as
     TheViziusGroup/vibe-engineering-skills and republished under the maintainer's own
     account as vibey-skills). The only file allowed to name the old coordinates is
     NOTICE.md, which exists precisely to record the attribution; everywhere else a
     stale org URL is a bug — every such link must point at the canonical slug below.

Deliberately hermetic: no HTTP requests. A link checker that needs the network is a link
checker that gets disabled the first time CI flakes. Reachability of third-party URLs is out
of scope; correctness of our own paths is not.

Exit 0 clean, 1 on any violation.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SLUG = "adammatthewsteinberger/vibey-skills"

# The pre-rename coordinates. Attribution lives in NOTICE.md; nothing else may link here.
FORMER_ORG = "TheViziusGroup"
FORMER_ORG_ALLOWED = {"NOTICE.md"}

ROOT_DOCS = [
    "README.md",
    "CONTRIBUTING.md",
    "CLAUDE.md",
    "SECURITY.md",
    "CODE_OF_CONDUCT.md",
]

LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
# Only `main` is matched, per CLAUDE.md. Note the failure mode if that ever changes: this
# pattern *selects* which links get checked, so a self-link naming any other branch is not
# reported as wrong — it is silently skipped. Repointing the plugin table at `develop` once
# left 79 links unvalidated while this checker still printed "ok".
SELF_PATH = re.compile(rf"https://github\.com/{re.escape(SLUG)}/(blob|tree)/main/([^)#\s]+)")

# Capture the repo name, then compare it exactly. A negative lookahead was tried first and
# was wrong: `(?!<repo>(?:[/.)]|$))` treats `$` as end-of-STRING, not end-of-line, so a URL
# followed by `"` or a newline slipped past and every occurrence in mkdocs.yml and
# pyproject.toml was reported as a foreign repo. Capture-then-compare cannot have that class
# of bug.
#
# Sibling repositories under the same owner (the README's "Related projects" block) are
# legitimate, so the current org is NOT policed for foreign repos — only the former org is.
FORMER_ORG_REPO = re.compile(rf"https://github\.com/{re.escape(FORMER_ORG)}/([A-Za-z0-9._-]+)")
FORMER_PAGES = re.compile(rf"https://{re.escape(FORMER_ORG.lower())}\.github\.io/")

# Only tracked files matter: .claudeloop/ holds the migration plan and run report, which
# reference internal repos on purpose and are gitignored precisely so they never ship.
SKIP_DIRS = {".git", ".claudeloop", ".remember", "archive", "site", "dist", "build", ".venv"}


def is_external(target: str) -> bool:
    return target.startswith(("http://", "https://", "mailto:", "tel:"))


def check_root_docs_are_absolute(problems: list[str]) -> None:
    for name in ROOT_DOCS:
        p = REPO / name
        if not p.is_file():
            continue
        for target in LINK.findall(p.read_text(encoding="utf-8")):
            if target.startswith("#") or is_external(target):
                continue
            problems.append(
                f"{name}: relative link `{target}` — breaks on PyPI and the Pages site; "
                f"use https://github.com/{SLUG}/blob/main/{target.lstrip('./')}"
            )


def scanned_markdown() -> list[Path]:
    """Markdown files that will actually be published."""
    return [p for p in REPO.rglob("*.md") if not SKIP_DIRS.intersection(p.relative_to(REPO).parts)]


def check_self_paths_exist(problems: list[str]) -> None:
    for p in scanned_markdown():
        rel = p.relative_to(REPO)
        for kind, path in SELF_PATH.findall(p.read_text(encoding="utf-8")):
            target = REPO / path
            if not target.exists():
                problems.append(f"{rel}: links to `{path}` via /{kind}/, which does not exist")
            elif kind == "blob" and target.is_dir():
                problems.append(
                    f"{rel}: `{path}` is a directory but linked with /blob/ (use /tree/)"
                )
            elif kind == "tree" and target.is_file():
                problems.append(f"{rel}: `{path}` is a file but linked with /tree/ (use /blob/)")


def check_docs_relative_links(problems: list[str]) -> None:
    docs = REPO / "docs"
    if not docs.is_dir():
        return
    for p in docs.rglob("*.md"):
        rel = p.relative_to(REPO)
        for target in LINK.findall(p.read_text(encoding="utf-8")):
            if target.startswith("#") or is_external(target):
                continue
            path = target.partition("#")[0]
            if not path:
                continue
            # A directory-style target (`reference/`) is resolved by mkdocs to that
            # section's index page; accept it when the generator will produce one.
            if path.endswith("/"):
                continue
            resolved = (p.parent / path).resolve()
            if resolved.exists():
                continue
            # Generated pages do not exist on disk until mkdocs runs.
            if "reference/" in target:
                continue
            problems.append(f"{rel}: relative link `{target}` does not resolve on disk")


def check_no_former_org_links(problems: list[str]) -> None:
    for p in scanned_markdown() + [REPO / "mkdocs.yml", REPO / "pyproject.toml"]:
        if not p.is_file():
            continue
        rel = p.relative_to(REPO)
        if str(rel) in FORMER_ORG_ALLOWED:
            continue
        text = p.read_text(encoding="utf-8")
        for repo in sorted(set(FORMER_ORG_REPO.findall(text))):
            problems.append(
                f"{rel}: links to the former publishing org (`{FORMER_ORG}/{repo}`) — "
                f"use https://github.com/{SLUG} (attribution belongs in NOTICE.md only)"
            )
        if FORMER_PAGES.search(text):
            problems.append(
                f"{rel}: links to the former Pages site — "
                f"use https://{SLUG.split('/')[0]}.github.io/{SLUG.split('/')[1]}/"
            )


def main() -> int:
    problems: list[str] = []
    check_root_docs_are_absolute(problems)
    check_self_paths_exist(problems)
    check_docs_relative_links(problems)
    check_no_former_org_links(problems)

    if problems:
        print(f"check_links: {len(problems)} problem(s)\n", file=sys.stderr)
        for pb in problems:
            print(f"  - {pb}", file=sys.stderr)
        return 1

    print("check_links: ok — root docs fully absolute, every repo path resolves")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
