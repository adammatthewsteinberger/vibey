"""Renders a DeploymentSpec into a minimal ARM template.

vibey's IaC module (iac.py) validates plans; nothing generated them, so
the real az adapter would have had nothing to execute. This renderer
covers the deploy interview's default topology (service_type
"container_app") with a managed environment plus a container app, sized
and exposed from the spec. The container image is a parameter with a
public hello-world default because the DeploymentSpec deliberately
carries no image -- what to run comes from the project, what to run it ON
comes from the spec.

Unsupported service types raise instead of guessing: an autonomous deploy
must never improvise infrastructure shape.
"""

from typing import Any

from vibey.domain.deployment import DeploymentSpec

DEFAULT_IMAGE = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"

_SUPPORTED = ("container_app",)


class UnsupportedTopology(ValueError):
    def __init__(self, service_type: str) -> None:
        super().__init__(
            f"service_type {service_type!r} has no ARM rendering; supported: {_SUPPORTED}"
        )


def render_template(spec: DeploymentSpec, *, image: str = DEFAULT_IMAGE) -> dict[str, Any]:
    if spec.topology.service_type not in _SUPPORTED:
        raise UnsupportedTopology(spec.topology.service_type)

    scope = spec.target_scope
    app_name = f"vibey-{spec.spec_id[:20].lower().replace('_', '-')}"
    env_name = f"{app_name}-env"
    tags = dict(scope.tags)

    ingress: dict[str, Any] | None = None
    if spec.topology.ingress_enabled:
        ingress = {
            "external": True,
            "targetPort": 80,
            "transport": "auto",
            "allowInsecure": not spec.topology.tls_enabled,
        }

    return {
        "$schema": (
            "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#"
        ),
        "contentVersion": "1.0.0.0",
        "parameters": {
            "image": {"type": "string", "defaultValue": image},
        },
        "resources": [
            {
                "type": "Microsoft.App/managedEnvironments",
                "apiVersion": "2023-05-01",
                "name": env_name,
                "location": scope.region,
                "tags": tags,
                "properties": {},
            },
            {
                "type": "Microsoft.App/containerApps",
                "apiVersion": "2023-05-01",
                "name": app_name,
                "location": scope.region,
                "tags": tags,
                "dependsOn": [f"[resourceId('Microsoft.App/managedEnvironments', '{env_name}')]"],
                "properties": {
                    "managedEnvironmentId": (
                        f"[resourceId('Microsoft.App/managedEnvironments', '{env_name}')]"
                    ),
                    "configuration": {"ingress": ingress},
                    "template": {
                        "containers": [{"name": app_name, "image": "[parameters('image')]"}],
                        "scale": {
                            "minReplicas": spec.topology.instances,
                            "maxReplicas": max(spec.topology.instances, 1),
                        },
                    },
                },
            },
        ],
        "outputs": {
            "appName": {"type": "string", "value": app_name},
        },
    }
