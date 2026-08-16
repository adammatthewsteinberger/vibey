import asyncio
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import asyncpg
import pytest
from typer.testing import CliRunner

from vibey.application.dto import EngineHealthRecord, EnqueueRequest
from vibey.bootstrap import build_app, database_url
from vibey.cli.main import app
from vibey.domain.circuit import CircuitState
from vibey.domain.job import idempotency_key
from vibey.domain.ledger import EventKind, Provenance
from vibey.domain.phase import Phase
from vibey.infrastructure.db.engine_health_repository import PostgresEngineHealthRepository
from vibey.infrastructure.engines.tailer import LedgerEventDraft

pytestmark = pytest.mark.integration
# Typer force-enables rich ANSI styling whenever GITHUB_ACTIONS is set
# (typer/rich_utils.py), which CI always has and a local shell never does.
# That embeds escape codes inside option names, breaking plain substring
# checks against --help output -- disable it the way Typer itself exposes.
runner = CliRunner(env={"_TYPER_FORCE_DISABLE_TERMINAL": "1"})


@pytest.fixture(autouse=True)
async def _use_test_database(monkeypatch: pytest.MonkeyPatch) -> None:
    url = os.environ.get(
        "VIBEY_TEST_DATABASE_URL",
        f"postgresql://{os.environ.get('USER', 'postgres')}@localhost:5432/vibey_test",
    )
    monkeypatch.setenv("VIBEY_PG_URL", url)

    conn = await asyncpg.connect(database_url())
    await conn.execute("DROP SCHEMA IF EXISTS public CASCADE")
    await conn.execute("CREATE SCHEMA IF NOT EXISTS public")

    await conn.close()


async def _seed_status_project(tmp_path: Path) -> UUID:
    async with build_app() as resources:
        project = await resources.projects.create(
            "ops-status-proj",
            tmp_path,
            max_cycles=5,
            config={"project": {"name": "ops-status-proj"}},
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
                cost_usd_cycle=1.50,
                selected_count=3,
            )
        )
        await resources.jobs.enqueue(
            EnqueueRequest(
                project_id=project.project_id,
                cycle=project.cycle,
                phase=Phase.INTAKE,
                kind="design.interview",
                idempotency_key=idempotency_key(
                    project.project_id, project.cycle, "design.interview", "1"
                ),
                requirement={},
            )
        )
        return project.project_id


def test_status_command_text_and_json(tmp_path: Path) -> None:
    project_id = asyncio.run(_seed_status_project(tmp_path))

    # Test text output
    res_text = runner.invoke(app, ["status", str(project_id)])
    assert res_text.exit_code == 0, res_text.output
    assert "ops-status-proj" in res_text.stdout
    assert "INTAKE" in res_text.stdout
    assert "claudeloop" in res_text.stdout

    # Test JSON output
    res_json = runner.invoke(app, ["status", "--json", str(project_id)])
    assert res_json.exit_code == 0, res_json.output
    payload = json.loads(res_json.stdout)
    assert payload["name"] == "ops-status-proj"
    assert payload["phase"] == "intake"
    assert payload["cycle"] == 1
    assert payload["queue_depth"]["ready"] == 1
    assert len(payload["circuits"]) == 1
    assert payload["circuits"][0]["engine_id"] == "claudeloop"


async def _seed_engines_project(tmp_path: Path) -> UUID:
    async with build_app() as resources:
        project = await resources.projects.create(
            "ops-engines-proj",
            tmp_path,
            max_cycles=5,
            config={"project": {"name": "ops-engines-proj"}},
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
                cost_usd_cycle=2.00,
                selected_count=5,
            )
        )
        return project.project_id


def test_engines_command(tmp_path: Path) -> None:
    project_id = asyncio.run(_seed_engines_project(tmp_path))
    res = runner.invoke(app, ["engines", str(project_id)])
    assert res.exit_code == 0, res.output
    assert "claudeloop" in res.stdout
    assert "closed" in res.stdout
    assert "$2.00" in res.stdout


async def _seed_cost_project(tmp_path: Path) -> UUID:
    async with build_app() as resources:
        project = await resources.projects.create(
            "ops-cost-proj",
            tmp_path,
            max_cycles=5,
            config={
                "project": {"name": "ops-cost-proj"},
                "budget": {"max_dollars_per_cycle": 40.0, "max_dollars_total": 250.0},
            },
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
                cost_usd_cycle=3.75,
                selected_count=4,
            )
        )
        return project.project_id


def test_cost_command(tmp_path: Path) -> None:
    project_id = asyncio.run(_seed_cost_project(tmp_path))
    res = runner.invoke(app, ["cost", str(project_id)])
    assert res.exit_code == 0, res.output
    assert "claudeloop" in res.stdout
    assert "$3.75" in res.stdout
    assert "Cycle Budget" in res.stdout


async def _seed_ledger_project(tmp_path: Path) -> UUID:
    async with build_app() as resources:
        project = await resources.projects.create(
            "ops-ledger-proj",
            tmp_path,
            max_cycles=5,
            config={"project": {"name": "ops-ledger-proj"}},
        )
        await resources.ledger.append(
            LedgerEventDraft(
                project_id=project.project_id,
                cycle=project.cycle,
                phase=Phase.INTAKE,
                kind=EventKind.QUESTION_ASKED,
                engine_id=None,
                job_id=None,
                causation_id=None,
                correlation_id=project.project_id,
                provenance=Provenance.TRUSTED,
                produced_at=datetime.now(UTC),
                payload={"question_id": "q1", "text": "What is the goal?"},
                digest="test-digest-1",
            )
        )
        await resources.ledger.append(
            LedgerEventDraft(
                project_id=project.project_id,
                cycle=project.cycle,
                phase=Phase.INTAKE,
                kind=EventKind.ANSWER_GIVEN,
                engine_id=None,
                job_id=None,
                causation_id=None,
                correlation_id=project.project_id,
                provenance=Provenance.TRUSTED,
                produced_at=datetime.now(UTC),
                payload={"question_id": "q1", "answer": "Build a notes app"},
                digest="test-digest-2",
            )
        )
        return project.project_id


def test_ledger_show_command(tmp_path: Path) -> None:
    project_id = asyncio.run(_seed_ledger_project(tmp_path))
    res = runner.invoke(app, ["ledger", "show", str(project_id)])
    assert res.exit_code == 0, res.output
    assert "QuestionAsked" in res.stdout
    assert "AnswerGiven" in res.stdout
    assert "#1" in res.stdout
    assert "#2" in res.stdout


def test_watch_command_with_no_projects() -> None:
    """Watch command exits gracefully when no projects exist."""
    from unittest.mock import AsyncMock, patch

    # Mock the TUI app so it doesn't actually start
    with patch("vibey.cli.main.VibeyDashboardApp") as mock_app:
        mock_app.return_value.run_async = AsyncMock()
        res = runner.invoke(app, ["watch"])
        assert res.exit_code == 1, res.output
        assert "no projects found" in res.output


def test_watch_command_with_unknown_project_id() -> None:
    """Watch command exits gracefully for unknown project ID."""
    from uuid import uuid4
    from unittest.mock import AsyncMock, patch

    unknown_id = uuid4()
    with patch("vibey.cli.main.VibeyDashboardApp") as mock_app:
        mock_app.return_value.run_async = AsyncMock()
        res = runner.invoke(app, ["watch", str(unknown_id)])
        assert res.exit_code == 1, res.output
        assert "unknown project" in res.output
