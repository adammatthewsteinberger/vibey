# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
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

    from vibey.application.dto import ConformanceCheckResult, ConformanceReport, PreflightResult
    from vibey.domain.engine import EngineId

    fake_report = ConformanceReport(
        engine_id=EngineId.CLAUDELOOP,
        checks=(
            ConformanceCheckResult(name="preflight", ok=True),
            ConformanceCheckResult(name="start_stop", ok=True),
        ),
    )
    # preflight() must also be mocked: the CLI only calls run_conformance
    # when preflight.installed is True, and a CI runner has no engine
    # binaries on PATH -- leaving this real makes the test pass only on a
    # machine that happens to have claudeloop installed.
    with (
        patch(
            "vibey.infrastructure.engines.loop_process_adapter.LoopProcessAdapter.preflight",
            new=AsyncMock(
                return_value=PreflightResult(installed=True, version="0.5.5", auth_ok=True)
            ),
        ),
        patch(
            "vibey.application.conformance.run_conformance",
            new=AsyncMock(return_value=fake_report),
        ),
    ):
        res = runner.invoke(app, ["doctor", "--conformance", "--engine", "claudeloop"])
    assert res.exit_code == 0, res.output
    assert "PASS" in res.output


def test_doctor_with_conformance_failure() -> None:
    from unittest.mock import AsyncMock, patch

    from vibey.application.dto import ConformanceCheckResult, ConformanceReport, PreflightResult
    from vibey.domain.engine import EngineId

    fake_report = ConformanceReport(
        engine_id=EngineId.CLAUDELOOP,
        checks=(
            ConformanceCheckResult(name="preflight", ok=True),
            ConformanceCheckResult(name="start_stop", ok=False, detail="timed out"),
        ),
    )
    with (
        patch(
            "vibey.infrastructure.engines.loop_process_adapter.LoopProcessAdapter.preflight",
            new=AsyncMock(
                return_value=PreflightResult(installed=True, version="0.5.5", auth_ok=True)
            ),
        ),
        patch(
            "vibey.application.conformance.run_conformance",
            new=AsyncMock(return_value=fake_report),
        ),
    ):
        res = runner.invoke(app, ["doctor", "--conformance", "--engine", "claudeloop"])
    assert res.exit_code == 1
    assert "FAIL" in res.output
    assert "timed out" in res.output


# ── worker command ────────────────────────────────────────────────────────────


@pytest.fixture()
def _fast_engine_preflight():  # type: ignore[no-untyped-def]
    """The worker's startup preflight sweep would otherwise spawn real
    engine subprocesses (doctor runs) in every worker CLI test."""
    from unittest.mock import AsyncMock, patch

    from vibey.application.dto import PreflightResult

    with patch(
        "vibey.infrastructure.engines.loop_process_adapter.LoopProcessAdapter.preflight",
        new=AsyncMock(return_value=PreflightResult(installed=True, version="1.0.0", auth_ok=True)),
    ):
        yield


@pytest.mark.usefixtures("_fast_engine_preflight")
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


@pytest.mark.usefixtures("_fast_engine_preflight")
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
    assert "processed one job" in res.output


@pytest.mark.usefixtures("_fast_engine_preflight")
def test_worker_unknown_kind_burns_an_attempt(tmp_path: Path) -> None:
    """The dispatcher rejects unknown kinds as VIBEY failures -- the poison
    path is now a feature to assert, not the stub's silent ack."""

    async def seed() -> UUID:
        async with build_app() as resources:
            p = await resources.projects.create("poison-proj", tmp_path, max_cycles=1, config={})
            from vibey.domain.job import idempotency_key

            job = await resources.jobs.enqueue(
                EnqueueRequest(
                    project_id=p.project_id,
                    cycle=p.cycle,
                    phase=Phase.INTAKE,
                    kind="test.work",
                    idempotency_key=idempotency_key(p.project_id, p.cycle, "test.work", "1"),
                    requirement={},
                )
            )
            return job.id

    job_id = asyncio.run(seed())
    from unittest.mock import AsyncMock, patch

    with patch("vibey.infrastructure.db.notifier.PostgresJobReadyNotifier") as mock_notifier_cls:
        mock_notifier_cls.return_value = AsyncMock()
        res = runner.invoke(app, ["worker", "--once"])
    assert res.exit_code == 0, res.output
    assert "processed one job" in res.output

    async def inspect() -> tuple[int, str]:
        async with build_app() as resources:
            job = await resources.jobs.get(job_id)
            assert job is not None
            assert job.last_error is not None
            return job.attempts, str(job.last_error)

    attempts, error = asyncio.run(inspect())
    assert attempts == 1
    assert "no handler registered" in error


