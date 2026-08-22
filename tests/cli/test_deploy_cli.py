# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
import asyncio
import os
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import asyncpg
import pytest
from typer.testing import CliRunner

from vibey.bootstrap import build_app, database_url
from vibey.cli.main import app
from vibey.domain.deployment import (
    AzureTargetScope,
    CostBoundary,
    DeploymentSpec,
    IdentityAuthority,
    RecoveryPolicy,
    TopologyConfig,
    VerificationContract,
)
from vibey.domain.ledger import EventKind, Provenance, digest_event
from vibey.domain.phase import Phase
from vibey.infrastructure.engines.tailer import LedgerEventDraft

# Typer force-enables rich ANSI styling whenever GITHUB_ACTIONS is set
# (typer/rich_utils.py), which CI always has and a local shell never does.
# That embeds escape codes inside option names, breaking plain substring
# checks against --help output -- disable it the way Typer itself exposes.
runner = CliRunner(env={"_TYPER_FORCE_DISABLE_TERMINAL": "1"})


def test_deploy_help_shows_subcommands() -> None:
    result = runner.invoke(app, ["deploy", "--help"])
    assert result.exit_code == 0
    assert "status" in result.output
    assert "inspect" in result.output
    assert "plan" in result.output
    assert "cancel" in result.output
    assert "rollback" in result.output


def test_deploy_no_subcommand_shows_help() -> None:
    result = runner.invoke(app, ["deploy"])
    assert result.exit_code == 0
    assert "deploy" in result.output.lower()


pytestmark = pytest.mark.integration


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


async def _seed_deploy_project(tmp_path: Path) -> UUID:
    async with build_app() as resources:
        project = await resources.projects.create(
            "deploy-cli-proj",
            tmp_path,
            max_cycles=5,
            config={
                "project": {"name": "deploy-cli-proj"},
                "deployment": {
                    "provider": "azure",
                    "target": "container_app",
                    "environment": "dev",
                    "resource_group": "rg-test",
                    "region": "eastus",
                },
            },
        )
        # Advance project to DEPLOY_EXECUTE
        await resources.projects.transition(
            project.project_id, expected=Phase.INTAKE, to=Phase.DEPLOY_DESIGN
        )
        await resources.projects.transition(
            project.project_id, expected=Phase.DEPLOY_DESIGN, to=Phase.DEPLOY_EXECUTE
        )

        # Record deployment spec and artifact in ledger
        target = AzureTargetScope("tenant-1", "sub-1", "rg-test", "dev", "eastus")
        identity = IdentityAuthority("workload_identity", "id-1", ("Contributor",))
        topology = TopologyConfig("container_app", "bicep", "Standard_B1s")
        recovery = RecoveryPolicy("revision", True)
        verification = VerificationContract("/health", ("curl /health",), 30)
        cost = CostBoundary(100.0, 10.0)
        spec = DeploymentSpec(
            "spec-cli",
            "1.0",
            target,
            identity,
            topology,
            recovery,
            verification,
            cost,
        )

        payload_spec = {
            "decision": "deployment_spec_accepted",
            "spec_id": spec.spec_id,
            "scope_digest": spec.scope_digest(),
            "monthly_budget": spec.cost_boundary.max_monthly_budget_usd,
        }
        await resources.ledger.append(
            LedgerEventDraft(
                project_id=project.project_id,
                cycle=project.cycle,
                phase=Phase.DEPLOY_DESIGN,
                kind=EventKind.DECISION_RECORDED,
                engine_id=None,
                job_id=None,
                causation_id=None,
                correlation_id=project.project_id,
                provenance=Provenance.TRUSTED,
                produced_at=datetime.now(UTC),
                payload=payload_spec,
                digest=digest_event(payload_spec),
            )
        )

        payload_dep = {
            "artifact_type": "deployment_verification",
            "deployment_id": "dep-cli-123",
            "outputs": {"endpoint": "https://deploy-cli-proj.azurecontainerapps.io"},
        }
        await resources.ledger.append(
            LedgerEventDraft(
                project_id=project.project_id,
                cycle=project.cycle,
                phase=Phase.DEPLOY_EXECUTE,
                kind=EventKind.ARTIFACT_PRODUCED,
                engine_id=None,
                job_id=None,
                causation_id=None,
                correlation_id=project.project_id,
                provenance=Provenance.TRUSTED,
                produced_at=datetime.now(UTC),
                payload=payload_dep,
                digest=digest_event(payload_dep),
            )
        )

        return project.project_id


def test_deploy_status_cli(tmp_path: Path) -> None:
    proj_id = asyncio.run(_seed_deploy_project(tmp_path))
    res = runner.invoke(app, ["deploy", "status", str(proj_id)])
    assert res.exit_code == 0
    assert "DEPLOY_EXECUTE" in res.output
    assert "https://deploy-cli-proj.azurecontainerapps.io" in res.output


def test_deploy_inspect_cli(tmp_path: Path) -> None:
    proj_id = asyncio.run(_seed_deploy_project(tmp_path))
    res = runner.invoke(app, ["deploy", "inspect", str(proj_id)])
    assert res.exit_code == 0
    assert "spec_id" in res.output or "scope_digest" in res.output


def test_deploy_plan_cli(tmp_path: Path) -> None:
    proj_id = asyncio.run(_seed_deploy_project(tmp_path))
    res = runner.invoke(app, ["deploy", "plan", str(proj_id)])
    assert res.exit_code == 0
    assert "Plan Evaluation" in res.output or "safe" in res.output.lower()


def test_deploy_cancel_cli(tmp_path: Path) -> None:
    proj_id = asyncio.run(_seed_deploy_project(tmp_path))
    res = runner.invoke(app, ["deploy", "cancel", str(proj_id)])
    assert res.exit_code == 0
    assert "cancelled" in res.output.lower() or "aborted" in res.output.lower()


def test_deploy_rollback_cli(tmp_path: Path) -> None:
    proj_id = asyncio.run(_seed_deploy_project(tmp_path))
    res = runner.invoke(app, ["deploy", "rollback", str(proj_id)])
    assert res.exit_code == 0
    assert "rollback" in res.output.lower()
