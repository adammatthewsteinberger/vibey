from pathlib import Path

import pytest

from vibey.application.conformance import run_conformance
from vibey.domain.capacity import CreditsExhausted
from vibey.domain.engine import EngineId
from vibey.infrastructure.engines.classify import CREDITS_FIXTURES
from vibey.infrastructure.engines.descriptors import ALL_DESCRIPTORS, CLAUDELOOP
from vibey.infrastructure.engines.scripted import ScriptedEngine


def _fixtures_for(engine_id: EngineId) -> list[tuple[str, dict[str, object], type]]:
    return [("credits", CREDITS_FIXTURES[engine_id], CreditsExhausted)]


async def test_scripted_engine_passes_full_conformance(tmp_path: Path) -> None:
    engine = ScriptedEngine(descriptor=CLAUDELOOP, base_dir=tmp_path)

    report = await run_conformance(engine, capacity_fixtures=_fixtures_for(CLAUDELOOP.engine_id))

    assert report.ok, [c for c in report.checks if not c.ok]
    assert {c.name for c in report.checks} == {
        "binary",
        "flags",
        "state_dir",
        "run_dir_shape",
        "snapshot_schema",
        "capacity_map",
        "done_marker",
        "control_plane",
        "structured_verdict",
    }


@pytest.mark.parametrize("descriptor", ALL_DESCRIPTORS, ids=lambda d: d.engine_id.value)
async def test_all_four_scripted_descriptors_pass_conformance(descriptor, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    engine = ScriptedEngine(descriptor=descriptor, base_dir=tmp_path)

    report = await run_conformance(engine, capacity_fixtures=_fixtures_for(descriptor.engine_id))

    assert report.ok, [c for c in report.checks if not c.ok]


async def test_explicit_trivial_worktree_is_used(tmp_path: Path) -> None:
    """Passing an explicit trivial_worktree covers the False branch at line 38."""
    engine = ScriptedEngine(descriptor=CLAUDELOOP, base_dir=tmp_path)
    custom_worktree = str(tmp_path / "custom-conformance")

    report = await run_conformance(
        engine,
        capacity_fixtures=_fixtures_for(CLAUDELOOP.engine_id),
        trivial_worktree=custom_worktree,
    )

    assert report.ok, [c for c in report.checks if not c.ok]


async def test_not_installed_fails_binary_check_without_crashing(tmp_path: Path) -> None:
    engine = ScriptedEngine(descriptor=CLAUDELOOP, base_dir=tmp_path, installed=False)

    report = await run_conformance(engine)

    assert report.ok is False
    binary_check = next(c for c in report.checks if c.name == "binary")
    assert binary_check.ok is False


async def test_a_deliberately_broken_descriptor_is_detected_not_crashed_on(
    tmp_path: Path,
) -> None:
    """The M3 exit condition, verbatim: a deliberately-broken descriptor is
    detected, not crashed on."""
    engine = ScriptedEngine(
        descriptor=CLAUDELOOP,
        base_dir=tmp_path,
        help_text="--preset low",  # missing most of the claimed flags
    )

    report = await run_conformance(engine)

    assert report.ok is False
    flags_check = next(c for c in report.checks if c.name == "flags")
    assert flags_check.ok is False
    assert "--effort" in flags_check.detail


async def test_wrong_capacity_mapping_is_caught_by_capacity_map_check(tmp_path: Path) -> None:
    engine = ScriptedEngine(descriptor=CLAUDELOOP, base_dir=tmp_path)
    # Deliberately assert the wrong expected type for a real credits fixture.
    from vibey.domain.capacity import WindowExhausted

    bad_fixtures = [("credits", CREDITS_FIXTURES[EngineId.CLAUDELOOP], WindowExhausted)]

    report = await run_conformance(engine, capacity_fixtures=bad_fixtures)

    capacity_check = next(c for c in report.checks if c.name == "capacity_map")
    assert capacity_check.ok is False


async def test_missing_done_marker_fails_that_check_only(tmp_path: Path) -> None:
    engine = ScriptedEngine(
        descriptor=CLAUDELOOP,
        base_dir=tmp_path,
        script=[
            {"kind": "SessionSeeded", "at": "2026-01-01T00:00:00+00:00", "payload": {}},
        ],
    )

    report = await run_conformance(engine)

    done_marker_check = next(c for c in report.checks if c.name == "done_marker")
    assert done_marker_check.ok is False
    # Everything upstream of the missing marker still ran and can still pass.
    run_dir_shape_check = next(c for c in report.checks if c.name == "run_dir_shape")
    assert run_dir_shape_check.ok is True


async def test_adapter_without_help_text_fails_the_flags_check(tmp_path: Path) -> None:
    class _NoHelpTextAdapter(ScriptedEngine):
        pass

    engine = _NoHelpTextAdapter(descriptor=CLAUDELOOP, base_dir=tmp_path)
    del engine.help_text  # slotted dataclass: remove the attribute entirely

    report = await run_conformance(engine)

    flags_check = next(c for c in report.checks if c.name == "flags")
    assert flags_check.ok is False
    assert "no help text" in flags_check.detail


async def test_version_below_minimum_fails_the_binary_check(tmp_path: Path) -> None:
    from vibey.application.dto import PreflightResult

    class _OldVersionAdapter(ScriptedEngine):
        async def preflight(self) -> PreflightResult:
            return PreflightResult(installed=True, version="0.0.1", auth_ok=True)

    engine = _OldVersionAdapter(descriptor=CLAUDELOOP, base_dir=tmp_path)

    report = await run_conformance(engine)

    binary_check = next(c for c in report.checks if c.name == "binary")
    assert binary_check.ok is False
    assert "< min" in binary_check.detail


async def test_adapter_start_raising_fails_downstream_checks_without_crashing(
    tmp_path: Path,
) -> None:
    class _BrokenStartAdapter(ScriptedEngine):
        async def start(self, spec):  # type: ignore[no-untyped-def, override]
            raise RuntimeError("disk full")

    engine = _BrokenStartAdapter(descriptor=CLAUDELOOP, base_dir=tmp_path)

    report = await run_conformance(engine)

    assert report.ok is False
    for name in ("state_dir", "run_dir_shape", "snapshot_schema", "done_marker"):
        check = next(c for c in report.checks if c.name == name)
        assert check.ok is False
        assert "disk full" in check.detail


async def test_missing_snapshot_fails_snapshot_schema_check(tmp_path: Path) -> None:
    class _NoSnapshotAdapter(ScriptedEngine):
        async def snapshot(self, handle):  # type: ignore[no-untyped-def, override]
            return None

    engine = _NoSnapshotAdapter(descriptor=CLAUDELOOP, base_dir=tmp_path)

    report = await run_conformance(engine)

    check = next(c for c in report.checks if c.name == "snapshot_schema")
    assert check.ok is False
    assert check.detail == "no snapshot"


async def test_structured_verdict_claimed_but_missing_fails_that_check(tmp_path: Path) -> None:
    engine = ScriptedEngine(
        descriptor=CLAUDELOOP,
        base_dir=tmp_path,
        script=[
            {
                "kind": "SessionSeeded",
                "at": "2026-01-01T00:00:00+00:00",
                "payload": {"seed_digest": "x"},
            }
        ],
    )

    report = await run_conformance(engine)

    check = next(c for c in report.checks if c.name == "structured_verdict")
    assert check.ok is False
    assert "no VerdictRendered" in check.detail


async def test_agyloop_structured_verdict_not_claimed_is_ok(tmp_path: Path) -> None:
    from vibey.infrastructure.engines.descriptors import CURSORLOOP

    # cursorloop's descriptor omits STRUCTURED_VERDICT (§1: "partial").
    engine = ScriptedEngine(descriptor=CURSORLOOP, base_dir=tmp_path)

    report = await run_conformance(engine)

    check = next(c for c in report.checks if c.name == "structured_verdict")
    assert check.ok is True
    assert check.detail == "not claimed"


async def test_a_missing_snapshot_fails_the_run_dir_shape_check(tmp_path: Path) -> None:
    """snapshots/latest.json is what a supervisor reads to learn where a run
    got to, so a run directory without one is not conformant even if every
    other file is present."""

    class _NoSnapshot(ScriptedEngine):
        async def start(self, spec: object) -> object:
            handle = await super().start(spec)  # type: ignore[arg-type]
            (handle.run_dir / "snapshots" / "latest.json").unlink(missing_ok=True)
            return handle

    engine = _NoSnapshot(
        descriptor=CLAUDELOOP,
        base_dir=tmp_path,
        script=[{"kind": "SessionSeeded", "at": "2026-01-01T00:00:00+00:00", "payload": {}}],
    )

    report = await run_conformance(engine)

    shape = next(c for c in report.checks if c.name == "run_dir_shape")
    assert shape.ok is False
    assert "snapshots/latest.json" in shape.detail


async def test_an_adapter_that_raises_fails_the_control_plane_check_rather_than_the_suite(
    tmp_path: Path,
) -> None:
    """A conformance suite exists to report on adapters, so an adapter that
    throws has to become a failed check, not an exception out of the runner."""

    class _RaisingInbox(ScriptedEngine):
        async def send_prompt(self, handle: object, text: str, *, now: bool) -> None:
            raise RuntimeError("inbox is not writable")

    engine = _RaisingInbox(
        descriptor=CLAUDELOOP,
        base_dir=tmp_path,
        script=[{"kind": "SessionSeeded", "at": "2026-01-01T00:00:00+00:00", "payload": {}}],
    )

    report = await run_conformance(engine)

    control = next(c for c in report.checks if c.name == "control_plane")
    assert control.ok is False
    assert "not writable" in control.detail
