# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""AzCliClientAdapter and the ARM renderer: the real Azure path, faked at
the subprocess boundary. Live execution requires `az login` and a real
subscription; everything up to that boundary is verified here."""

import json
from datetime import UTC, datetime

import pytest

from vibey.domain.deployment import (
    AzureTargetScope,
    CostBoundary,
    DeploymentConsent,
    DeploymentSpec,
    IdentityAuthority,
    RecoveryPolicy,
    TopologyConfig,
    VerificationContract,
)
from vibey.infrastructure.azure.arm import DEFAULT_IMAGE, UnsupportedTopology, render_template
from vibey.infrastructure.azure.az_cli import (
    AzCliClientAdapter,
    AzCliError,
    MutationNotAuthorized,
)
from vibey.infrastructure.engines.claudeloop_process import CommandResult

NOW = datetime(2026, 8, 19, tzinfo=UTC)


def _spec(*, service_type: str = "container_app", ingress: bool = True) -> DeploymentSpec:
    return DeploymentSpec(
        spec_id="spec-az-1",
        version="1.0.0",
        target_scope=AzureTargetScope(
            tenant_id="tenant-123",
            subscription_id="sub-456",
            resource_group="rg-vibey-dev",
            environment="dev",
            region="eastus",
            tags={"owner": "vibey"},
        ),
        identity=IdentityAuthority(
            identity_type="workload_identity_oidc",
            principal_id="principal-789",
            approved_roles=("Contributor",),
        ),
        topology=TopologyConfig(
            service_type=service_type,
            iac_provider="bicep",
            sku="Standard_B1s",
            instances=2,
            ingress_enabled=ingress,
            tls_enabled=True,
        ),
        recovery_policy=RecoveryPolicy(
            progressive_exposure="revision",
            auto_rollback_on_health_failure=True,
            max_rollback_attempts=2,
        ),
        verification=VerificationContract(
            health_endpoint="/health",
            smoke_tests=(),
            bake_window_seconds=60,
        ),
        cost_boundary=CostBoundary(
            max_monthly_budget_usd=100.0,
            max_deployment_cost_usd=10.0,
        ),
    )


def _consent(spec: DeploymentSpec, *, authorized: bool = True) -> DeploymentConsent:
    return DeploymentConsent(
        consent_id="consent-1",
        target_scope_digest=spec.scope_digest(),
        granted_by="operator",
        granted_at=NOW,
        explicit_mutation_authorized=authorized,
    )


class FakeExecutor:
    """Canned az responses keyed by subcommand prefix; records every argv."""

    def __init__(self, responses: dict[str, tuple[int, str, str]] | None = None) -> None:
        self.responses = responses or {}
        self.calls: list[tuple[str, ...]] = []

    async def execute(self, argv: tuple[str, ...]) -> CommandResult:
        self.calls.append(argv)
        key = " ".join(argv[1:3])
        returncode, stdout, stderr = self.responses.get(key, (0, "{}", ""))
        return CommandResult(returncode=returncode, stdout=stdout, stderr=stderr)


# ── the ARM renderer ─────────────────────────────────────────────────────────


def test_render_template_shapes_a_container_app_from_the_spec() -> None:
    template = render_template(_spec())

    env, app = template["resources"]
    assert env["type"] == "Microsoft.App/managedEnvironments"
    assert app["type"] == "Microsoft.App/containerApps"
    assert env["location"] == app["location"] == "eastus"
    assert app["tags"] == {"owner": "vibey"}
    assert app["properties"]["template"]["scale"]["minReplicas"] == 2
    ingress = app["properties"]["configuration"]["ingress"]
    assert ingress["external"] is True
    assert ingress["allowInsecure"] is False  # tls_enabled
    assert template["parameters"]["image"]["defaultValue"] == DEFAULT_IMAGE


def test_render_template_without_ingress_and_with_custom_image() -> None:
    template = render_template(_spec(ingress=False), image="example.azurecr.io/app:1")

    _, app = template["resources"]
    assert app["properties"]["configuration"]["ingress"] is None
    assert template["parameters"]["image"]["defaultValue"] == "example.azurecr.io/app:1"


def test_render_template_refuses_unknown_topologies() -> None:
    with pytest.raises(UnsupportedTopology):
        render_template(_spec(service_type="kubernetes_fleet"))


# ── the adapter ──────────────────────────────────────────────────────────────


async def test_discovery_reads_account_and_resources() -> None:
    executor = FakeExecutor(
        {
            "account show": (0, json.dumps({"tenantId": "tenant-real"}), ""),
            "resource list": (0, json.dumps([{"id": "res-1"}]), ""),
        }
    )
    adapter = AzCliClientAdapter(executor=executor)

    result = await adapter.discover_environment(_spec().target_scope)

    assert result.tenant_id == "tenant-real"
    assert result.existing_resources == ({"id": "res-1"},)
    assert all(argv[0] == "az" and argv[-2:] == ("-o", "json") for argv in executor.calls)


async def test_discovery_treats_a_missing_resource_group_as_empty() -> None:
    executor = FakeExecutor(
        {
            "account show": (0, "{}", ""),
            "resource list": (1, "", "ResourceGroupNotFound"),
        }
    )
    adapter = AzCliClientAdapter(executor=executor)

    result = await adapter.discover_environment(_spec().target_scope)

    assert result.existing_resources == ()


async def test_execute_plan_deploys_the_rendered_template_with_consent() -> None:
    spec = _spec()
    deployment = {
        "id": "/subscriptions/sub-456/deployments/vibey-spec-az-1",
        "properties": {"provisioningState": "Succeeded", "outputs": {"appName": {"value": "x"}}},
    }
    executor = FakeExecutor(
        {
            "group create": (0, "{}", ""),
            "deployment group": (0, json.dumps(deployment), ""),
        }
    )
    adapter = AzCliClientAdapter(executor=executor)

    result = await adapter.execute_plan(spec, _consent(spec))

    assert result.provisioning_state == "Succeeded"
    assert result.deployment_id.endswith("vibey-spec-az-1")
    deploy_argv = next(a for a in executor.calls if a[1] == "deployment")
    assert "--template-file" in deploy_argv
    assert "--subscription" in deploy_argv


async def test_mutations_are_refused_without_digest_bound_consent() -> None:
    spec = _spec()
    executor = FakeExecutor()
    adapter = AzCliClientAdapter(executor=executor)

    stale = DeploymentConsent(
        consent_id="c",
        target_scope_digest="a-different-digest",
        granted_by="operator",
        granted_at=NOW,
        explicit_mutation_authorized=True,
    )
    with pytest.raises(MutationNotAuthorized):
        await adapter.execute_plan(spec, stale)

    unauthorized = _consent(spec, authorized=False)
    with pytest.raises(MutationNotAuthorized):
        await adapter.execute_plan(spec, unauthorized)

    with pytest.raises(MutationNotAuthorized):
        await adapter.delete_resource(spec.target_scope, "res-1", stale)

    # No az mutation ever ran.
    assert executor.calls == []


async def test_status_and_consented_delete() -> None:
    scope = _spec().target_scope
    executor = FakeExecutor(
        {
            "resource show": (
                0,
                json.dumps({"properties": {"provisioningState": "Succeeded"}}),
                "",
            ),
            "resource delete": (0, "", ""),
        }
    )
    adapter = AzCliClientAdapter(executor=executor)

    status = await adapter.get_resource_status(scope, "res-1")
    assert status.provisioning_state == "Succeeded"
    assert status.health_state == "Healthy"

    consent = DeploymentConsent(
        consent_id="c",
        target_scope_digest=scope.digest(),
        granted_by="operator",
        granted_at=NOW,
        explicit_mutation_authorized=True,
    )
    await adapter.delete_resource(scope, "res-1", consent)
    assert any(argv[1:3] == ("resource", "delete") for argv in executor.calls)


async def test_az_failures_surface_argv_and_stderr() -> None:
    executor = FakeExecutor({"account show": (1, "", "az: not logged in")})
    adapter = AzCliClientAdapter(executor=executor)

    with pytest.raises(AzCliError) as excinfo:
        await adapter.discover_environment(_spec().target_scope)

    assert "not logged in" in str(excinfo.value)
