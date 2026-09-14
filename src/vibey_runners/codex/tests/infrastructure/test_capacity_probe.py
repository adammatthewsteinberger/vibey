# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""CompositeCapacityProbe: B then C then A; enrichment never overrides exec."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from codexloop.application.dto import ProbeResult
from codexloop.application.ports import CapacityProbe
from codexloop.domain.capacity import (
    Available,
    PlanWindows,
    QuotaExhausted,
    RateLimitWindow,
)
from tests.application.fakes import FakeCapacityProbe

NOW = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)

B_WINDOWS = PlanWindows(
    primary=RateLimitWindow(
        used_percent=90.0,
        window_minutes=300,
        resets_at=NOW + timedelta(hours=5),
    ),
    secondary=None,
    plan_type="plus",
    limit_reached=None,
)
C_WINDOWS = PlanWindows(
    primary=RateLimitWindow(used_percent=40.0, window_minutes=300, resets_at=NOW),
    secondary=None,
    plan_type="plus",
    limit_reached=None,
)
EXEC_WINDOWS = PlanWindows(
    primary=RateLimitWindow(used_percent=10.0, window_minutes=300, resets_at=None),
    secondary=None,
    plan_type="plus",
    limit_reached=None,
)
EXEC_QUOTA = ProbeResult(
    outcome=QuotaExhausted(reason="insufficient_quota"),
    snapshot=EXEC_WINDOWS,
)
EXEC_AVAILABLE = ProbeResult(outcome=Available(), snapshot=EXEC_WINDOWS)


class _ScriptedReader:
    def __init__(
        self,
        label: str,
        log: list[str],
        result: PlanWindows | None = None,
        *,
        error: BaseException | None = None,
    ) -> None:
        self._label = label
        self._log = log
        self._result = result
        self._error = error
        self.calls = 0

    async def __call__(self) -> PlanWindows | None:
        self.calls += 1
        self._log.append(self._label)
        if self._error is not None:
            raise self._error
        return self._result


class _SyncReader:
    def __init__(
        self,
        label: str,
        log: list[str],
        result: PlanWindows | None = None,
        *,
        error: BaseException | None = None,
    ) -> None:
        self._label = label
        self._log = log
        self._result = result
        self._error = error
        self.calls = 0

    def __call__(self) -> PlanWindows | None:
        self.calls += 1
        self._log.append(self._label)
        if self._error is not None:
            raise self._error
        return self._result


def _exec(result: ProbeResult, log: list[str]) -> FakeCapacityProbe:
    probe = FakeCapacityProbe(result, call_log=log)
    return probe


async def test_app_server_tried_first_rollout_skipped_exec_always_authoritative() -> None:
    from codexloop.infrastructure.capacity_probe import CompositeCapacityProbe

    log: list[str] = []
    app_server = _ScriptedReader("B", log, B_WINDOWS)
    rollout = _SyncReader("C", log, C_WINDOWS)
    exec_probe = _exec(EXEC_QUOTA, log)

    probe = CompositeCapacityProbe(exec_probe, app_server=app_server, rollout=rollout)
    result = await probe.probe()

    assert isinstance(probe, CapacityProbe)
    assert log == ["B", "probe"]
    assert exec_probe.calls == 1
    assert app_server.calls == 1
    assert rollout.calls == 0
    assert result.outcome == EXEC_QUOTA.outcome
    assert result.snapshot == B_WINDOWS


async def test_rollout_used_when_app_server_returns_none() -> None:
    from codexloop.infrastructure.capacity_probe import CompositeCapacityProbe

    log: list[str] = []
    app_server = _ScriptedReader("B", log, None)
    rollout = _SyncReader("C", log, C_WINDOWS)
    exec_probe = _exec(EXEC_AVAILABLE, log)

    probe = CompositeCapacityProbe(exec_probe, app_server=app_server, rollout=rollout)
    result = await probe.probe()

    assert log == ["B", "C", "probe"]
    assert result.outcome == EXEC_AVAILABLE.outcome
    assert result.snapshot == C_WINDOWS


