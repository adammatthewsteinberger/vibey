# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Faked-mode conformance: all four engines pass the 9-check suite using
ScriptedEngine (no subprocess, no network, no API key).

This duplicates the application-level conformance tests but from the
tests/live/ location with the @live marker so `pytest -m live` picks
them up as the faked half of the two-mode harness.
"""

from pathlib import Path

import pytest

from vibey.application.conformance import run_conformance
from vibey.domain.capacity import CreditsExhausted
from vibey.domain.engine import EngineId
from vibey.infrastructure.engines.classify import CREDITS_FIXTURES
from vibey.infrastructure.engines.descriptors import ALL_DESCRIPTORS
from vibey.infrastructure.engines.scripted import ScriptedEngine


def _fixtures_for(engine_id: EngineId) -> list[tuple[str, dict[str, object], type]]:
    return [("credits", CREDITS_FIXTURES[engine_id], CreditsExhausted)]


@pytest.mark.live
@pytest.mark.parametrize("descriptor", ALL_DESCRIPTORS, ids=lambda d: d.engine_id.value)
async def test_scripted_conformance_all_engines(
    descriptor,  # type: ignore[no-untyped-def]
    tmp_path: Path,
) -> None:
    engine = ScriptedEngine(descriptor=descriptor, base_dir=tmp_path)
    report = await run_conformance(
        engine,
        capacity_fixtures=_fixtures_for(descriptor.engine_id),
    )
    assert report.ok, [c for c in report.checks if not c.ok]


@pytest.mark.live
@pytest.mark.parametrize("descriptor", ALL_DESCRIPTORS, ids=lambda d: d.engine_id.value)
async def test_scripted_run_dir_shape_is_valid(
    descriptor,  # type: ignore[no-untyped-def]
    tmp_path: Path,
) -> None:
    """Each engine's ScriptedEngine writes the canonical run directory
    layout: meta.json, events.jsonl, snapshots/latest.json, inbox/."""
    engine = ScriptedEngine(descriptor=descriptor, base_dir=tmp_path)
    report = await run_conformance(engine)
    shape_check = next(c for c in report.checks if c.name == "run_dir_shape")
    assert shape_check.ok, shape_check.detail
