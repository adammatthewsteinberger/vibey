# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Shared fixtures.

The suite must behave the same on a laptop and inside GitHub Actions. Actions exports a
number of variables that the code under test reads, and a test that silently changes
behaviour because of one of them is worse than a failing test: it hides a branch and,
in this case, writes into the real job summary.
"""

from __future__ import annotations

import pytest

# Variables Actions sets that this tool reads. Cleared for every test; a test that wants
# one sets it explicitly, which also documents that it is what is under test.
_ACTIONS_ENV = ("GITHUB_STEP_SUMMARY", "GITHUB_RUN_NUMBER", "GITHUB_OUTPUT")


@pytest.fixture(autouse=True)
def _no_ambient_actions_env(monkeypatch):
    for name in _ACTIONS_ENV:
        monkeypatch.delenv(name, raising=False)
