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
    with patch("vibey.tui.dashboard.VibeyDashboardApp") as mock_app:
        mock_app.return_value.run_async = AsyncMock()
        res = runner.invoke(app, ["watch"])
        assert res.exit_code == 1, res.output
        assert "no projects found" in res.output


def test_watch_command_with_unknown_project_id() -> None:
    """Watch command exits gracefully for unknown project ID."""
    from unittest.mock import AsyncMock, patch
    from uuid import uuid4

    unknown_id = uuid4()
    with patch("vibey.tui.dashboard.VibeyDashboardApp") as mock_app:
        mock_app.return_value.run_async = AsyncMock()
        res = runner.invoke(app, ["watch", str(unknown_id)])
        assert res.exit_code == 1, res.output
        assert "unknown project" in res.output


# ── "use latest" paths ──────────────────────────────────────────────────────


def test_status_uses_latest_project_when_no_id_given(tmp_path: Path) -> None:
    asyncio.run(_seed_status_project(tmp_path))
    res = runner.invoke(app, ["status"])
    assert res.exit_code == 0, res.output
    assert "ops-status-proj" in res.stdout


def test_status_no_projects_exits_with_error() -> None:
    res = runner.invoke(app, ["status"])
    assert res.exit_code == 1
    assert "no projects found" in res.output


def test_engines_uses_latest_project_when_no_id_given(tmp_path: Path) -> None:
    asyncio.run(_seed_engines_project(tmp_path))
    res = runner.invoke(app, ["engines"])
    assert res.exit_code == 0, res.output
    assert "claudeloop" in res.stdout


def test_engines_no_projects_exits_with_error() -> None:
    res = runner.invoke(app, ["engines"])
    assert res.exit_code == 1
    assert "no projects found" in res.output


def test_engines_with_no_engines_recorded(tmp_path: Path) -> None:
    async def seed() -> UUID:
        async with build_app() as resources:
            p = await resources.projects.create("empty-eng", tmp_path, max_cycles=1, config={})
            return p.project_id

    pid = asyncio.run(seed())
    res = runner.invoke(app, ["engines", str(pid)])
    assert res.exit_code == 0, res.output
    assert "no engines recorded" in res.output


def test_cost_uses_latest_project_when_no_id_given(tmp_path: Path) -> None:
    asyncio.run(_seed_cost_project(tmp_path))
    res = runner.invoke(app, ["cost"])
    assert res.exit_code == 0, res.output
    assert "Cycle Budget" in res.stdout


def test_cost_no_projects_exits_with_error() -> None:
    res = runner.invoke(app, ["cost"])
    assert res.exit_code == 1
    assert "no projects found" in res.output


def test_cost_unknown_project_exits_with_error() -> None:
    from uuid import uuid4

    res = runner.invoke(app, ["cost", str(uuid4())])
    assert res.exit_code == 1
    assert "unknown project" in res.output


def test_ledger_no_subcommand_shows_help() -> None:
    res = runner.invoke(app, ["ledger"])
    assert res.exit_code == 0
    assert "show" in res.output.lower()


def test_ledger_show_uses_latest_project_when_no_id_given(tmp_path: Path) -> None:
    asyncio.run(_seed_ledger_project(tmp_path))
    res = runner.invoke(app, ["ledger", "show"])
    assert res.exit_code == 0, res.output
    assert "QuestionAsked" in res.stdout


def test_ledger_show_no_projects_exits_with_error() -> None:
    res = runner.invoke(app, ["ledger", "show"])
    assert res.exit_code == 1
    assert "no projects found" in res.output


def test_ledger_show_with_phase_filter(tmp_path: Path) -> None:
    pid = asyncio.run(_seed_ledger_project(tmp_path))
    res = runner.invoke(app, ["ledger", "show", str(pid), "--phase", "intake"])
    assert res.exit_code == 0, res.output
    assert "INTAKE" in res.stdout


