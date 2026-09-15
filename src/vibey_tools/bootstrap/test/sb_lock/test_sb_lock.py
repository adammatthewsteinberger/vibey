"""Tests for ``vibey_bootstrap.sb_lock``."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.sb_lock import ManagedLock, lock_for_process


@pytest.fixture(autouse=True)
def _reset() -> None:
    _reset_counters()


def test_lock_for_process_registers_and_closes() -> None:
    renewer = MagicMock()
    with patch(
        "vibey_bootstrap.sb_lock._new_auto_lock_renewer",
        return_value=renewer,
    ):
        with lock_for_process(MagicMock(), MagicMock()):
            renewer.register.assert_called_once()
            renewer.close.assert_not_called()
        renewer.close.assert_called_once()
    assert counter_snapshot().get("sb_lock.renewer_started", 0) == 1


def test_lock_for_process_closes_on_exception() -> None:
    renewer = MagicMock()
    with patch(
        "vibey_bootstrap.sb_lock._new_auto_lock_renewer",
        return_value=renewer,
    ):
        with pytest.raises(RuntimeError):
            with lock_for_process(MagicMock(), MagicMock()):
                raise RuntimeError("boom")
        renewer.close.assert_called_once()


def test_lock_for_process_swallows_construction_failure() -> None:
    def _bad() -> Any:
        raise RuntimeError("no AutoLockRenewer available")

    with patch(
        "vibey_bootstrap.sb_lock._new_auto_lock_renewer",
        side_effect=_bad,
    ):
        # Must not raise — renewer is defensive, not a correctness gate
        with lock_for_process(MagicMock(), MagicMock()):
            pass
    assert counter_snapshot().get("sb_lock.renewer_construction_failed", 0) == 1


def test_lock_for_process_close_failure_bumps_counter() -> None:
    renewer = MagicMock()
    renewer.close.side_effect = RuntimeError("close failed")
    with patch(
        "vibey_bootstrap.sb_lock._new_auto_lock_renewer",
        return_value=renewer,
    ):
        with lock_for_process(MagicMock(), MagicMock()):
            pass
    assert counter_snapshot().get("sb_lock.close_failed", 0) == 1


def test_managed_lock_context_manager() -> None:
    renewer = MagicMock()
    with patch(
        "vibey_bootstrap.sb_lock._new_auto_lock_renewer",
        return_value=renewer,
    ):
        with ManagedLock(MagicMock(), MagicMock()) as lock:
            assert isinstance(lock, ManagedLock)
            renewer.register.assert_called_once()
        renewer.close.assert_called_once()


def test_managed_lock_start_idempotent() -> None:
    renewer = MagicMock()
    with patch(
        "vibey_bootstrap.sb_lock._new_auto_lock_renewer",
        return_value=renewer,
    ):
        lock = ManagedLock(MagicMock(), MagicMock())
        lock.start()
        lock.start()  # idempotent — no second registration
        assert renewer.register.call_count == 1
        lock.close()