@pytest.mark.usefixtures("_fast_engine_preflight")
def test_worker_no_projects() -> None:
    from unittest.mock import AsyncMock, patch

    with patch("vibey.infrastructure.db.notifier.PostgresJobReadyNotifier") as mock_notifier_cls:
        mock_notifier = AsyncMock()
        mock_notifier_cls.return_value = mock_notifier
        res = runner.invoke(app, ["worker", "--once"])
    assert res.exit_code == 1
    assert "no projects found" in res.output


@pytest.mark.usefixtures("_fast_engine_preflight")
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
    assert "processed one job" in res.output


@pytest.mark.usefixtures("_fast_engine_preflight")
def test_worker_invalid_engine() -> None:
    res = runner.invoke(app, ["worker", "--engines", "nonexistent"])
    assert res.exit_code == 2


@pytest.mark.usefixtures("_fast_engine_preflight")
def test_worker_invalid_provider() -> None:
    res = runner.invoke(app, ["worker", "--provider", "nonexistent"])
    assert res.exit_code == 2
    assert "provider must be" in res.output


@pytest.mark.usefixtures("_fast_engine_preflight")
def test_worker_project_flag_selects_that_project(tmp_path: Path) -> None:
    async def seed() -> UUID:
        async with build_app() as resources:
            older = await resources.projects.create(
                "older-proj", tmp_path / "older", max_cycles=1, config={}
            )
            await resources.projects.create(
                "newer-proj", tmp_path / "newer", max_cycles=1, config={}
            )
            return older.project_id

    older_id = asyncio.run(seed())
    from unittest.mock import AsyncMock, patch

    with patch("vibey.infrastructure.db.notifier.PostgresJobReadyNotifier") as mock_notifier_cls:
        mock_notifier_cls.return_value = AsyncMock()
        res = runner.invoke(app, ["worker", "--once", "--project", str(older_id)])
    assert res.exit_code == 0, res.output
    assert "project=older-proj" in res.output
    assert "no ready job" in res.output


@pytest.mark.usefixtures("_fast_engine_preflight")
def test_worker_unknown_project_exits_1(tmp_path: Path) -> None:
    from unittest.mock import AsyncMock, patch
    from uuid import uuid4

    async def seed() -> None:
        async with build_app() as resources:
            await resources.projects.create("some-proj", tmp_path, max_cycles=1, config={})

    asyncio.run(seed())
    with patch("vibey.infrastructure.db.notifier.PostgresJobReadyNotifier") as mock_notifier_cls:
        mock_notifier_cls.return_value = AsyncMock()
        res = runner.invoke(app, ["worker", "--once", "--project", str(uuid4())])
    assert res.exit_code == 1
    assert "no projects found" in res.output


@pytest.mark.usefixtures("_fast_engine_preflight")
def test_worker_engines_allow_list_with_claudeloop(tmp_path: Path) -> None:
    async def seed() -> None:
        async with build_app() as resources:
            await resources.projects.create("eng-proj", tmp_path, max_cycles=1, config={})

    asyncio.run(seed())
    from unittest.mock import AsyncMock, patch

    with patch("vibey.infrastructure.db.notifier.PostgresJobReadyNotifier") as mock_notifier_cls:
        mock_notifier_cls.return_value = AsyncMock()
        res = runner.invoke(app, ["worker", "--once", "--engines", "claudeloop,agyloop"])
    assert res.exit_code == 0, res.output
    assert "no ready job" in res.output


@pytest.mark.usefixtures("_fast_engine_preflight")
def test_worker_engines_allow_list_without_claudeloop(tmp_path: Path) -> None:
    """The implementer falls back to the first allowed engine when
    claudeloop isn't in the allow list."""

    async def seed() -> None:
        async with build_app() as resources:
            await resources.projects.create("eng2-proj", tmp_path, max_cycles=1, config={})

    asyncio.run(seed())
    from unittest.mock import AsyncMock, patch

    with patch("vibey.infrastructure.db.notifier.PostgresJobReadyNotifier") as mock_notifier_cls:
        mock_notifier_cls.return_value = AsyncMock()
        res = runner.invoke(app, ["worker", "--once", "--engines", "agyloop"])
    assert res.exit_code == 0, res.output
    assert "no ready job" in res.output