def test_ledger_show_with_kind_filter(tmp_path: Path) -> None:
    pid = asyncio.run(_seed_ledger_project(tmp_path))
    res = runner.invoke(app, ["ledger", "show", str(pid), "--kind", "QuestionAsked"])
    assert res.exit_code == 0, res.output
    assert "QuestionAsked" in res.stdout


def test_status_with_no_engines_shows_no_engines_message(tmp_path: Path) -> None:
    async def seed() -> UUID:
        async with build_app() as resources:
            p = await resources.projects.create("no-eng-proj", tmp_path, max_cycles=1, config={})
            return p.project_id

    pid = asyncio.run(seed())
    res = runner.invoke(app, ["status", str(pid)])
    assert res.exit_code == 0, res.output
    assert "no engines recorded" in res.output


# ── deploy commands without project_id and with unknown project ─────────────


def test_deploy_status_uses_latest_project(tmp_path: Path) -> None:
    from tests.cli.test_deploy_cli import _seed_deploy_project

    asyncio.run(_seed_deploy_project(tmp_path))
    res = runner.invoke(app, ["deploy", "status"])
    assert res.exit_code == 0, res.output
    assert "deploy-cli-proj" in res.stdout


def test_deploy_status_no_projects_exits_with_error() -> None:
    res = runner.invoke(app, ["deploy", "status"])
    assert res.exit_code == 1
    assert "no projects found" in res.output


def test_deploy_status_unknown_project() -> None:
    from uuid import uuid4

    res = runner.invoke(app, ["deploy", "status", str(uuid4())])
    assert res.exit_code == 1
    assert "unknown project" in res.output


def test_deploy_inspect_uses_latest_project(tmp_path: Path) -> None:
    from tests.cli.test_deploy_cli import _seed_deploy_project

    asyncio.run(_seed_deploy_project(tmp_path))
    res = runner.invoke(app, ["deploy", "inspect"])
    assert res.exit_code == 0, res.output
    assert "spec_id" in res.output


def test_deploy_inspect_no_projects_exits_with_error() -> None:
    res = runner.invoke(app, ["deploy", "inspect"])
    assert res.exit_code == 1
    assert "no projects found" in res.output


def test_deploy_inspect_unknown_project() -> None:
    from uuid import uuid4

    res = runner.invoke(app, ["deploy", "inspect", str(uuid4())])
    assert res.exit_code == 1
    assert "unknown project" in res.output


def test_deploy_plan_uses_latest_project(tmp_path: Path) -> None:
    from tests.cli.test_deploy_cli import _seed_deploy_project

    asyncio.run(_seed_deploy_project(tmp_path))
    res = runner.invoke(app, ["deploy", "plan"])
    assert res.exit_code == 0, res.output
    assert "Plan Evaluation" in res.output


def test_deploy_plan_no_projects_exits_with_error() -> None:
    res = runner.invoke(app, ["deploy", "plan"])
    assert res.exit_code == 1
    assert "no projects found" in res.output


def test_deploy_plan_unknown_project() -> None:
    from uuid import uuid4

    res = runner.invoke(app, ["deploy", "plan", str(uuid4())])
    assert res.exit_code == 1
    assert "unknown project" in res.output


def test_deploy_cancel_uses_latest_project(tmp_path: Path) -> None:
    from tests.cli.test_deploy_cli import _seed_deploy_project

    asyncio.run(_seed_deploy_project(tmp_path))
    res = runner.invoke(app, ["deploy", "cancel"])
    assert res.exit_code == 0, res.output
    assert "cancelled" in res.output.lower()


def test_deploy_cancel_no_projects_exits_with_error() -> None:
    res = runner.invoke(app, ["deploy", "cancel"])
    assert res.exit_code == 1
    assert "no projects found" in res.output


def test_deploy_cancel_unknown_project() -> None:
    from uuid import uuid4

    res = runner.invoke(app, ["deploy", "cancel", str(uuid4())])
    assert res.exit_code == 1
    assert "unknown project" in res.output


