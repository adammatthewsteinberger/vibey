# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""`.dockerignore` must never exclude something the Dockerfile copies.

This is a silent failure, which is why it is worth a test. `**/build` looks like an
obviously correct thing to ignore -- until it matches `src/vibey/infrastructure/build/`,
which is a package. The image then builds perfectly clean and dies at runtime on
`vibey --version` with `ModuleNotFoundError: No module named 'vibey.infrastructure.build'`,
and nothing between the pattern and the crash mentions the pattern.

Docker resolves these patterns itself, so this re-implements just enough of that matching
to answer one question: of the tracked files the Dockerfile copies, is any excluded?
"""

from __future__ import annotations

import fnmatch
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DOCKERFILE = REPO / "deploy" / "docker" / "Dockerfile"
DOCKERIGNORE = REPO / ".dockerignore"


def _patterns() -> list[str]:
    return [
        line.strip()
        for line in DOCKERIGNORE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def _copied_prefixes() -> list[str]:
    """Every build-context path named by a `COPY` that is not `--from` another stage."""
    prefixes: list[str] = []
    for line in DOCKERFILE.read_text(encoding="utf-8").splitlines():
        match = re.match(r"\s*COPY\s+(?!--from)(.*)", line)
        if not match:
            continue
        # The last token is the destination; everything before it is a source.
        sources = match.group(1).split()[:-1]
        prefixes.extend(source.rstrip("/") for source in sources if source != ".")
    return prefixes


def _excluded_by(path: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        if pattern.startswith("**/"):
            tail = pattern[3:]
            if any(fnmatch.fnmatch(segment, tail) for segment in path.split("/")):
                return pattern
        else:
            anchored = pattern.lstrip("/")
            if path == anchored or path.startswith(anchored + "/"):
                return pattern
    return None


def _tracked() -> list[str]:
    done = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True)
    return done.stdout.split()


def test_the_dockerfile_copies_nothing_that_dockerignore_drops() -> None:
    patterns = _patterns()
    prefixes = _copied_prefixes()
    assert prefixes, "no COPY sources parsed — has the Dockerfile moved?"

    needed = [
        path
        for path in _tracked()
        if any(path == prefix or path.startswith(prefix + "/") for prefix in prefixes)
    ]
    assert needed, f"no tracked file matches any COPY source {prefixes}"

    dropped = [(path, _excluded_by(path, patterns)) for path in needed]
    dropped = [(path, pattern) for path, pattern in dropped if pattern]
    assert not dropped, (
        "these files are copied by the Dockerfile but excluded from the build context: "
        + ", ".join(f"{path} (by {pattern!r})" for path, pattern in dropped[:10])
    )


def test_the_package_that_taught_us_this_is_still_included() -> None:
    """Named explicitly: `src/vibey/infrastructure/build/` is a package, not build output."""
    assert _excluded_by("src/vibey/infrastructure/build/__init__.py", _patterns()) is None