@pytest.mark.usefixtures("_fast_engine_preflight")
def test_worker_provider_claudeloop_constructs_live_providers(tmp_path: Path) -> None:
    """--provider claudeloop builds the live design provider without any
    subprocess spawn at construction time."""

    async def seed() -> None:
        async with build_app() as resources:
            await resources.projects.create("live-prov-proj", tmp_path, max_cycles=1, config={})

    asyncio.run(seed())
    from unittest.mock import AsyncMock, patch

    with patch("vibey.infrastructure.db.notifier.PostgresJobReadyNotifier") as mock_notifier_cls:
        mock_notifier_cls.return_value = AsyncMock()
        res = runner.invoke(app, ["worker", "--once", "--provider", "claudeloop"])
    assert res.exit_code == 0, res.output
    assert "provider=claudeloop" in res.output
    assert "no ready job" in res.output


@pytest.mark.usefixtures("_fast_engine_preflight")
def test_worker_parallelism_spawns_gathered_loops(tmp_path: Path) -> None:
    """-j 2 continuous takes the gather branch; the mocked notifier's
    KeyboardInterrupt ends the run once both loops go idle."""

    async def seed() -> None:
        async with build_app() as resources:
            await resources.projects.create("par-proj", tmp_path, max_cycles=1, config={})

    asyncio.run(seed())
    from unittest.mock import AsyncMock, patch

    with patch("vibey.infrastructure.db.notifier.PostgresJobReadyNotifier") as mock_notifier_cls:
        mock_notifier = AsyncMock()
        mock_notifier.wait_for_job_ready = AsyncMock(side_effect=KeyboardInterrupt)
        mock_notifier_cls.return_value = mock_notifier
        res = runner.invoke(app, ["worker", "-j", "2"])
    assert "parallelism=2" in res.output


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


@pytest.mark.usefixtures("_fast_engine_preflight")
def test_worker_warns_about_engines_without_conformance(tmp_path: Path) -> None:
    """The sweep records preflight but never grants conformance -- until
    doctor --conformance --record runs, engine-driven jobs can't select."""

    async def seed() -> None:
        async with build_app() as resources:
            await resources.projects.create("sweep-proj", tmp_path, max_cycles=1, config={})

    asyncio.run(seed())
    from unittest.mock import AsyncMock, patch

    with patch("vibey.infrastructure.db.notifier.PostgresJobReadyNotifier") as mock_notifier_cls:
        mock_notifier_cls.return_value = AsyncMock()
        res = runner.invoke(app, ["worker", "--once"])
    assert res.exit_code == 0, res.output
    assert "no recorded conformance" in res.output
    assert "doctor --conformance --record" in res.output

    async def check() -> int:
        async with build_app() as resources:
            latest = await resources.projects.get_latest()
            assert latest is not None
            records = await resources.engine_health_service.list_for_project(latest.project_id)
            assert all(r.installed for r in records)
            assert all(not r.conformance_ok for r in records)
            return len(records)

    assert asyncio.run(check()) == 4


@pytest.mark.usefixtures("_fast_engine_preflight")
def test_worker_stays_quiet_when_every_engine_has_conformance(tmp_path: Path) -> None:
    from vibey.application.dto import PreflightResult

    async def seed() -> None:
        async with build_app() as resources:
            project = await resources.projects.create(
                "quiet-sweep-proj", tmp_path, max_cycles=1, config={}
            )
            good = PreflightResult(installed=True, version="1.0.0", auth_ok=True)
            for engine_id in resources.engine_adapters:
                await resources.engine_health_service.update_from_preflight(
                    project.project_id, engine_id, good, conformance_ok=True
                )

    asyncio.run(seed())
    from unittest.mock import AsyncMock, patch

    with patch("vibey.infrastructure.db.notifier.PostgresJobReadyNotifier") as mock_notifier_cls:
        mock_notifier_cls.return_value = AsyncMock()
        res = runner.invoke(app, ["worker", "--once"])
    assert res.exit_code == 0, res.output
    assert "no recorded conformance" not in res.output