def test_deploy_rollback_uses_latest_project(tmp_path: Path) -> None:
    from tests.cli.test_deploy_cli import _seed_deploy_project

    asyncio.run(_seed_deploy_project(tmp_path))
    res = runner.invoke(app, ["deploy", "rollback"])
    assert res.exit_code == 0, res.output
    assert "rollback" in res.output.lower()


def test_deploy_rollback_no_projects_exits_with_error() -> None:
    res = runner.invoke(app, ["deploy", "rollback"])
    assert res.exit_code == 1
    assert "no projects found" in res.output


def test_deploy_rollback_unknown_project() -> None:
    from uuid import uuid4

    res = runner.invoke(app, ["deploy", "rollback", str(uuid4())])
    assert res.exit_code == 1
    assert "unknown project" in res.output


# ── _work_once and _enqueue_design error paths ──────────────────────────────


def test_work_once_unknown_project() -> None:
    from uuid import uuid4

    res = runner.invoke(app, ["work", str(uuid4())])
    assert res.exit_code != 0


def test_work_once_unknown_provider(tmp_path: Path) -> None:
    async def seed() -> UUID:
        async with build_app() as resources:
            p = await resources.projects.create("prov-test", tmp_path, max_cycles=1, config={})
            return p.project_id

    pid = asyncio.run(seed())
    res = runner.invoke(app, ["work", str(pid), "--provider", "nonexistent"])
    assert res.exit_code != 0


def test_work_once_visual_phase_rejects_non_scripted_provider(tmp_path: Path) -> None:
    async def seed() -> UUID:
        async with build_app() as resources:
            p = await resources.projects.create("vis-test", tmp_path, max_cycles=1, config={})
            await resources.projects.transition(
                p.project_id, expected=Phase.INTAKE, to=Phase.VISUAL_DESIGN
            )
            return p.project_id

    pid = asyncio.run(seed())
    res = runner.invoke(app, ["work", str(pid), "--provider", "claudeloop"])
    assert res.exit_code != 0


def test_work_once_claudeloop_provider(tmp_path: Path) -> None:
    async def seed() -> UUID:
        async with build_app() as resources:
            p = await resources.projects.create("cl-test", tmp_path, max_cycles=1, config={})
            await resources.projects.transition(
                p.project_id, expected=Phase.INTAKE, to=Phase.DESIGN
            )
            return p.project_id

    pid = asyncio.run(seed())
    res = runner.invoke(app, ["work", str(pid), "--provider", "claudeloop"])
    assert res.exit_code == 0, res.output
    assert "no ready job" in res.output


def test_enqueue_design_unknown_project() -> None:
    from uuid import uuid4

    res = runner.invoke(app, ["design", "resume", str(uuid4())])
    assert res.exit_code != 0


def test_enqueue_design_wrong_phase(tmp_path: Path) -> None:
    async def seed() -> UUID:
        async with build_app() as resources:
            p = await resources.projects.create("phase-test", tmp_path, max_cycles=1, config={})
            await resources.projects.transition(p.project_id, expected=Phase.INTAKE, to=Phase.BUILD)
            return p.project_id

    pid = asyncio.run(seed())
    res = runner.invoke(app, ["design", "resume", str(pid)])
    assert res.exit_code != 0


def test_accept_design_unknown_project() -> None:
    from uuid import uuid4

    res = runner.invoke(app, ["design", "accept", str(uuid4())])
    assert res.exit_code != 0


def test_accept_design_with_spec_json(tmp_path: Path) -> None:
    import json as _json

    spec_json = tmp_path / "spec.json"
    spec_data = {
        "objective": "Ship",
        "constraints": [{"text": "Offline", "kind": "hard"}],
        "non_goals": [],
        "criteria": [
            {
                "criterion_id": "AC-1",
                "given": "input",
                "when": "run",
                "then": "output",
                "fit": "passes",
            }
        ],
        "nfrs": [],
        "walking_skeleton": "path",
    }
    spec_json.write_text(_json.dumps(spec_data))

    async def seed() -> UUID:
        async with build_app() as resources:
            p = await resources.projects.create(
                "spec-accept", tmp_path / "repo", max_cycles=1, config={}
            )
            await resources.projects.transition(
                p.project_id, expected=Phase.INTAKE, to=Phase.DESIGN
            )
            return p.project_id

    pid = asyncio.run(seed())
    res = runner.invoke(app, ["design", "accept", str(pid), "--spec-json", str(spec_json)])
    assert res.exit_code == 0, res.output
    assert "accepted design" in res.output


