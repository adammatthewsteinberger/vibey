from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from vibey.application.dto import EngineHealthRecord
from vibey.domain.circuit import CircuitState
from vibey.domain.job import JobState
from vibey.domain.ledger import EventKind, LedgerEvent, Provenance
from vibey.domain.phase import Phase
from vibey.tui.dashboard import (
    DashboardState,
    VibeyDashboardApp,
    format_circuit_summary,
    format_event_row,
    format_queue_summary,
)


def test_format_helpers() -> None:
    circuits = {
        "claudeloop": "closed",
        "codexloop": "open",
    }
    summary = format_circuit_summary(circuits)
    assert "claudeloop: closed" in summary
    assert "codexloop: open" in summary

    queue = {
        JobState.READY: 2,
        JobState.LEASED: 1,
        JobState.AWAITING_HUMAN: 0,
        JobState.AWAITING_CAPACITY: 0,
        JobState.SUCCEEDED: 5,
        JobState.FAILED: 0,
    }
    q_summary = format_queue_summary(queue)
    assert "READY: 2" in q_summary
    assert "LEASED: 1" in q_summary
    assert "SUCCEEDED: 5" in q_summary

    event = LedgerEvent(
        event_id=uuid4(),
        project_id=uuid4(),
        cycle=1,
        phase=Phase.BUILD,
        seq=42,
        kind=EventKind.SAVEPOINT_CREATED,
        engine_id=None,
        job_id=None,
        causation_id=None,
        correlation_id=None,
        provenance=Provenance.AGENT,
        produced_at=datetime(2026, 8, 15, 12, 0, tzinfo=UTC),
        payload={"commit": "abc1234"},
        digest="sha256:test",
    )
    row = format_event_row(event)
    assert "#42" in row
    assert "BUILD" in row
    assert "SavePointCreated" in row


@pytest.mark.asyncio
async def test_dashboard_app_renders_state() -> None:
    project_id = uuid4()
    state = DashboardState(
        project_id=project_id,
        project_name="my-demo-app",
        repo_path=Path("/tmp/demo"),
        phase=Phase.BUILD,
        cycle=1,
        max_cycles=10,
        visual_decision="OPTED_IN",
        deployment_decision="DECLINED",
        queue_depth={
            JobState.READY: 3,
            JobState.LEASED: 1,
            JobState.AWAITING_HUMAN: 0,
            JobState.AWAITING_CAPACITY: 0,
            JobState.SUCCEEDED: 4,
            JobState.FAILED: 0,
        },
        circuits=(
            EngineHealthRecord(
                project_id=project_id,
                engine_id="claudeloop",
                installed=True,
                version="1.0.0",
                conformance_ok=True,
                conformance_at=datetime.now(UTC),
                auth_ok_at=datetime.now(UTC),
                circuit=CircuitState.CLOSED,
                capacity_state=None,
                resets_at=None,
                probe_next_at=None,
                probe_attempt=0,
                consecutive_fail=0,
                ewma_failure=0.0,
                cost_usd_cycle=1.25,
                selected_count=4,
            ),
        ),
        active_worktrees=("c1-item-001", "c1-integration"),
        ledger_tail=(
            LedgerEvent(
                event_id=uuid4(),
                project_id=project_id,
                cycle=1,
                phase=Phase.BUILD,
                seq=10,
                kind=EventKind.TURN_COMPLETED,
                engine_id=None,
                job_id=None,
                causation_id=None,
                correlation_id=None,
                provenance=Provenance.AGENT,
                produced_at=datetime(2026, 8, 15, 12, 1, tzinfo=UTC),
                payload={"tokens": 500},
                digest="sha256:tail",
            ),
        ),
    )

    app = VibeyDashboardApp(initial_state=state)
    async with app.run_test() as pilot:
        # Give textual time to mount widgets
        await pilot.pause()
        assert app.is_running
        # Check that widgets have rendered expected contents
        status_panel = app.query_one("#status-panel")
        assert "my-demo-app" in str(status_panel.render())
        assert "BUILD" in str(status_panel.render())

        queue_panel = app.query_one("#queue-panel")
        assert "READY: 3" in str(queue_panel.render())

        circuits_panel = app.query_one("#circuits-panel")
        assert "claudeloop" in str(circuits_panel.render())

        worktrees_panel = app.query_one("#worktrees-panel")
        assert "c1-item-001" in str(worktrees_panel.render())

        ledger_panel = app.query_one("#ledger-panel")
        assert "#10" in str(ledger_panel.render())


