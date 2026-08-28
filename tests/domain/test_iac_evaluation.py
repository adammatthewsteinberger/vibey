# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from vibey.domain.deployment import (
    ChangeAction,
    CostBoundary,
    NormalizedResourceChange,
    evaluate_iac_plan,
)


def test_safe_iac_plan_evaluation() -> None:
    changes = (
        NormalizedResourceChange(
            resource_id="/subscriptions/sub-1/resourceGroups/rg-1/providers/Microsoft.App/containerApps/app-1",
            resource_type="Microsoft.App/containerApps",
            action=ChangeAction.CREATE,
            estimated_monthly_cost_usd=25.0,
        ),
        NormalizedResourceChange(
            resource_id="/subscriptions/sub-1/resourceGroups/rg-1/providers/Microsoft.OperationalInsights/workspaces/law-1",
            resource_type="Microsoft.OperationalInsights/workspaces",
            action=ChangeAction.CREATE,
            estimated_monthly_cost_usd=5.0,
        ),
    )
    cost_boundary = CostBoundary(max_monthly_budget_usd=100.0, max_deployment_cost_usd=10.0)
    eval_result = evaluate_iac_plan(changes, cost_boundary)

    assert eval_result.is_safe_for_automated_apply is True
    assert eval_result.has_destructive_deletions is False
    assert eval_result.exceeds_budget is False
    assert eval_result.total_estimated_monthly_cost_usd == 30.0
    assert len(eval_result.blocking_reasons) == 0


def test_destructive_deletion_blocks_automated_apply() -> None:
    changes = (
        NormalizedResourceChange(
            resource_id="/subscriptions/sub-1/resourceGroups/rg-1/providers/Microsoft.Sql/servers/sql-1",
            resource_type="Microsoft.Sql/servers",
            action=ChangeAction.DELETE,
            estimated_monthly_cost_usd=0.0,
        ),
    )
    cost_boundary = CostBoundary(max_monthly_budget_usd=100.0, max_deployment_cost_usd=10.0)
    eval_result = evaluate_iac_plan(changes, cost_boundary)

    assert eval_result.is_safe_for_automated_apply is False
    assert eval_result.has_destructive_deletions is True
    assert any("deletion" in r.lower() for r in eval_result.blocking_reasons)


def test_cost_budget_overrun_blocks_automated_apply() -> None:
    changes = (
        NormalizedResourceChange(
            resource_id="/subscriptions/sub-1/resourceGroups/rg-1/providers/Microsoft.App/containerApps/app-1",
            resource_type="Microsoft.App/containerApps",
            action=ChangeAction.CREATE,
            estimated_monthly_cost_usd=250.0,
        ),
    )
    cost_boundary = CostBoundary(max_monthly_budget_usd=100.0, max_deployment_cost_usd=10.0)
    eval_result = evaluate_iac_plan(changes, cost_boundary)

    assert eval_result.is_safe_for_automated_apply is False
    assert eval_result.exceeds_budget is True
    assert any("budget" in r.lower() for r in eval_result.blocking_reasons)
