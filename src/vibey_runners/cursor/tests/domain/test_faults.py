# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

import dataclasses

import pytest

from cursorloop.domain.errors import (
    BudgetExhaustedError,
    CursorloopError,
    LockHeldError,
    PlanParseError,
    StateCorruptError,
)
from cursorloop.domain.faults import Busy, ConfigFault, Fault, TransientFault


def test_fault_variants_are_frozen_dataclasses() -> None:
    fault = TransientFault(kind="network", attempt_hint=1)
    with pytest.raises(dataclasses.FrozenInstanceError):
        fault.attempt_hint = 2  # type: ignore[misc]


def test_transient_fault_fields() -> None:
    fault = TransientFault(kind="timeout", attempt_hint=3)
    assert fault.kind == "timeout"
    assert fault.attempt_hint == 3


def test_busy_fields() -> None:
    busy = Busy(agent_id="agent-1", active_run_id="run-42")
    assert busy.agent_id == "agent-1"
    assert busy.active_run_id == "run-42"

    empty_busy = Busy(agent_id="", active_run_id=None)
    assert empty_busy.active_run_id is None


def test_config_fault_fields() -> None:
    fault = ConfigFault(detail="bad config", help_url="https://example.com/help")
    assert fault.detail == "bad config"
    assert fault.help_url == "https://example.com/help"


def test_fault_union_accepts_all_variants() -> None:
    faults: list[Fault] = [
        TransientFault(kind="network", attempt_hint=0),
        Busy(agent_id="a", active_run_id=None),
        ConfigFault(detail="x", help_url=None),
    ]
    assert len(faults) == 3


def test_faults_module_docstring_states_not_capacity_states() -> None:
    import cursorloop.domain.faults as faults_module

    doc = faults_module.__doc__ or ""
    assert "not" in doc.lower()
    assert "capacity" in doc.lower()


def test_cursorloop_error_hierarchy() -> None:
    assert issubclass(PlanParseError, CursorloopError)
    assert issubclass(StateCorruptError, CursorloopError)
    assert issubclass(LockHeldError, CursorloopError)
    assert issubclass(BudgetExhaustedError, CursorloopError)


def test_cursorloop_errors_are_exceptions() -> None:
    for cls in (PlanParseError, StateCorruptError, LockHeldError, BudgetExhaustedError):
        err = cls("detail")
        assert isinstance(err, CursorloopError)
        assert str(err) == "detail"
