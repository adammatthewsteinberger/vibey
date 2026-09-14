# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

import os

import pytest

from agyloop.domain.classify import TurnSignals, classify_explained


@pytest.mark.live
def test_live_classify_harness_skips_without_key() -> None:
    """Opt-in with ``pytest -m live``. Does not force a 429 / burn quota."""
    if not os.environ.get("GOOGLE_API_KEY"):
        pytest.skip("GOOGLE_API_KEY not set")
    result = classify_explained(
        TurnSignals(
            http_status=429,
            status="RESOURCE_EXHAUSTED",
            message="Resource has been exhausted (e.g. check quota).",
        )
    )
    assert result.rung == "unknown_window"