def test_doctor_record_persists_preflight_only(tmp_path: Path) -> None:
    from unittest.mock import AsyncMock, patch

    from vibey.application.dto import PreflightResult

    async def seed() -> None:
        async with build_app() as resources:
            await resources.projects.create("doc-rec-proj", tmp_path, max_cycles=1, config={})

    asyncio.run(seed())
    with patch(
        "vibey.infrastructure.engines.loop_process_adapter.LoopProcessAdapter.preflight",
        new=AsyncMock(return_value=PreflightResult(installed=True, version="9.9.9", auth_ok=True)),
    ):
        res = runner.invoke(app, ["doctor", "--record", "--engine", "claudeloop"])
    assert res.exit_code == 0, res.output
    assert "recorded preflight for claudeloop" in res.output

    async def check() -> None:
        async with build_app() as resources:
            latest = await resources.projects.get_latest()
            assert latest is not None
            record = await resources.engine_health_repo.get(latest.project_id, "claudeloop")
            assert record is not None
            assert record.version == "9.9.9"
            assert record.conformance_ok is False

    asyncio.run(check())


def test_doctor_record_with_conformance_grants_eligibility(tmp_path: Path) -> None:
    from unittest.mock import AsyncMock, patch

    from vibey.application.dto import (
        ConformanceCheckResult,
        ConformanceReport,
        PreflightResult,
    )

    async def seed() -> None:
        async with build_app() as resources:
            await resources.projects.create("doc-conf-proj", tmp_path, max_cycles=1, config={})

    asyncio.run(seed())
    from vibey.domain.engine import EngineId

    ok_report = ConformanceReport(
        engine_id=EngineId.CLAUDELOOP,
        checks=(ConformanceCheckResult(name="binary", ok=True),),
    )
    with (
        patch(
            "vibey.infrastructure.engines.loop_process_adapter.LoopProcessAdapter.preflight",
            new=AsyncMock(
                return_value=PreflightResult(installed=True, version="9.9.9", auth_ok=True)
            ),
        ),
        patch(
            "vibey.application.conformance.run_conformance",
            new=AsyncMock(return_value=ok_report),
        ),
    ):
        res = runner.invoke(app, ["doctor", "--conformance", "--record", "--engine", "claudeloop"])
    assert res.exit_code == 0, res.output
    assert "recorded engine_health for claudeloop" in res.output

    async def check() -> None:
        async with build_app() as resources:
            latest = await resources.projects.get_latest()
            assert latest is not None
            record = await resources.engine_health_repo.get(latest.project_id, "claudeloop")
            assert record is not None
            assert record.conformance_ok is True

    asyncio.run(check())


def test_doctor_record_without_projects_exits_1() -> None:
    from unittest.mock import AsyncMock, patch

    from vibey.application.dto import PreflightResult

    with patch(
        "vibey.infrastructure.engines.loop_process_adapter.LoopProcessAdapter.preflight",
        new=AsyncMock(return_value=PreflightResult(installed=True, version="1.0.0", auth_ok=True)),
    ):
        res = runner.invoke(app, ["doctor", "--record", "--engine", "claudeloop"])
    assert res.exit_code == 1
    assert "no projects found" in res.output


def test_doctor_record_specific_project(tmp_path: Path) -> None:
    from unittest.mock import AsyncMock, patch

    from vibey.application.dto import PreflightResult

    async def seed() -> UUID:
        async with build_app() as resources:
            older = await resources.projects.create(
                "rec-older", tmp_path / "older", max_cycles=1, config={}
            )
            await resources.projects.create(
                "rec-newer", tmp_path / "newer", max_cycles=1, config={}
            )
            return older.project_id

    older_id = asyncio.run(seed())
    with patch(
        "vibey.infrastructure.engines.loop_process_adapter.LoopProcessAdapter.preflight",
        new=AsyncMock(return_value=PreflightResult(installed=True, version="1.0.0", auth_ok=True)),
    ):
        res = runner.invoke(
            app, ["doctor", "--record", "--engine", "claudeloop", "--project", str(older_id)]
        )
    assert res.exit_code == 0, res.output

    async def check() -> None:
        async with build_app() as resources:
            record = await resources.engine_health_repo.get(older_id, "claudeloop")
            assert record is not None

    asyncio.run(check())