# ── watch command with real project ──────────────────────────────────────────


def test_watch_with_replay(tmp_path: Path) -> None:
    from unittest.mock import AsyncMock, patch

    pid = asyncio.run(_seed_ledger_project(tmp_path))
    with patch("vibey.tui.dashboard.VibeyReplayApp") as mock_replay:
        mock_replay.return_value.run_async = AsyncMock()
        res = runner.invoke(app, ["watch", str(pid), "--replay"])
        assert res.exit_code == 0, res.output
        mock_replay.assert_called_once()


def test_watch_with_latest_project(tmp_path: Path) -> None:
    from unittest.mock import AsyncMock, patch

    asyncio.run(_seed_status_project(tmp_path))
    with patch("vibey.tui.dashboard.VibeyDashboardApp") as mock_app_cls:
        mock_app_cls.return_value.run_async = AsyncMock()
        res = runner.invoke(app, ["watch"])
        assert res.exit_code == 0, res.output
        mock_app_cls.assert_called_once()


def test_watch_with_explicit_project(tmp_path: Path) -> None:
    from unittest.mock import AsyncMock, patch

    pid = asyncio.run(_seed_status_project(tmp_path))
    with patch("vibey.tui.dashboard.VibeyDashboardApp") as mock_app_cls:
        mock_app_cls.return_value.run_async = AsyncMock()
        res = runner.invoke(app, ["watch", str(pid)])
        assert res.exit_code == 0, res.output
        mock_app_cls.assert_called_once()


# ── deploy status/inspect branch coverage ────────────────────────────────────


def test_deploy_status_no_deployment_events(tmp_path: Path) -> None:
    async def seed() -> UUID:
        async with build_app() as resources:
            p = await resources.projects.create("no-dep-ev", tmp_path, max_cycles=1, config={})
            return p.project_id

    pid = asyncio.run(seed())
    res = runner.invoke(app, ["deploy", "status", str(pid)])
    assert res.exit_code == 0, res.output
    assert "(none)" in res.output


def test_deploy_status_event_without_endpoint(tmp_path: Path) -> None:
    async def seed() -> UUID:
        async with build_app() as resources:
            p = await resources.projects.create("no-endpoint", tmp_path, max_cycles=1, config={})
            await resources.ledger.append(
                LedgerEventDraft(
                    project_id=p.project_id,
                    cycle=p.cycle,
                    phase=Phase.INTAKE,
                    kind=EventKind.ARTIFACT_PRODUCED,
                    engine_id=None,
                    job_id=None,
                    causation_id=None,
                    correlation_id=p.project_id,
                    provenance=Provenance.TRUSTED,
                    produced_at=datetime.now(UTC),
                    payload={
                        "artifact_type": "deployment_verification",
                        "outputs": {"status": "ok"},
                    },
                    digest="test",
                )
            )
            return p.project_id

    pid = asyncio.run(seed())
    res = runner.invoke(app, ["deploy", "status", str(pid)])
    assert res.exit_code == 0, res.output
    assert "(none)" in res.output


def test_deploy_inspect_no_spec_events(tmp_path: Path) -> None:
    async def seed() -> UUID:
        async with build_app() as resources:
            p = await resources.projects.create("no-spec-ev", tmp_path, max_cycles=1, config={})
            return p.project_id

    pid = asyncio.run(seed())
    res = runner.invoke(app, ["deploy", "inspect", str(pid)])
    assert res.exit_code == 0, res.output
    assert "default" in res.output