@pytest.mark.asyncio
async def test_fetch_dashboard_state_from_db(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import os

    import asyncpg

    from vibey.application.dto import EnqueueRequest
    from vibey.bootstrap import build_app, database_url
    from vibey.domain.job import idempotency_key
    from vibey.infrastructure.db.engine_health_repository import PostgresEngineHealthRepository
    from vibey.infrastructure.engines.tailer import LedgerEventDraft
    from vibey.tui.dashboard import fetch_dashboard_state

    url = os.environ.get(
        "VIBEY_TEST_DATABASE_URL",
        f"postgresql://{os.environ.get('USER', 'postgres')}@localhost:5432/vibey_test",
    )
    monkeypatch.setenv("VIBEY_PG_URL", url)

    conn = await asyncpg.connect(database_url())
    await conn.execute("DROP SCHEMA public CASCADE")
    await conn.execute("CREATE SCHEMA public")
    await conn.close()

    async with build_app() as resources:
        project = await resources.projects.create(
            "tui-test-proj",
            tmp_path,
            max_cycles=5,
            config={"project": {"name": "tui-test-proj"}},
        )
        health_repo = PostgresEngineHealthRepository(resources.ledger._pool)
        await health_repo.upsert(
            EngineHealthRecord(
                project_id=project.project_id,
                engine_id="claudeloop",
                installed=True,
                version="1.0.0",
                conformance_ok=True,
                conformance_at=datetime.now(UTC),
                auth_ok_at=datetime.now(UTC),
                circuit=CircuitState.CLOSED,
                capacity_state=None,
                resets_at=None,
                probe_next_at=None,
                probe_attempt=0,
                consecutive_fail=0,
                ewma_failure=0.0,
                cost_usd_cycle=0.50,
                selected_count=2,
            )
        )
        await resources.jobs.enqueue(
            EnqueueRequest(
                project_id=project.project_id,
                cycle=project.cycle,
                phase=Phase.INTAKE,
                kind="test.job",
                idempotency_key=idempotency_key(project.project_id, project.cycle, "test.job", "1"),
                requirement={},
            )
        )
        await resources.ledger.append(
            LedgerEventDraft(
                project_id=project.project_id,
                cycle=project.cycle,
                phase=Phase.INTAKE,
                kind=EventKind.VISUAL_DESIGN_OPTED_IN,
                engine_id=None,
                job_id=None,
                causation_id=None,
                correlation_id=project.project_id,
                provenance=Provenance.TRUSTED,
                produced_at=datetime.now(UTC),
                payload={"choice": "opt_in"},
                digest="test-digest",
            )
        )

        state = await fetch_dashboard_state(
            projects=resources.projects,
            jobs=resources.jobs,
            health=health_repo,
            ledger=resources.ledger,
            project_id=project.project_id,
        )
        assert state.project_name == "tui-test-proj"
        assert state.visual_decision == "OPTED_IN"
        assert state.queue_depth[JobState.READY] == 1
        assert len(state.circuits) == 1
        assert len(state.ledger_tail) == 1


@pytest.mark.asyncio
async def test_dashboard_refresh_action() -> None:
    project_id = uuid4()
    state1 = DashboardState(
        project_id=project_id,
        project_name="proj-1",
        repo_path=Path("/tmp/demo"),
        phase=Phase.INTAKE,
        cycle=1,
        max_cycles=10,
        visual_decision=None,
        deployment_decision=None,
        queue_depth={s: 0 for s in JobState},
        circuits=(),
        active_worktrees=(),
        ledger_tail=(),
    )
    state2 = DashboardState(
        project_id=project_id,
        project_name="proj-1",
        repo_path=Path("/tmp/demo"),
        phase=Phase.DESIGN,
        cycle=1,
        max_cycles=10,
        visual_decision="OPTED_IN",
        deployment_decision=None,
        queue_depth={s: 0 for s in JobState},
        circuits=(),
        active_worktrees=(),
        ledger_tail=(),
    )
    current = state1

    def fetcher() -> DashboardState:
        return current

    app = VibeyDashboardApp(initial_state=state1, state_fetcher=fetcher, refresh_interval=0.1)
    async with app.run_test() as pilot:
        await pilot.pause()
        status_panel = app.query_one("#status-panel")
        assert "INTAKE" in str(status_panel.render())

        current = state2
        app.action_refresh()
        await pilot.pause()
        assert "DESIGN" in str(status_panel.render())
