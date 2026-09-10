# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agyloop.domain.classify import TurnSignals, classify_explained

_FIXTURES = Path(__file__).parents[1] / "fixtures" / "errors"


@pytest.mark.parametrize("path", sorted(_FIXTURES.glob("*.json")))
def test_golden_error_fixtures(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    signals = TurnSignals(**data["signals"])
    result = classify_explained(signals)
    assert type(result.state).__name__ == data["expected_state"]
    assert result.rung == data["expected_rung"]
    expected_kind = data.get("expected_rate_limit_type")
    if expected_kind is not None:
        assert getattr(result.state, "rate_limit_type", None) == expected_kind
