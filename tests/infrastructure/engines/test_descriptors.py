# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
import pytest

from vibey.domain.effort import Effort
from vibey.domain.engine import EngineId
from vibey.infrastructure.engines.descriptors import (
    AGYLOOP,
    ALL_DESCRIPTORS,
    BY_ENGINE_ID,
    CLAUDELOOP,
    CODEXLOOP,
    CURSORLOOP,
)

ALL_EFFORTS = list(Effort)

# claudeloop/agyloop/cursorloop all have a real, verified per-effort CLI
# flag (confirmed against real --help output, see descriptors.py's own
# header comment) and so always produce non-empty argv. codexloop has no
# CLI-level effort control at all -- see test_codexloop_has_no_cli_level_
# effort_control below for its own, deliberately different invariant.
DESCRIPTORS_WITH_REAL_EFFORT_FLAGS = [
    d for d in ALL_DESCRIPTORS if d.engine_id != EngineId.CODEXLOOP
]


@pytest.mark.parametrize(
    "descriptor", DESCRIPTORS_WITH_REAL_EFFORT_FLAGS, ids=lambda d: d.engine_id.value
)
@pytest.mark.parametrize("effort", ALL_EFFORTS)
def test_invoke_covers_every_effort_level(descriptor, effort) -> None:  # type: ignore[no-untyped-def]
    invocation = descriptor.invoke(effort)
    assert invocation.argv
    assert invocation.achieved <= effort


def test_all_descriptors_have_unique_engine_ids() -> None:
    ids = [d.engine_id for d in ALL_DESCRIPTORS]
    assert len(ids) == len(set(ids))
    assert set(ids) == set(EngineId)


def test_by_engine_id_matches_all_descriptors() -> None:
    assert set(BY_ENGINE_ID) == {d.engine_id for d in ALL_DESCRIPTORS}
    for descriptor in ALL_DESCRIPTORS:
        assert BY_ENGINE_ID[descriptor.engine_id] is descriptor


def test_claudeloop_and_agyloop_achieve_full_five_level_range() -> None:
    for effort in ALL_EFFORTS:
        assert CLAUDELOOP.invoke(effort).achieved is effort
        assert AGYLOOP.invoke(effort).achieved is effort


def test_codexloop_has_no_cli_level_effort_control() -> None:
    """codexloop's `run` has no --effort flag at all (confirmed against real
    --help and cli/commands/run.py directly) and no other CLI-level way to
    set effort/reasoning depth at invocation -- per its own domain/
    model_profile.py it always starts at internal Effort.MEDIUM and can
    only change via a runtime SetEffort event, not a launch flag. Every
    level projects to empty argv and Effort.STANDARD (MEDIUM's vibey
    equivalent) -- vibey's own effort request has no effect on codexloop
    today, so requesting anything above STANDARD saturates."""
    for effort in ALL_EFFORTS:
        invocation = CODEXLOOP.invoke(effort)
        assert invocation.argv == ()
        assert invocation.achieved is Effort.STANDARD
    assert CODEXLOOP.saturates_at(Effort.TRIVIAL) is False
    assert CODEXLOOP.saturates_at(Effort.LOW) is False
    assert CODEXLOOP.saturates_at(Effort.STANDARD) is False
    assert CODEXLOOP.saturates_at(Effort.HIGH) is True
    assert CODEXLOOP.saturates_at(Effort.MAX) is True


def test_agyloop_uses_real_five_level_effort_flag() -> None:
    assert AGYLOOP.invoke(Effort.MAX).argv == ("--preset", "high", "--effort", "max")
    assert AGYLOOP.saturates_at(Effort.MAX) is False


def test_cursorloop_has_no_effort_flag_only_model_ids() -> None:
    for effort in ALL_EFFORTS:
        invocation = CURSORLOOP.invoke(effort)
        assert invocation.argv[0] == "--model"
        assert invocation.achieved is effort


@pytest.mark.parametrize("descriptor", ALL_DESCRIPTORS, ids=lambda d: d.engine_id.value)
def test_saturates_at_truth_table(descriptor) -> None:  # type: ignore[no-untyped-def]
    for effort in ALL_EFFORTS:
        achieved = descriptor.invoke(effort).achieved
        assert descriptor.saturates_at(effort) == (achieved < effort)
