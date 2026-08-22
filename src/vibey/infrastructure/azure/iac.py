# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""IaC static checks, preflight verification, and ARM what-if evaluation.

Milestone 10 task 10.5.
"""

from collections.abc import Mapping, Sequence
from typing import Any

from vibey.domain.deployment import (
    ChangeAction,
    CostBoundary,
    NormalizedResourceChange,
    PlanEvaluation,
    evaluate_iac_plan,
)


class IacValidator:
    """Validator for Bicep and Terraform IaC definitions and ARM what-if changesets."""

    def validate_syntax(self, provider: str, content: str) -> bool:
        prov = provider.lower().strip()
        if prov == "bicep":
            return self._validate_bicep(content)
        if prov in ("terraform", "tf"):
            return self._validate_terraform(content)
        return False

    def _validate_bicep(self, content: str) -> bool:
        # Balanced braces check and minimal syntax heuristics
        if content.count("{") != content.count("}"):
            return False
        if content.count("(") != content.count(")"):
            return False
        return "resource" in content or "param" in content or "module" in content

    def _validate_terraform(self, content: str) -> bool:
        if content.count("{") != content.count("}"):
            return False
        return "resource" in content or "variable" in content or "terraform" in content

    def normalize_arm_what_if(
        self, what_if_json: Mapping[str, Any]
    ) -> Sequence[NormalizedResourceChange]:
        changes: list[NormalizedResourceChange] = []
        raw_changes = what_if_json.get("changes", [])

        action_map: Mapping[str, ChangeAction] = {
            "create": ChangeAction.CREATE,
            "delete": ChangeAction.DELETE,
            "modify": ChangeAction.MODIFY,
            "nochange": ChangeAction.NO_CHANGE,
            "ignore": ChangeAction.NO_CHANGE,
            "deploy": ChangeAction.CREATE,
        }

        for change in raw_changes:
            resource_id = str(change.get("resourceId", ""))
            change_type = str(change.get("changeType", "create")).lower()
            action = action_map.get(change_type, ChangeAction.MODIFY)

            # Extract resource type from resourceId or change payload
            parts = resource_id.split("/providers/")
            if len(parts) > 1:
                resource_type = parts[1].split("/")[0]
            else:
                resource_type = "Microsoft.Resources/resourceGroups"

            changes.append(
                NormalizedResourceChange(
                    resource_id=resource_id,
                    resource_type=resource_type,
                    action=action,
                    estimated_monthly_cost_usd=0.0,
                    details=dict(change),
                )
            )

        return tuple(changes)

    def evaluate_plan(
        self, changes: Sequence[NormalizedResourceChange], cost_boundary: CostBoundary
    ) -> PlanEvaluation:
        return evaluate_iac_plan(changes, cost_boundary)
