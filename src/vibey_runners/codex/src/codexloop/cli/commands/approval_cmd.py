# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""``codexloop approval`` — enqueue SetApproval."""

from __future__ import annotations

import typer

from codexloop.bootstrap import enqueue_run_control
from codexloop.domain.approval import ApprovalPolicy
from codexloop.domain.control import SetApproval
from codexloop.domain.errors import ConfigurationError


def approval_cmd(
    policy: str = typer.Argument(..., help="Approval policy."),
    run_id: str | None = typer.Option(None, "--run-id", help="Target run id."),
) -> None:
    """Queue an approval-policy change for the next control boundary."""
    try:
        value = ApprovalPolicy(policy)
        path = enqueue_run_control(SetApproval(policy=value), run_id=run_id)
    except (ConfigurationError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2) from exc
    typer.echo(f"queued → {path}")
