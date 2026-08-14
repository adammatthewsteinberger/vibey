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


@pytest.mark.parametrize("descriptor", ALL_DESCRIPTORS, ids=lambda d: d.engine_id.value)
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


def test_codexloop_saturates_at_high() -> None:
    assert CODEXLOOP.invoke(Effort.HIGH).achieved is Effort.HIGH
    assert CODEXLOOP.invoke(Effort.MAX).achieved is Effort.HIGH
    assert CODEXLOOP.saturates_at(Effort.MAX) is True
    assert CODEXLOOP.saturates_at(Effort.HIGH) is False


def test_agyloop_saturates_at_high() -> None:
    assert AGYLOOP.invoke(Effort.MAX).achieved is Effort.HIGH
    assert AGYLOOP.saturates_at(Effort.MAX) is True


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