# ── doctor command ────────────────────────────────────────────────────────────


def test_doctor_basic_lists_all_engines() -> None:
    res = runner.invoke(app, ["doctor"])
    assert res.exit_code == 0, res.output
    assert "claudeloop" in res.output


def test_doctor_specific_engine() -> None:
    res = runner.invoke(app, ["doctor", "--engine", "claudeloop"])
    assert res.exit_code == 0, res.output
    assert "claudeloop" in res.output


def test_doctor_unknown_engine() -> None:
    res = runner.invoke(app, ["doctor", "--engine", "nonexistent"])
    assert res.exit_code == 1


def test_doctor_no_detail_skips_detail_line() -> None:
    from unittest.mock import AsyncMock, patch

    from vibey.application.dto import PreflightResult

    fake_result = PreflightResult(installed=True, auth_ok=True, version="1.0.0", detail="")
    with patch(
        "vibey.infrastructure.engines.loop_process_adapter.LoopProcessAdapter.preflight",
        new=AsyncMock(return_value=fake_result),
    ):
        res = runner.invoke(app, ["doctor", "--engine", "claudeloop"])
    assert res.exit_code == 0, res.output
    assert "detail:" not in res.output
    assert "installed" in res.output


def test_doctor_shows_detail_when_present() -> None:
    from unittest.mock import AsyncMock, patch

    from vibey.application.dto import PreflightResult

    fake_result = PreflightResult(
        installed=False, auth_ok=False, version=None, detail="claude not found in PATH"
    )
    with patch(
        "vibey.infrastructure.engines.loop_process_adapter.LoopProcessAdapter.preflight",
        new=AsyncMock(return_value=fake_result),
    ):
        res = runner.invoke(app, ["doctor", "--engine", "claudeloop"])
    assert res.exit_code == 0, res.output
    assert "detail:" in res.output
    assert "claude not found in PATH" in res.output


def test_doctor_with_conformance() -> None:
    from unittest.mock import AsyncMock, patch

    from vibey.application.dto import ConformanceCheckResult, ConformanceReport
    from vibey.domain.engine import EngineId

    fake_report = ConformanceReport(
        engine_id=EngineId.CLAUDELOOP,
        checks=(
            ConformanceCheckResult(name="preflight", ok=True),
            ConformanceCheckResult(name="start_stop", ok=True),
        ),
    )
    with patch(
        "vibey.application.conformance.run_conformance",
        new=AsyncMock(return_value=fake_report),
    ):
        res = runner.invoke(app, ["doctor", "--conformance", "--engine", "claudeloop"])
    assert res.exit_code == 0, res.output
    assert "PASS" in res.output


def test_doctor_with_conformance_failure() -> None:
    from unittest.mock import AsyncMock, patch

    from vibey.application.dto import ConformanceCheckResult, ConformanceReport
    from vibey.domain.engine import EngineId

    fake_report = ConformanceReport(
        engine_id=EngineId.CLAUDELOOP,
        checks=(
            ConformanceCheckResult(name="preflight", ok=True),
            ConformanceCheckResult(name="start_stop", ok=False, detail="timed out"),
        ),
    )
    with patch(
        "vibey.application.conformance.run_conformance",
        new=AsyncMock(return_value=fake_report),
    ):
        res = runner.invoke(app, ["doctor", "--conformance", "--engine", "claudeloop"])
    assert res.exit_code == 1
    assert "FAIL" in res.output
    assert "timed out" in res.output


# ── worker command ────────────────────────────────────────────────────────────


def test_worker_once_no_job(tmp_path: Path) -> None:
    async def seed_empty() -> None:
        async with build_app() as resources:
            await resources.projects.create("empty-worker", tmp_path, max_cycles=1, config={})

    asyncio.run(seed_empty())
    from unittest.mock import AsyncMock, patch

    with patch("vibey.infrastructure.db.notifier.PostgresJobReadyNotifier") as mock_notifier_cls:
        mock_notifier = AsyncMock()
        mock_notifier_cls.return_value = mock_notifier
        res = runner.invoke(app, ["worker", "--once"])
    assert res.exit_code == 0, res.output
    assert "no ready job" in res.output


