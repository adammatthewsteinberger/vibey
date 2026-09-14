# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Shared fixtures for deterministic system tests (real FS/git, no live Gemini)."""

from __future__ import annotations

import subprocess  # nosec B404 - fixed-argument git init only
from pathlib import Path

import pytest


@pytest.fixture
def git_sandbox(tmp_path: Path) -> Path:
    repo = tmp_path / "sandbox"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "agyloop-system@example.com"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "agyloop system"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    (repo / "README.md").write_text("sandbox\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "init"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    return repo
