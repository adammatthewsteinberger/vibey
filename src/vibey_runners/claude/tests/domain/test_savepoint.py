# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for domain/savepoint.py — SavePointRef and UnwindResult.

These value objects are already exercised indirectly by tests/application/
and tests/infrastructure/, but CI measures domain coverage from tests/domain/
alone (per-layer gate, not aggregate), so their own invariants need direct
domain-level tests too.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from claudeloop.domain.savepoint import SavePointRef, UnwindResult


def _ref(**overrides: object) -> SavePointRef:
    defaults: dict[str, object] = {
        "n": 1,
        "ref": "refs/claudeloop/run-1/1",
        "sha": "abc123",
        "label": "turn-1",
        "at": datetime(2026, 1, 1, tzinfo=timezone.utc),
    }
    defaults.update(overrides)
    return SavePointRef(**defaults)  # type: ignore[arg-type]


class TestSavePointRef:
    def test_valid_construction(self) -> None:
        ref = _ref()
        assert ref.n == 1
        assert ref.plan_item is None
        assert ref.committed is False

    def test_optional_fields(self) -> None:
        ref = _ref(plan_item="task-a", committed=True)
        assert ref.plan_item == "task-a"
        assert ref.committed is True

    def test_rejects_non_positive_n(self) -> None:
        with pytest.raises(ValueError, match="save point number must be >= 1"):
            _ref(n=0)

    def test_rejects_blank_ref(self) -> None:
        with pytest.raises(ValueError, match="save point ref must not be blank"):
            _ref(ref="   ")

    def test_rejects_blank_sha(self) -> None:
        with pytest.raises(ValueError, match="save point sha must not be blank"):
            _ref(sha="")


class TestUnwindResult:
    def test_construction(self) -> None:
        target = _ref()
        result = UnwindResult(to=target, backup_ref="refs/backup/1", restored_sha="abc123")
        assert result.to is target
        assert result.backup_ref == "refs/backup/1"
        assert result.restored_sha == "abc123"

    def test_backup_ref_optional(self) -> None:
        result = UnwindResult(to=_ref(), backup_ref=None, restored_sha="abc123")
        assert result.backup_ref is None
