# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from vibey.domain.deployment import ChangeAction, CostBoundary
from vibey.infrastructure.azure.iac import IacValidator


def test_bicep_static_syntax_validation() -> None:
    validator = IacValidator()
    valid_bicep = """
    param location string = 'eastus'
    resource app 'Microsoft.App/containerApps@2023-05-01' = {
      name: 'myapp'
      location: location
    }
    """
    assert validator.validate_syntax("bicep", valid_bicep) is True

    invalid_bicep = "param location string = { broken bicep"
    assert validator.validate_syntax("bicep", invalid_bicep) is False

    invalid_bicep_paren = "param location string = ( broken bicep"
    assert validator.validate_syntax("bicep", invalid_bicep_paren) is False


def test_terraform_static_syntax_validation() -> None:
    validator = IacValidator()
    valid_tf = """
    resource "azurerm_resource_group" "rg" {
      name     = "rg-app"
      location = "East US"
    }
    """
    assert validator.validate_syntax("terraform", valid_tf) is True

    invalid_tf = 'resource "azurerm_resource_group" { broken'
    assert validator.validate_syntax("terraform", invalid_tf) is False


def test_normalize_arm_what_if_response() -> None:
    validator = IacValidator()
    what_if_raw = {
        "status": "Succeeded",
        "changes": [
            {
                "resourceId": (
                    "/subscriptions/sub-1/resourceGroups/rg-1"
                    "/providers/Microsoft.App/containerApps/app-1"
                ),
                "changeType": "Create",
            },
            {
                "resourceId": (
                    "/subscriptions/sub-1/resourceGroups/rg-1"
                    "/providers/Microsoft.Storage/storageAccounts/sa1"
                ),
                "changeType": "Delete",
            },
            {
                "resourceId": (
                    "/subscriptions/sub-1/resourceGroups/rg-1"
                    "/providers/Microsoft.Insights/components/ai1"
                ),
                "changeType": "Modify",
            },
            {
                "resourceId": (
                    "/subscriptions/sub-1/resourceGroups/rg-1/providers/Microsoft.Network/vnet/v1"
                ),
                "changeType": "NoChange",
            },
            {
                "resourceId": "/subscriptions/sub-1/resourceGroups/rg-1",
                "changeType": "Create",
            },
        ],
    }

    changes = validator.normalize_arm_what_if(what_if_raw)
    assert len(changes) == 5
    assert changes[4].resource_type == "Microsoft.Resources/resourceGroups"

    assert changes[0].action == ChangeAction.CREATE
    assert changes[1].action == ChangeAction.DELETE
    assert changes[2].action == ChangeAction.MODIFY
    assert changes[3].action == ChangeAction.NO_CHANGE

    cost_boundary = CostBoundary(max_monthly_budget_usd=100.0, max_deployment_cost_usd=10.0)
    evaluation = validator.evaluate_plan(changes, cost_boundary)
    assert evaluation.is_safe_for_automated_apply is False
    assert evaluation.has_destructive_deletions is True


def test_unsupported_iac_provider() -> None:
    validator = IacValidator()
    assert validator.validate_syntax("pulumi", "...") is False