async def test_exec_alone_decides_when_both_enrichment_sources_are_none() -> None:
    from codexloop.infrastructure.capacity_probe import CompositeCapacityProbe

    log: list[str] = []
    app_server = _ScriptedReader("B", log, None)
    rollout = _SyncReader("C", log, None)
    exec_probe = _exec(EXEC_QUOTA, log)

    probe = CompositeCapacityProbe(exec_probe, app_server=app_server, rollout=rollout)
    result = await probe.probe()

    assert log == ["B", "C", "probe"]
    assert exec_probe.calls == 1
    assert result.outcome == EXEC_QUOTA.outcome
    assert result.snapshot == EXEC_WINDOWS


async def test_app_server_raise_is_treated_as_none_and_never_raised() -> None:
    from codexloop.infrastructure.capacity_probe import CompositeCapacityProbe

    log: list[str] = []
    app_server = _ScriptedReader("B", log, error=RuntimeError("appserver down"))
    rollout = _SyncReader("C", log, C_WINDOWS)
    exec_probe = _exec(EXEC_AVAILABLE, log)

    probe = CompositeCapacityProbe(exec_probe, app_server=app_server, rollout=rollout)
    result = await probe.probe()

    assert log == ["B", "C", "probe"]
    assert result.outcome == EXEC_AVAILABLE.outcome
    assert result.snapshot == C_WINDOWS


async def test_disabled_enrichment_uses_exec_result_alone() -> None:
    from codexloop.infrastructure.capacity_probe import CompositeCapacityProbe

    log: list[str] = []
    exec_probe = _exec(EXEC_QUOTA, log)

    probe = CompositeCapacityProbe(exec_probe)
    result = await probe.probe()

    assert log == ["probe"]
    assert exec_probe.calls == 1
    assert result.outcome == EXEC_QUOTA.outcome
    assert result.snapshot == EXEC_WINDOWS


async def test_sync_app_server_callable_is_used() -> None:
    from codexloop.infrastructure.capacity_probe import CompositeCapacityProbe

    log: list[str] = []
    app_server = _SyncReader("B", log, B_WINDOWS)
    rollout = _SyncReader("C", log, C_WINDOWS)
    exec_probe = _exec(EXEC_AVAILABLE, log)

    probe = CompositeCapacityProbe(exec_probe, app_server=app_server, rollout=rollout)
    result = await probe.probe()

    assert log == ["B", "probe"]
    assert result.snapshot == B_WINDOWS
    assert result.outcome == EXEC_AVAILABLE.outcome


async def test_rollout_raise_is_treated_as_none() -> None:
    from codexloop.infrastructure.capacity_probe import CompositeCapacityProbe

    log: list[str] = []
    app_server = _ScriptedReader("B", log, None)
    rollout = _SyncReader("C", log, error=OSError("stale home"))
    exec_probe = _exec(EXEC_QUOTA, log)

    probe = CompositeCapacityProbe(exec_probe, app_server=app_server, rollout=rollout)
    result = await probe.probe()

    assert log == ["B", "C", "probe"]
    assert result.outcome == EXEC_QUOTA.outcome
    assert result.snapshot == EXEC_WINDOWS


def test_build_runner_wires_composite_probe(tmp_path: Path) -> None:
    from codexloop.application.ports import CapacityProbe
    from codexloop.bootstrap import RunnerConfig, build_runner
    from codexloop.infrastructure.capacity_probe import CompositeCapacityProbe

    ctx = build_runner(RunnerConfig(), cwd=tmp_path)
    assert isinstance(ctx.probe, CompositeCapacityProbe)
    assert isinstance(ctx.probe, CapacityProbe)
    assert ctx.notifier is not None
    assert ctx.reporter is not None