def test_worker_rejects_unknown_azure_mode() -> None:
    res = runner.invoke(app, ["worker", "--azure", "gcp"])
    assert res.exit_code == 2
    assert "memory" in res.output and "az" in res.output


def test_worker_azure_az_requires_a_logged_in_cli() -> None:
    from unittest.mock import patch

    class _NotLoggedIn:
        returncode = 1
        stdout = ""
        stderr = "Please run 'az login'"

    with patch("vibey.cli.main.subprocess.run", return_value=_NotLoggedIn()):
        res = runner.invoke(app, ["worker", "--azure", "az"])
    assert res.exit_code == 1
    assert "az login" in res.output


@pytest.mark.usefixtures("_fast_engine_preflight")
def test_worker_azure_az_builds_the_real_adapter_when_logged_in(tmp_path: Path) -> None:
    from unittest.mock import AsyncMock, patch

    async def seed() -> None:
        async with build_app() as resources:
            await resources.projects.create("az-proj", tmp_path, max_cycles=1, config={})

    asyncio.run(seed())

    class _LoggedIn:
        returncode = 0
        stdout = ""
        stderr = ""

    with (
        patch("vibey.cli.main.subprocess.run", return_value=_LoggedIn()),
        patch("vibey.infrastructure.db.notifier.PostgresJobReadyNotifier") as notifier_cls,
    ):
        notifier_cls.return_value = AsyncMock()
        res = runner.invoke(app, ["worker", "--azure", "az", "--once"])
    assert res.exit_code == 0, res.output


def test_worker_without_wait_still_exits_when_no_project_exists() -> None:
    """The one-shot CLI default stays honest: nothing to work on is an
    error, not a hang."""
    res = runner.invoke(app, ["worker"])

    assert res.exit_code == 1
    assert "no projects found" in res.output


@pytest.mark.usefixtures("_fast_engine_preflight")
def test_worker_wait_for_project_polls_until_one_appears(tmp_path: Path) -> None:
    """A long-lived deployment must not exit when no project exists yet:
    exiting is a restart loop that ends only when a human creates one, and
    the crash counter makes a healthy worker look broken (observed on a
    real minikube install before this flag). The project is created from
    inside the sleep, exactly as it would be while a Deployment waits."""
    from unittest.mock import AsyncMock, patch

    async def create_project(_seconds: float) -> None:
        async with build_app() as resources:
            await resources.projects.create("late", tmp_path, max_cycles=1, config={})

    with (
        patch("vibey.cli.main.asyncio.sleep", new=AsyncMock(side_effect=create_project)) as slept,
        patch("vibey.infrastructure.db.notifier.PostgresJobReadyNotifier") as notifier_cls,
    ):
        notifier_cls.return_value = AsyncMock()
        res = runner.invoke(app, ["worker", "--wait-for-project", "1", "--once"])

    assert res.exit_code == 0, res.output
    assert "no project yet; polling every 1s" in res.output
    assert slept.await_count == 1


@pytest.mark.usefixtures("_fast_engine_preflight")
def test_worker_drains_on_sigterm_rather_than_claiming_more(tmp_path: Path) -> None:
    """Kubernetes scale-in is SIGTERM, a wait, then SIGKILL. Before this,
    the worker ignored SIGTERM entirely: measured on minikube, a pod kept
    processing jobs 77s after the signal and five 'terminated' pods still
    held live Postgres connections while the Deployment reported 0/0.
    Scale-to-zero freed nothing and the eventual SIGKILL would land
    mid-session. The signal arrives here exactly where a real scale-in
    delivers it -- while the worker sits idle waiting for the next job."""
    import signal
    from unittest.mock import AsyncMock, patch

    async def seed() -> None:
        async with build_app() as resources:
            await resources.projects.create("drain", tmp_path, max_cycles=1, config={})

    asyncio.run(seed())

    async def sigterm(*_args: object, **_kwargs: object) -> None:
        os.kill(os.getpid(), signal.SIGTERM)
        # Let the loop's signal self-pipe deliver it before the next claim.
        await asyncio.sleep(0.1)

    with patch("vibey.infrastructure.db.notifier.PostgresJobReadyNotifier") as notifier_cls:
        notifier = AsyncMock()
        notifier.wait_for_job_ready = AsyncMock(side_effect=sigterm)
        notifier_cls.return_value = notifier
        res = runner.invoke(app, ["worker", "-j", "1"])

    assert res.exit_code == 0, res.output
    assert "draining on SIGTERM" in res.output
    # The point of the flag: it stopped claiming. One idle wait, then out.
    assert notifier.wait_for_job_ready.await_count == 1


