# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Fixtures shared by the live test suite. See docs/guides/live-testing.md.

Isolation and cost control:
- Every live test runs in a fresh temp git repo (tmp_path), never a real
  project.
- Paid tests (marker: `live and paid`) are additionally skipped unless
  --run-paid-live is passed, so a plain `pytest -m live` never spends tokens.
- `pytest.ini`'s default addopts is `-m "not live"`, so neither the free nor
  the paid tier runs on a bare `pytest` invocation or in CI.
"""

from __future__ import annotations

import subprocess  # nosec B404 - fixed-argument git init only, never shell=True
from pathlib import Path

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-paid-live",
        action="store_true",
        default=False,
        help="Additionally run tests marked 'paid' that spend real tokens/turns "
        "against your Claude account.",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--run-paid-live"):
        return
    skip_paid = pytest.mark.skip(reason="needs --run-paid-live (spends real tokens)")
    for item in items:
        if "paid" in item.keywords:
            item.add_marker(skip_paid)


@pytest.fixture
def sandbox_repo(tmp_path: Path) -> Path:
    """A fresh, empty git repo — never a real project directory — so any
    session `claudeloop` creates during a live test is namespaced away from
    real work and easy to spot in `claudeloop sessions` output."""
    repo = tmp_path / "sandbox"
    repo.mkdir()
    subprocess.run(  # nosec B603 B607
        ["git", "init", "-q"], cwd=repo, check=True, capture_output=True
    )
    subprocess.run(  # nosec B603 B607
        ["git", "config", "user.email", "claudeloop-live-test@example.com"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(  # nosec B603 B607
        ["git", "config", "user.name", "claudeloop live test"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    return repo
