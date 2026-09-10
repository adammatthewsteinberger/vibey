# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
import os
from collections.abc import Iterator
from datetime import UTC, datetime
from unittest.mock import patch

import pytest

FROZEN_NOW = datetime(2026, 8, 13, 18, 0, tzinfo=UTC)


@pytest.fixture
def fake_now() -> Iterator[datetime]:
    """Freeze the classifier clock so RPD reset arithmetic is deterministic."""
    with patch("agyloop.domain.classify._current_time", return_value=FROZEN_NOW):
        yield FROZEN_NOW


@pytest.fixture(autouse=True)
def _skip_harness_retarget_by_default(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Unit tests must not copy the 99MB bundled localharness into ~/.cache, and should not
    inherit ambient AGYLOOP_* env."""
    for key in list(os.environ):
        if key.startswith("AGYLOOP_"):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("AGYLOOP_SKIP_HARNESS_RETARGET", "1")
    monkeypatch.setenv("AGYLOOP_GEMINI_REWRITE_PROXY", "0")
    yield
    from agyloop.infrastructure.agent.harness_retarget import restore_harness

    restore_harness()


def pytest_configure(config: pytest.Config) -> None:
    """Let ``pytest -m system`` override addopts' default marker exclusion."""
    cli_markers: list[str] = []
    args = config.invocation_params.args
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "-m" and index + 1 < len(args):
            cli_markers.append(args[index + 1])
            index += 2
            continue
        if arg.startswith("-m") and arg != "-m":
            cli_markers.append(arg[2:])
        index += 1
    if cli_markers:
        config.option.markexpr = " and ".join(cli_markers)
