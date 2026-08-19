"""Tests for application/engine_health_service.py — the business logic
wrapper around EngineHealthRepository."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from vibey.application.dto import EngineHealthRecord, PreflightResult
from vibey.application.engine_health_service import EngineHealthService
from vibey.domain.capacity import (
    AuthenticationFailed,
    CreditsExhausted,
    WindowExhausted,
)
from vibey.domain.engine import EngineId


class FakeEngineHealthRepository:
    def __init__(self) -> None:
        self._records: dict[tuple[object, str], EngineHealthRecord] = {}

    async def get(self, project_id: object, engine_id: str) -> EngineHealthRecord | None:
        return self._records.get((project_id, engine_id))

    async def upsert(self, record: EngineHealthRecord) -> EngineHealthRecord:
        self._records[(record.project_id, record.engine_id.value)] = record
        return record

    async def list_for_project(self, project_id: object) -> tuple[EngineHealthRecord, ...]:
        return tuple(r for (pid, _), r in self._records.items() if pid == project_id)


def _make_record(
    project_id: object | None = None,
    engine_id: EngineId = EngineId.CLAUDELOOP,
    **overrides: object,
) -> EngineHealthRecord:
    defaults: dict[str, object] = {
        "project_id": project_id or uuid4(),
        "engine_id": engine_id,
        "installed": True,
        "version": "1.0.0",
        "conformance_ok": True,
        "conformance_at": datetime.now(UTC),
        "auth_ok_at": datetime.now(UTC),
        "circuit": "closed",
        "capacity_state": None,
        "resets_at": None,
        "probe_next_at": None,
        "probe_attempt": 0,
        "consecutive_fail": 0,
        "ewma_failure": 0.0,
        "cost_usd_cycle": 0.0,
        "selected_count": 0,
    }
    defaults.update(overrides)
    return EngineHealthRecord(**defaults)  # type: ignore[arg-type]


# --- get_or_create ---


async def test_get_or_create_returns_existing_record() -> None:
    repo = FakeEngineHealthRepository()
    project_id = uuid4()
    existing = _make_record(project_id=project_id, version="2.0.0")
    await repo.upsert(existing)

    svc = EngineHealthService(repo)
    result = await svc.get_or_create(project_id, EngineId.CLAUDELOOP)

    assert result.version == "2.0.0"


async def test_get_or_create_returns_defaults_when_missing() -> None:
    repo = FakeEngineHealthRepository()
    svc = EngineHealthService(repo)

    result = await svc.get_or_create(uuid4(), EngineId.CLAUDELOOP)

    assert result.installed is False
    assert result.circuit == "closed"
    assert result.ewma_failure == 0.0


# --- update_from_preflight ---


async def test_update_from_preflight_sets_installed_and_version() -> None:
    repo = FakeEngineHealthRepository()
    svc = EngineHealthService(repo)
    project_id = uuid4()

    result = await svc.update_from_preflight(
        project_id,
        EngineId.CLAUDELOOP,
        PreflightResult(installed=True, version="3.5.0", auth_ok=True),
        conformance_ok=True,
    )

    assert result.installed is True
    assert result.version == "3.5.0"
    assert result.conformance_ok is True
    assert result.auth_ok_at is not None


async def test_update_from_preflight_auth_not_ok_clears_auth_ok_at() -> None:
    repo = FakeEngineHealthRepository()
    svc = EngineHealthService(repo)
    project_id = uuid4()

    result = await svc.update_from_preflight(
        project_id,
        EngineId.CLAUDELOOP,
        PreflightResult(installed=True, version="1.0.0", auth_ok=False),
        conformance_ok=False,
    )

    assert result.auth_ok_at is None


async def test_update_from_preflight_conformance_fail_preserves_old_conformance_at() -> None:
    repo = FakeEngineHealthRepository()
    project_id = uuid4()
    old_time = datetime(2026, 1, 1, tzinfo=UTC)
    existing = _make_record(project_id=project_id, conformance_at=old_time)
    await repo.upsert(existing)

    svc = EngineHealthService(repo)
    result = await svc.update_from_preflight(
        project_id,
        EngineId.CLAUDELOOP,
        PreflightResult(installed=True, version="1.0.0", auth_ok=True),
        conformance_ok=False,
    )

    assert result.conformance_ok is False
    assert result.conformance_at == old_time


# --- record_capacity_rejection ---


async def test_record_capacity_rejection_credits_exhausted() -> None:
    repo = FakeEngineHealthRepository()
    svc = EngineHealthService(repo)
    project_id = uuid4()

    result = await svc.record_capacity_rejection(
        project_id, EngineId.CLAUDELOOP, CreditsExhausted()
    )

    assert result.circuit == "open"
    assert result.capacity_state == "CreditsExhausted"
    assert result.resets_at is None
    assert result.probe_next_at is not None
    assert result.consecutive_fail == 1
    assert result.ewma_failure > 0.0


async def test_record_capacity_rejection_window_exhausted() -> None:
    repo = FakeEngineHealthRepository()
    svc = EngineHealthService(repo)
    project_id = uuid4()
    resets = datetime.now(UTC) + timedelta(hours=1)

    result = await svc.record_capacity_rejection(
        project_id, EngineId.CLAUDELOOP, WindowExhausted(resets_at=resets)
    )

    assert result.circuit == "open"
    assert result.capacity_state == "WindowExhausted"
    assert result.resets_at == resets
    assert result.probe_next_at == resets


async def test_record_capacity_rejection_authentication_failed() -> None:
    repo = FakeEngineHealthRepository()
    svc = EngineHealthService(repo)
    project_id = uuid4()

    result = await svc.record_capacity_rejection(
        project_id, EngineId.CLAUDELOOP, AuthenticationFailed(detail="bad token")
    )

    assert result.circuit == "open"
    assert result.capacity_state == "AuthenticationFailed"
    assert result.probe_next_at is None


async def test_capacity_rejection_with_available_is_noop() -> None:
    from vibey.domain.capacity import Available

    repo = FakeEngineHealthRepository()
    svc = EngineHealthService(repo)
    project_id = uuid4()

    result = await svc.record_capacity_rejection(project_id, EngineId.CLAUDELOOP, Available())

    assert result.circuit == "closed"
    assert result.capacity_state is None


async def test_capacity_rejection_exponential_backoff_for_credits() -> None:
    repo = FakeEngineHealthRepository()
    svc = EngineHealthService(repo)
    project_id = uuid4()

    r1 = await svc.record_capacity_rejection(project_id, EngineId.CLAUDELOOP, CreditsExhausted())
    r2 = await svc.record_capacity_rejection(project_id, EngineId.CLAUDELOOP, CreditsExhausted())

    assert r2.probe_attempt == 2
    assert r2.consecutive_fail == 2
    assert r2.probe_next_at is not None
    assert r1.probe_next_at is not None
    # Second probe should be further out (exponential backoff)


async def test_ewma_failure_increases_on_rejection() -> None:
    repo = FakeEngineHealthRepository()
    svc = EngineHealthService(repo)
    project_id = uuid4()

    r1 = await svc.record_capacity_rejection(project_id, EngineId.CLAUDELOOP, CreditsExhausted())
    r2 = await svc.record_capacity_rejection(project_id, EngineId.CLAUDELOOP, CreditsExhausted())

    assert r2.ewma_failure > r1.ewma_failure


# --- record_selection ---


async def test_record_selection_increments_count_and_cost() -> None:
    repo = FakeEngineHealthRepository()
    svc = EngineHealthService(repo)
    project_id = uuid4()

    r1 = await svc.record_selection(project_id, EngineId.CLAUDELOOP, cost_usd=0.50)
    assert r1.selected_count == 1
    assert r1.cost_usd_cycle == pytest.approx(0.50)

    r2 = await svc.record_selection(project_id, EngineId.CLAUDELOOP, cost_usd=0.25)
    assert r2.selected_count == 2
    assert r2.cost_usd_cycle == pytest.approx(0.75)


# --- record_success ---


async def test_record_success_resets_circuit_and_failures() -> None:
    repo = FakeEngineHealthRepository()
    svc = EngineHealthService(repo)
    project_id = uuid4()

    # Set up a failing state first
    await svc.record_capacity_rejection(project_id, EngineId.CLAUDELOOP, CreditsExhausted())

    result = await svc.record_success(project_id, EngineId.CLAUDELOOP)

    assert result.circuit == "closed"
    assert result.capacity_state is None
    assert result.consecutive_fail == 0
    assert result.probe_attempt == 0
    assert result.ewma_failure < 0.1  # decayed


async def test_record_success_decays_ewma() -> None:
    repo = FakeEngineHealthRepository()
    project_id = uuid4()
    existing = _make_record(project_id=project_id, ewma_failure=0.5)
    await repo.upsert(existing)

    svc = EngineHealthService(repo)
    result = await svc.record_success(project_id, EngineId.CLAUDELOOP)

    assert result.ewma_failure == pytest.approx(0.45)


# --- list_for_project ---


async def test_list_for_project_returns_all_records() -> None:
    repo = FakeEngineHealthRepository()
    project_id = uuid4()

    await repo.upsert(_make_record(project_id=project_id, engine_id=EngineId.CLAUDELOOP))
    await repo.upsert(_make_record(project_id=project_id, engine_id=EngineId.CODEXLOOP))

    svc = EngineHealthService(repo)
    records = await svc.list_for_project(project_id)

    assert len(records) == 2


async def test_record_preflight_refreshes_auth_but_preserves_conformance() -> None:
    """The worker's startup sweep must never grant or revoke conformance --
    that verdict belongs to `vibey doctor --conformance --record` alone."""
    from vibey.application.dto import PreflightResult

    repo = FakeEngineHealthRepository()
    service = EngineHealthService(repo)
    project_id = uuid4()
    granted = await service.update_from_preflight(
        project_id,
        EngineId.CLAUDELOOP,
        PreflightResult(installed=True, version="1.0.0", auth_ok=True),
        conformance_ok=True,
    )
    assert granted.conformance_ok is True

    refreshed = await service.record_preflight(
        project_id,
        EngineId.CLAUDELOOP,
        PreflightResult(installed=True, version="1.1.0", auth_ok=True),
    )

    assert refreshed.version == "1.1.0"
    assert refreshed.conformance_ok is True
    assert refreshed.conformance_at == granted.conformance_at
    assert refreshed.auth_ok_at is not None


async def test_record_preflight_keeps_prior_auth_timestamp_on_auth_failure() -> None:
    from vibey.application.dto import PreflightResult

    repo = FakeEngineHealthRepository()
    service = EngineHealthService(repo)
    project_id = uuid4()
    first = await service.record_preflight(
        project_id,
        EngineId.AGYLOOP,
        PreflightResult(installed=True, version="1.0.0", auth_ok=True),
    )
    assert first.auth_ok_at is not None

    second = await service.record_preflight(
        project_id,
        EngineId.AGYLOOP,
        PreflightResult(installed=True, version="1.0.0", auth_ok=False),
    )

    assert second.auth_ok_at == first.auth_ok_at
    assert second.conformance_ok is False
