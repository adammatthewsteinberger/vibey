# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Annotated

import typer

from agyloop import bootstrap
from agyloop.application.usecases.doctor import all_passed, run_doctor
from agyloop.cli.render import render_classification, render_doctor_checks
from agyloop.domain.classify import TurnSignals, classify_explained

app = typer.Typer(add_completion=False)


@app.callback(invoke_without_command=True)
def doctor(ctx: typer.Context) -> None:
    """Pre-flight checks: resolve GOOGLE_API_KEY or ADC auth lane and source.

    Reports the effective Gemini lane without guessing. Asserts no interactive
    hooks. Does not read live quota — check AI Studio for that.
    """
    if ctx.invoked_subcommand is not None:
        return
    env = bootstrap.build_doctor_environment()
    checks = run_doctor(env, cwd=Path.cwd())
    typer.echo(render_doctor_checks(checks))
    if not all_passed(checks):
        raise typer.Exit(code=1)


@app.command("repair-harness")
def repair_harness() -> None:
    """Restore a bundled localharness backup created by agyloop's site-packages patch."""
    typer.echo(bootstrap.repair_harness())


@app.command("explain-classify")
def explain_classify(
    message: Annotated[
        str,
        typer.Option("--message", help="Error / exception message to classify."),
    ] = "",
    http_status: Annotated[
        int | None, typer.Option("--http-status", help="HTTP status if known.")
    ] = None,
    status: Annotated[
        str | None, typer.Option("--status", help="Google RPC status (RESOURCE_EXHAUSTED, …).")
    ] = None,
    quota_metric: Annotated[
        str | None, typer.Option("--quota-metric", help="quotaMetric / quotaId token.")
    ] = None,
    error_code: Annotated[
        str | None, typer.Option("--error-code", help="rate_limit_exceeded or quota_exceeded.")
    ] = None,
    retry_after: Annotated[
        float | None, typer.Option("--retry-after", help="RetryInfo.retryDelay seconds.")
    ] = None,
    exception_type: Annotated[
        str | None, typer.Option("--exception-type", help="Python exception class name.")
    ] = None,
) -> None:
    """Run the capacity classifier and print which ladder rung fired."""
    signals = TurnSignals(
        http_status=http_status,
        status=status,
        message=message or None,
        quota_metric=quota_metric,
        error_code=error_code,
        retry_info_delay=timedelta(seconds=retry_after) if retry_after is not None else None,
        exception_type=exception_type,
    )
    result = classify_explained(signals)
    typer.echo(render_classification(result))