def test_doctor_cluster_passes_against_a_migrated_database(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The in-cluster preflight is a different question from engine health:
    it asks whether this deployment is wired correctly at all."""
    from unittest.mock import patch

    async def migrate() -> None:
        async with build_app():
            pass

    asyncio.run(migrate())
    monkeypatch.chdir(tmp_path)

    # No engine binaries: the scripted-provider image, which is the state
    # of the published image today and not a fault.
    with patch("shutil.which", return_value=None):
        res = runner.invoke(app, ["doctor", "--cluster"])

    assert res.exit_code == 0, res.output
    assert "PASS database" in res.output
    assert "PASS migrations" in res.output


def test_doctor_cluster_exits_nonzero_when_the_database_is_unreachable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A preflight that reported success against a database nobody reached
    would be worse than no preflight."""
    from unittest.mock import patch

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("VIBEY_PG_URL", "postgresql://nobody@127.0.0.1:1/nothing")

    with patch("shutil.which", return_value=None):
        res = runner.invoke(app, ["doctor", "--cluster"])

    assert res.exit_code == 1
    assert "FAIL database" in res.output


def test_operator_command_runs_the_operator_scoped_to_a_namespace() -> None:
    from unittest.mock import patch

    with patch("vibey.infrastructure.operator.run") as run_operator:
        res = runner.invoke(app, ["operator", "--namespace", "vibey"])

    assert res.exit_code == 0, res.output
    run_operator.assert_called_once_with(namespace="vibey")


def test_operator_command_explains_itself_when_the_extra_is_not_installed() -> None:
    """kopf is an optional extra, so the failure mode has to name the fix
    rather than surfacing a raw ImportError traceback."""
    import sys
    from unittest.mock import patch

    with patch.dict(sys.modules, {"vibey.infrastructure.operator": None}):
        res = runner.invoke(app, ["operator"])

    assert res.exit_code == 1
    assert "vibey[operator]" in res.output


async def test_recorded_spend_is_visible_to_the_budget_brake(tmp_path: Path) -> None:
    """The bug this guards: DESIGN spend reached no ledger, so
    LedgerBudgetSource summed zero for the phase and the project's cap --
    however large or small -- could never trip. Measured live before the
    fix: 83 QuestionAsked events across eight projects and not one
    TurnCompleted or BudgetSpent, while a single design turn had cost
    $0.44.
    """
    from vibey.application.budget_source import LedgerBudgetSource
    from vibey.cli.main import _build_spend_recorder
    from vibey.domain.phase import Phase

    async with build_app() as resources:
        project = await resources.projects.create("brake", tmp_path, max_cycles=1, config={})
        record = _build_spend_recorder(
            resources.ledger, project.project_id, project.cycle, Phase.DESIGN
        )
        await record(2, 0.6916597)

        source = LedgerBudgetSource(resources.ledger, max_dollars=200.0)
        ledger = await source.current(project.project_id, project.cycle)

    assert ledger.turns_spent == 2
    assert ledger.dollars_spent == pytest.approx(0.6916597)


def test_recover_no_args() -> None:
    result = runner.invoke(app, ["recover"])
    assert result.exit_code == 1
    assert "Must specify either --project <id> or --all" in result.stdout


def test_recover_all_projects(tmp_path: Path) -> None:
    async def seed() -> None:
        async with build_app() as resources:
            _ = resources

    asyncio.run(seed())

    result = runner.invoke(app, ["recover", "--all"])
    assert result.exit_code == 0
    assert "Recovered 0 stuck job(s)." in result.stdout


def test_recover_with_project(tmp_path: Path) -> None:
    async def seed() -> None:
        async with build_app() as resources:
            _ = resources

    asyncio.run(seed())

    import uuid

    pid = str(uuid.uuid4())
    result = runner.invoke(app, ["recover", "--project", pid])
    assert result.exit_code == 0
    assert "Recovered 0 stuck job(s)." in result.stdout