def test_worker_once_with_job(tmp_path: Path) -> None:
    async def seed() -> UUID:
        async with build_app() as resources:
            p = await resources.projects.create("worker-proj", tmp_path, max_cycles=1, config={})
            from vibey.domain.job import idempotency_key

            await resources.jobs.enqueue(
                EnqueueRequest(
                    project_id=p.project_id,
                    cycle=p.cycle,
                    phase=Phase.INTAKE,
                    kind="test.work",
                    idempotency_key=idempotency_key(p.project_id, p.cycle, "test.work", "1"),
                    requirement={},
                )
            )
            return p.project_id

    asyncio.run(seed())
    from unittest.mock import AsyncMock, patch

    with patch("vibey.infrastructure.db.notifier.PostgresJobReadyNotifier") as mock_notifier_cls:
        mock_notifier = AsyncMock()
        mock_notifier_cls.return_value = mock_notifier
        res = runner.invoke(app, ["worker", "--once"])
    assert res.exit_code == 0, res.output
    assert "claimed job" in res.output
    assert "completed job" in res.output


def test_worker_no_projects() -> None:
    from unittest.mock import AsyncMock, patch

    with patch("vibey.infrastructure.db.notifier.PostgresJobReadyNotifier") as mock_notifier_cls:
        mock_notifier = AsyncMock()
        mock_notifier_cls.return_value = mock_notifier
        res = runner.invoke(app, ["worker", "--once"])
    assert res.exit_code == 1
    assert "no projects found" in res.output


def test_worker_continuous_processes_then_waits(tmp_path: Path) -> None:
    async def seed() -> None:
        async with build_app() as resources:
            p = await resources.projects.create("cont-worker", tmp_path, max_cycles=1, config={})
            from vibey.domain.job import idempotency_key as idem_key

            await resources.jobs.enqueue(
                EnqueueRequest(
                    project_id=p.project_id,
                    cycle=p.cycle,
                    phase=Phase.INTAKE,
                    kind="test.work",
                    idempotency_key=idem_key(p.project_id, p.cycle, "test.work", "1"),
                    requirement={},
                )
            )

    asyncio.run(seed())
    from unittest.mock import AsyncMock, patch

    with patch("vibey.infrastructure.db.notifier.PostgresJobReadyNotifier") as mock_notifier_cls:
        mock_notifier = AsyncMock()
        mock_notifier.wait_for_job_ready = AsyncMock(side_effect=KeyboardInterrupt)
        mock_notifier_cls.return_value = mock_notifier
        res = runner.invoke(app, ["worker"])
    assert "claimed job" in res.output
    assert "completed job" in res.output


def test_worker_invalid_engine() -> None:
    res = runner.invoke(app, ["worker", "--engines", "nonexistent"])
    assert res.exit_code == 2


# ── watch state_fetcher coverage ──────────────────────────────────────────────


def test_watch_state_fetcher_is_invoked(tmp_path: Path) -> None:
    from unittest.mock import AsyncMock, patch

    pid = asyncio.run(_seed_status_project(tmp_path))
    fetcher_called = False

    with patch("vibey.tui.dashboard.VibeyDashboardApp") as mock_app_cls:

        def capture_init(**kwargs: object) -> AsyncMock:
            fetcher = kwargs.get("state_fetcher")

            async def run_async_calls_fetcher() -> None:
                nonlocal fetcher_called
                if fetcher is not None:
                    await fetcher()
                    fetcher_called = True

            m = AsyncMock()
            m.run_async = run_async_calls_fetcher
            return m

        mock_app_cls.side_effect = capture_init
        res = runner.invoke(app, ["watch", str(pid)])
        assert res.exit_code == 0, res.output
    assert fetcher_called
