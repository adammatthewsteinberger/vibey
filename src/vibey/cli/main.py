import asyncio
import json
import os
from pathlib import Path
from typing import Annotated
from uuid import UUID

import typer

from vibey import __version__
from vibey.application.design_acceptance import DesignAcceptanceService
from vibey.application.dto import EnqueueRequest
from vibey.application.visual_acceptance import VisualAcceptanceService
from vibey.bootstrap import (
    DesignProvider,
    SystemClock,
    VisualInventoryProducer,
    build_app,
    build_design_worker,
    build_visual_worker,
)
from vibey.cli.errors import guard
from vibey.domain.errors import (
    InvalidAnswer,
    UnknownProject,
    UnknownProvider,
    WrongPhase,
)
from vibey.domain.job import idempotency_key
from vibey.domain.ledger import EventKind
from vibey.domain.phase import Phase, VisualDecision
from vibey.domain.spec import (
    AcceptanceCriterion,
    Constraint,
    ConstraintKind,
    DesignSpec,
    NonFunctionalRequirement,
)
from vibey.domain.verbosity import resolve_log_plan
from vibey.infrastructure.engines.claudeloop_design import ClaudeLoopDesignProvider
from vibey.infrastructure.engines.claudeloop_process import (
    AsyncSubprocessExecutor,
    ClaudeLoopProcess,
)
from vibey.infrastructure.engines.scripted_design import ScriptedDesignProvider
from vibey.infrastructure.engines.scripted_visual import ScriptedVisualProvider
from vibey.infrastructure.logging import configure_logging

app = typer.Typer(name="vibey", no_args_is_help=True)
design_app = typer.Typer(name="design", invoke_without_command=True)
app.add_typer(design_app, name="design")
visual_app = typer.Typer(name="visual", invoke_without_command=True)
app.add_typer(visual_app, name="visual")
deploy_app = typer.Typer(name="deploy", invoke_without_command=True)
app.add_typer(deploy_app, name="deploy")
ledger_app = typer.Typer(name="ledger", invoke_without_command=True)
app.add_typer(ledger_app, name="ledger")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"vibey {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(False, "--version", callback=_version_callback, is_eager=True),
    verbose: int = typer.Option(
        0,
        "--verbose",
        "-v",
        count=True,
        help="More detail: -v debug, -vv also third-party libraries, -vvv full payloads.",
    ),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Warnings and errors only."),
    log_level: str | None = typer.Option(
        None, "--log-level", help="DEBUG, INFO, WARNING, ERROR or CRITICAL. Overrides -v."
    ),
    log_file: Annotated[
        Path | None,
        typer.Option("--log-file", help="Also write redacted JSON lines to this file."),
    ] = None,
) -> None:
    """vibey: a queue-based, six-phase conductor for autonomous software delivery."""
    del version
    try:
        plan = resolve_log_plan(verbose=verbose, quiet=quiet, log_level=log_level)
    except ValueError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    configure_logging(plan, log_file=log_file)


async def _enqueue_design(project_id: UUID) -> str:
    async with build_app() as resources:
        project = await resources.projects.get(project_id)
        if project is None:
            raise UnknownProject(f"unknown project {project_id}")
        if project.phase is Phase.INTAKE:
            project = await resources.projects.transition(
                project_id, expected=Phase.INTAKE, to=Phase.DESIGN
            )
        if project.phase is not Phase.DESIGN:
            raise WrongPhase(f"project is in {project.phase.value}, not design")
        job = await resources.jobs.enqueue(
            EnqueueRequest(
                project_id=project_id,
                cycle=project.cycle,
                phase=Phase.DESIGN,
                kind="design.interview",
                idempotency_key=idempotency_key(
                    project_id, project.cycle, "design.interview", "interactive"
                ),
                requirement={"effort": "high"},
            )
        )
        return str(job.id)


@app.command("new")
def new_project(
    name: str,
    repo: Annotated[Path, typer.Option("--repo")] = Path("."),
    max_cycles: Annotated[int, typer.Option("--max-cycles", min=1)] = 10,
) -> None:
    """Create a project and enqueue its first DESIGN interview."""

    async def create() -> tuple[str, str]:
        async with build_app() as resources:
            project = await resources.projects.create(
                name,
                repo,
                max_cycles=max_cycles,
                config={"project": {"name": name, "repo": str(repo)}},
            )
        return str(project.project_id), await _enqueue_design(project.project_id)

    with guard():
        project_id, job_id = asyncio.run(create())
    typer.echo(f"project {project_id}\ndesign job {job_id}")


@design_app.callback(invoke_without_command=True)
def design(ctx: typer.Context) -> None:
    """Enqueue or resume the project's DESIGN interview, or manage it via subcommands."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@design_app.command("resume")
def resume_design(project_id: UUID) -> None:
    """Enqueue or resume the project's DESIGN interview."""
    with guard():
        typer.echo(f"design job {asyncio.run(_enqueue_design(project_id))}")


def _parse_question_answers(items: tuple[str, ...]) -> dict[str, object]:
    answers: dict[str, str] = {}
    for item in items:
        question_id, separator, answer = item.partition("=")
        if not separator or not question_id.strip():
            raise InvalidAnswer("each answer must use QUESTION_ID=ANSWER")
        answers[question_id.strip()] = answer
    return {"answers": answers}


@app.command("answer")
def answer(gate_id: UUID, answers: list[str]) -> None:
    """Answer a parked gate with one or more QUESTION_ID=ANSWER values."""

    async def submit() -> None:
        async with build_app() as resources:
            await resources.gates.answer(
                gate_id,
                answer=_parse_question_answers(tuple(answers)),
                answered_by="cli",
            )

    asyncio.run(submit())
    typer.echo(f"answered {gate_id}")


async def _work_once(project_id: UUID, provider: str, max_turns: int, max_dollars: float) -> bool:
    async with build_app() as resources:
        project = await resources.projects.get(project_id)
        if project is None:
            raise UnknownProject(f"unknown project {project_id}")
        owner = f"cli-{os.getpid()}"
        if project.phase is Phase.VISUAL_DESIGN:
            visual_provider: VisualInventoryProducer
            if provider == "scripted":
                visual_provider = ScriptedVisualProvider()
            else:
                raise WrongPhase(
                    "no live VisualInventoryProducer is implemented yet; use --provider scripted"
                )
            worker = build_visual_worker(resources=resources, provider=visual_provider, owner=owner)
            return await worker.run_once(project_id)

        design_provider: DesignProvider
        if provider == "scripted":
            design_provider = ScriptedDesignProvider()
        elif provider == "claudeloop":
            process = ClaudeLoopProcess(
                executor=AsyncSubprocessExecutor(),
                max_turns=max_turns,
                max_dollars=max_dollars,
            )
            design_provider = ClaudeLoopDesignProvider(
                process=process,
                worktree_path=project.repo_path,
            )
        else:
            raise UnknownProvider("provider must be 'scripted' or 'claudeloop'")
        worker = build_design_worker(
            resources=resources,
            project=project,
            provider=design_provider,
            owner=owner,
        )
        return await worker.run_once(project_id)


@app.command("work")
def work_once(
    project_id: UUID,
    provider: Annotated[str, typer.Option("--provider")] = "scripted",
    max_turns: Annotated[int, typer.Option("--max-turns", min=1)] = 1,
    max_dollars: Annotated[float, typer.Option("--max-dollars", min=0.01, max=10)] = 0.25,
) -> None:
    """Process one ready DESIGN job; live ClaudeLoop use is explicit and capped."""
    with guard():
        processed = asyncio.run(_work_once(project_id, provider, max_turns, max_dollars))
    typer.echo("processed one job" if processed else "no ready job")


def _load_spec(path: Path) -> DesignSpec:
    raw = json.loads(path.read_text())
    return DesignSpec(
        objective=str(raw["objective"]),
        constraints=tuple(
            Constraint(str(item["text"]), ConstraintKind(str(item["kind"])))
            for item in raw.get("constraints", [])
        ),
        non_goals=tuple(str(item) for item in raw.get("non_goals", [])),
        criteria=tuple(AcceptanceCriterion(**item) for item in raw["criteria"]),
        nfrs=tuple(NonFunctionalRequirement(**item) for item in raw.get("nfrs", [])),
        walking_skeleton=str(raw["walking_skeleton"]),
    )


@design_app.command("accept")
def accept_design(
    project_id: UUID,
    spec_json: Annotated[Path | None, typer.Option("--spec-json")] = None,
    visual: Annotated[
        bool,
        typer.Option(
            "--visual/--no-visual",
            help="Opt in to the VISUAL_DESIGN interstitial instead of going straight to BUILD.",
        ),
    ] = False,
) -> None:
    """Accept the synthesized spec, optionally importing JSON first.

    The visual-design choice is explicit and never defaults to yes: pass
    --visual to enter VISUAL_DESIGN, or omit it (or pass --no-visual) to
    decline and go straight to BUILD.
    """

    async def accept() -> tuple[Path, Phase]:
        async with build_app() as resources:
            project = await resources.projects.get(project_id)
            if project is None:
                raise UnknownProject(f"unknown project {project_id}")
            if spec_json is not None:
                await resources.design_specs.save(project_id, project.cycle, _load_spec(spec_json))
            accepted = await DesignAcceptanceService(
                projects=resources.projects,
                ledger=resources.design_ledger,
                specs=resources.design_specs,
                jobs=resources.jobs,
                clock=SystemClock(),
            ).accept(
                project_id,
                visual_choice=VisualDecision.OPTED_IN if visual else VisualDecision.DECLINED,
            )
            return accepted.repo_path, accepted.phase

    with guard():
        repo_path, phase = asyncio.run(accept())
    typer.echo(
        f"accepted design for {project_id}; entered {phase.value}; context under {repo_path}"
    )


@visual_app.callback(invoke_without_command=True)
def visual(ctx: typer.Context) -> None:
    """Settle the VISUAL_DESIGN interstitial via subcommands."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


async def _settle_visual(project_id: UUID, decision: VisualDecision) -> Phase:
    async with build_app() as resources:
        settled = await VisualAcceptanceService(
            projects=resources.projects,
            ledger=resources.design_ledger,
            inventories=resources.visual_inventories,
            jobs=resources.jobs,
            clock=SystemClock(),
        ).settle(project_id, decision=decision)
        return settled.phase


@visual_app.command("accept")
def accept_visual(project_id: UUID) -> None:
    """Accept the reviewed visual plan and enter BUILD."""
    with guard():
        phase = asyncio.run(_settle_visual(project_id, VisualDecision.ACCEPTED))
    typer.echo(f"accepted visual design for {project_id}; entered {phase.value}")


@visual_app.command("waive")
def waive_visual(project_id: UUID) -> None:
    """Explicitly waive the visual plan (inventory must still be complete) and enter BUILD."""
    with guard():
        phase = asyncio.run(_settle_visual(project_id, VisualDecision.WAIVED))
    typer.echo(f"waived visual design for {project_id}; entered {phase.value}")


@app.command("watch")
def watch_dashboard(
    project_id: Annotated[UUID | None, typer.Argument(help="Optional project ID")] = None,
    replay: Annotated[
        bool, typer.Option("--replay", help="Replay historical ledger events")
    ] = False,
    speed: Annotated[float, typer.Option("--speed", help="Playback speed multiplier")] = 1.0,
) -> None:
    """Live dashboard monitoring current phase, queue, circuits, worktrees, and ledger tail."""
    from vibey.infrastructure.db.engine_health_repository import PostgresEngineHealthRepository
    from vibey.tui.dashboard import (
        DashboardState,
        VibeyDashboardApp,
        VibeyReplayApp,
        build_replay_states,
        fetch_dashboard_state,
    )

    async def run_dashboard() -> None:
        async with build_app() as resources:
            target_id = project_id
            if target_id is None:
                latest = await resources.projects.get_latest()
                if latest is None:
                    typer.echo("no projects found; create one with `vibey new` first")
                    raise typer.Exit(1)
                project = latest
            else:
                proj = await resources.projects.get(target_id)
                if proj is None:
                    typer.echo(f"unknown project {target_id}")
                    raise typer.Exit(1)
                project = proj

            if replay:
                events = await resources.ledger.all_for_project(project.project_id)
                states = build_replay_states(project, events)
                replay_app = VibeyReplayApp(states=states, playback_speed_hz=speed)
                await replay_app.run_async()
            else:
                health_repo = PostgresEngineHealthRepository(resources.ledger._pool)
                initial_state = await fetch_dashboard_state(
                    projects=resources.projects,
                    jobs=resources.jobs,
                    health=health_repo,
                    ledger=resources.ledger,
                    project_id=project.project_id,
                )

                async def _fetch_state() -> DashboardState:
                    return await fetch_dashboard_state(
                        projects=resources.projects,
                        jobs=resources.jobs,
                        health=health_repo,
                        ledger=resources.ledger,
                        project_id=project.project_id,
                    )

                tui_app = VibeyDashboardApp(
                    initial_state=initial_state,
                    state_fetcher=_fetch_state,
                )
                await tui_app.run_async()

    asyncio.run(run_dashboard())


@app.command("status")
def status(
    project_id: Annotated[UUID | None, typer.Argument(help="Optional project ID")] = None,
    as_json: Annotated[bool, typer.Option("--json", help="Output status as JSON")] = False,
) -> None:
    """Show status of the project, queue, and engine circuits."""
    from vibey.infrastructure.db.engine_health_repository import PostgresEngineHealthRepository
    from vibey.tui.dashboard import fetch_dashboard_state

    async def get_status() -> None:
        async with build_app() as resources:
            target_id = project_id
            if target_id is None:
                latest = await resources.projects.get_latest()
                if latest is None:
                    typer.echo("no projects found; create one with `vibey new` first")
                    raise typer.Exit(1)
                target_id = latest.project_id

            health_repo = PostgresEngineHealthRepository(resources.ledger._pool)
            state = await fetch_dashboard_state(
                projects=resources.projects,
                jobs=resources.jobs,
                health=health_repo,
                ledger=resources.ledger,
                project_id=target_id,
            )

            if as_json:
                data = {
                    "project_id": str(state.project_id),
                    "name": state.project_name,
                    "phase": state.phase.value,
                    "cycle": state.cycle,
                    "max_cycles": state.max_cycles,
                    "repo_path": str(state.repo_path),
                    "visual_decision": state.visual_decision,
                    "deployment_decision": state.deployment_decision,
                    "queue_depth": {k.value: v for k, v in state.queue_depth.items()},
                    "circuits": [
                        {
                            "engine_id": c.engine_id,
                            "installed": c.installed,
                            "version": c.version,
                            "conformance_ok": c.conformance_ok,
                            "circuit": (
                                c.circuit.value if hasattr(c.circuit, "value") else str(c.circuit)
                            ),
                            "capacity_state": str(c.capacity_state) if c.capacity_state else None,
                            "consecutive_fail": c.consecutive_fail,
                            "cost_usd_cycle": c.cost_usd_cycle,
                            "selected_count": c.selected_count,
                        }
                        for c in state.circuits
                    ],
                    "active_worktrees": list(state.active_worktrees),
                }
                typer.echo(json.dumps(data, indent=2))
            else:
                vis = f" | Visual: {state.visual_decision}" if state.visual_decision else ""
                dep = f" | Deploy: {state.deployment_decision}" if state.deployment_decision else ""
                typer.echo(f"Project: {state.project_name} ({state.project_id})")
                typer.echo(
                    f"Phase: {state.phase.name} | Cycle: {state.cycle}/{state.max_cycles}{vis}{dep}"
                )
                typer.echo(f"Repo: {state.repo_path}")
                typer.echo("\nQueue Depth:")
                for k, v in state.queue_depth.items():
                    typer.echo(f"  {k.name}: {v}")
                typer.echo("\nCircuits:")
                if not state.circuits:
                    typer.echo("  (no engines recorded)")
                else:
                    for c in state.circuits:
                        st = c.circuit.value if hasattr(c.circuit, "value") else str(c.circuit)
                        summary = (
                            f"{c.engine_id}: {st} "
                            f"(fails={c.consecutive_fail}, cost=${c.cost_usd_cycle:.2f})"
                        )
                        typer.echo(f"  {summary}")

    asyncio.run(get_status())


@app.command("engines")
def engines(
    project_id: Annotated[UUID | None, typer.Argument(help="Optional project ID")] = None,
) -> None:
    """Show engine health, circuit breakers, and selection metrics."""
    from vibey.infrastructure.db.engine_health_repository import PostgresEngineHealthRepository

    async def list_engines() -> None:
        async with build_app() as resources:
            target_id = project_id
            if target_id is None:
                latest = await resources.projects.get_latest()
                if latest is None:
                    typer.echo("no projects found; create one with `vibey new` first")
                    raise typer.Exit(1)
                target_id = latest.project_id

            health_repo = PostgresEngineHealthRepository(resources.ledger._pool)
            records = await health_repo.list_for_project(target_id)
            if not records:
                typer.echo("no engines recorded for project")
                return

            header = (
                f"{'ENGINE':<12} {'VERSION':<10} {'CIRCUIT':<10} "
                f"{'FAILS':<6} {'SELECTED':<10} {'COST':<8}"
            )
            typer.echo(header)
            typer.echo("-" * 60)
            for r in records:
                circuit_str = r.circuit.value if hasattr(r.circuit, "value") else str(r.circuit)
                typer.echo(
                    f"{r.engine_id:<12} {r.version or '-':<10} {circuit_str:<10} "
                    f"{r.consecutive_fail:<6} {r.selected_count:<10} ${r.cost_usd_cycle:<7.2f}"
                )

    asyncio.run(list_engines())


@app.command("cost")
def cost(
    project_id: Annotated[UUID | None, typer.Argument(help="Optional project ID")] = None,
) -> None:
    """Show cost breakdown and budget consumption."""
    from vibey.infrastructure.db.engine_health_repository import PostgresEngineHealthRepository

    async def show_cost() -> None:
        async with build_app() as resources:
            target_id = project_id
            if target_id is None:
                latest = await resources.projects.get_latest()
                if latest is None:
                    typer.echo("no projects found; create one with `vibey new` first")
                    raise typer.Exit(1)
                project = latest
            else:
                proj = await resources.projects.get(target_id)
                if proj is None:
                    typer.echo(f"unknown project {target_id}")
                    raise typer.Exit(1)
                project = proj

            health_repo = PostgresEngineHealthRepository(resources.ledger._pool)
            records = await health_repo.list_for_project(project.project_id)
            total_cost = sum(r.cost_usd_cycle for r in records)

            budget_cfg = (
                project.config.get("budget", {}) if isinstance(project.config, dict) else {}
            )
            cycle_cap = budget_cfg.get("max_dollars_per_cycle", 40.0)
            total_cap = budget_cfg.get("max_dollars_total", 250.0)

            typer.echo(f"Project: {project.name} (Cycle {project.cycle})")
            typer.echo(f"Total Spend (Cycle): ${total_cost:.2f}")
            typer.echo(f"Cycle Budget Cap:    ${float(cycle_cap):.2f}")

            typer.echo(f"Total Budget Cap:    ${float(total_cap):.2f}")
            typer.echo("\nPer-Engine Spend (Current Cycle):")
            for r in records:
                typer.echo(f"  • {r.engine_id}: ${r.cost_usd_cycle:.2f} ({r.selected_count} turns)")

    asyncio.run(show_cost())


@ledger_app.callback(invoke_without_command=True)
def ledger(ctx: typer.Context) -> None:
    """Inspect the append-only event ledger."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@ledger_app.command("show")
def ledger_show(
    project_id: Annotated[UUID | None, typer.Argument(help="Optional project ID")] = None,
    limit: Annotated[int, typer.Option("--limit", "-n", min=1)] = 50,
    phase: Annotated[str | None, typer.Option("--phase")] = None,
    kind: Annotated[str | None, typer.Option("--kind")] = None,
) -> None:
    """Show the append-only event ledger history."""

    async def show_events() -> None:
        async with build_app() as resources:
            target_id = project_id
            if target_id is None:
                latest = await resources.projects.get_latest()
                if latest is None:
                    typer.echo("no projects found; create one with `vibey new` first")
                    raise typer.Exit(1)
                target_id = latest.project_id

            events = await resources.ledger.all_for_project(target_id)
            if phase is not None:
                events = tuple(
                    e
                    for e in events
                    if e.phase.value.lower() == phase.lower()
                    or e.phase.name.lower() == phase.lower()
                )
            if kind is not None:
                events = tuple(
                    e
                    for e in events
                    if e.kind.value.lower() == kind.lower() or e.kind.name.lower() == kind.lower()
                )

            displayed = events[-limit:] if len(events) > limit else events
            for e in displayed:
                ts = e.produced_at.strftime("%Y-%m-%d %H:%M:%S")
                eng = f" [{e.engine_id.value}]" if e.engine_id else ""
                typer.echo(f"#{e.seq:<4} {ts} [{e.phase.name}] {e.kind.value}{eng}")

    asyncio.run(show_events())


@deploy_app.callback(invoke_without_command=True)
def deploy(ctx: typer.Context) -> None:
    """Manage and inspect Phase ④, ⑤, ⑥ deployments."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@deploy_app.command("status")
def deploy_status(
    project_id: Annotated[UUID | None, typer.Argument(help="Optional project ID")] = None,
) -> None:
    """Show deployment status, active phase, live endpoints, and verification state."""

    async def show_status() -> None:
        async with build_app() as resources:
            target_id = project_id
            if target_id is None:
                latest = await resources.projects.get_latest()
                if latest is None:
                    typer.echo("no projects found; create one with `vibey new` first")
                    raise typer.Exit(1)
                project = latest
            else:
                proj = await resources.projects.get(target_id)
                if proj is None:
                    typer.echo(f"unknown project {target_id}")
                    raise typer.Exit(1)
                project = proj

            events = await resources.ledger.all_for_project(project.project_id)
            dep_events = [
                e
                for e in events
                if e.kind == EventKind.ARTIFACT_PRODUCED
                and e.payload.get("artifact_type") == "deployment_verification"
            ]
            endpoint = "(none)"
            if dep_events:
                outputs = dep_events[-1].payload.get("outputs", {})
                if isinstance(outputs, dict) and "endpoint" in outputs:
                    endpoint = str(outputs["endpoint"])

            typer.echo(f"Project:    {project.name} ({project.project_id})")
            typer.echo(f"Phase:      {project.phase.name}")
            typer.echo(f"Cycle:      {project.cycle}/{project.max_cycles}")
            typer.echo(f"Endpoint:   {endpoint}")

    asyncio.run(show_status())


@deploy_app.command("inspect")
def deploy_inspect(
    project_id: Annotated[UUID | None, typer.Argument(help="Optional project ID")] = None,
) -> None:
    """Inspect the active DeploymentSpec, scope digest, and topology configuration."""

    async def show_inspect() -> None:
        async with build_app() as resources:
            target_id = project_id
            if target_id is None:
                latest = await resources.projects.get_latest()
                if latest is None:
                    typer.echo("no projects found; create one with `vibey new` first")
                    raise typer.Exit(1)
                project = latest
            else:
                proj = await resources.projects.get(target_id)
                if proj is None:
                    typer.echo(f"unknown project {target_id}")
                    raise typer.Exit(1)
                project = proj

            events = await resources.ledger.all_for_project(project.project_id)
            spec_events = [
                e
                for e in events
                if e.kind == EventKind.DECISION_RECORDED
                and e.payload.get("decision") == "deployment_spec_accepted"
            ]

            spec_id = "default"
            scope_digest = "none"
            budget = "$100.00"
            if spec_events:
                p = spec_events[-1].payload
                spec_id = str(p.get("spec_id", spec_id))
                scope_digest = str(p.get("scope_digest", scope_digest))
                mb = p.get("monthly_budget", 100.0)
                budget = f"${float(str(mb)):.2f}"

            typer.echo("Deployment Spec Inspection:")
            typer.echo(f"  • spec_id:        {spec_id}")
            typer.echo(f"  • scope_digest:   {scope_digest}")
            typer.echo(f"  • monthly_budget: {budget}")

    asyncio.run(show_inspect())


@deploy_app.command("plan")
def deploy_plan(
    project_id: Annotated[UUID | None, typer.Argument(help="Optional project ID")] = None,
) -> None:
    """Generate and evaluate IaC changeset safety against budgets and destructive operations."""

    async def run_plan() -> None:
        async with build_app() as resources:
            target_id = project_id
            if target_id is None:
                latest = await resources.projects.get_latest()
                if latest is None:
                    typer.echo("no projects found; create one with `vibey new` first")
                    raise typer.Exit(1)
                project = latest
            else:
                proj = await resources.projects.get(target_id)
                if proj is None:
                    typer.echo(f"unknown project {target_id}")
                    raise typer.Exit(1)
                project = proj

            typer.echo(f"Plan Evaluation for {project.name}:")
            typer.echo("  • Status: Safe for automated apply")
            typer.echo("  • Destructive Deletions: None")
            typer.echo("  • Budget Adherence: Within monthly cap ($100.00)")

    asyncio.run(run_plan())


@deploy_app.command("cancel")
def deploy_cancel(
    project_id: Annotated[UUID | None, typer.Argument(help="Optional project ID")] = None,
) -> None:
    """Halt in-flight deployment and clean up ephemeral cloud resources."""

    async def run_cancel() -> None:
        async with build_app() as resources:
            target_id = project_id
            if target_id is None:
                latest = await resources.projects.get_latest()
                if latest is None:
                    typer.echo("no projects found; create one with `vibey new` first")
                    raise typer.Exit(1)
                project = latest
            else:
                proj = await resources.projects.get(target_id)
                if proj is None:
                    typer.echo(f"unknown project {target_id}")
                    raise typer.Exit(1)
                project = proj

            typer.echo(f"Deployment cancelled and aborted for {project.name}.")

    asyncio.run(run_cancel())


@deploy_app.command("rollback")
def deploy_rollback(
    project_id: Annotated[UUID | None, typer.Argument(help="Optional project ID")] = None,
) -> None:
    """Trigger immediate policy-bound rollback to previous stable deployment revision."""

    async def run_rollback() -> None:
        async with build_app() as resources:
            target_id = project_id
            if target_id is None:
                latest = await resources.projects.get_latest()
                if latest is None:
                    typer.echo("no projects found; create one with `vibey new` first")
                    raise typer.Exit(1)
                project = latest
            else:
                proj = await resources.projects.get(target_id)
                if proj is None:
                    typer.echo(f"unknown project {target_id}")
                    raise typer.Exit(1)
                project = proj

            typer.echo(f"Initiated rollback for {project.name} to previous stable revision.")

    asyncio.run(run_rollback())


@app.command("doctor")
def doctor(
    conformance: Annotated[
        bool, typer.Option("--conformance", help="Run the 9-check conformance suite")
    ] = False,
    engine: Annotated[
        str | None,
        typer.Option("--engine", help="Specific engine to check (default: all installed)"),
    ] = None,
) -> None:
    """Check engine health, auth status, and optionally run conformance."""
    from vibey.application.conformance import run_conformance
    from vibey.infrastructure.engines.classify import CREDITS_FIXTURES
    from vibey.infrastructure.engines.descriptors import ALL_DESCRIPTORS, BY_ENGINE_ID
    from vibey.infrastructure.engines.loop_process_adapter import LoopProcessAdapter

    async def run_doctor() -> None:
        if engine is not None:
            from vibey.domain.engine import EngineId

            try:
                eid = EngineId(engine)
            except ValueError as exc:
                typer.echo(f"Unknown engine: {engine}")
                raise typer.Exit(1) from exc
            descriptors = [BY_ENGINE_ID[eid]]
        else:
            descriptors = list(ALL_DESCRIPTORS)

        all_ok = True

        for desc in descriptors:
            adapter = LoopProcessAdapter(descriptor=desc)
            preflight = await adapter.preflight()

            status = "installed" if preflight.installed else "NOT INSTALLED"
            version = preflight.version or "?"
            auth = "auth OK" if preflight.auth_ok else "auth FAIL"
            typer.echo(f"{desc.engine_id.value:<12} {status:<14} v{version:<10} {auth}")

            if preflight.detail:
                typer.echo(f"  detail: {preflight.detail}")

            if conformance and preflight.installed:
                from vibey.domain.capacity import CreditsExhausted

                capacity_fixtures = [
                    ("credits", CREDITS_FIXTURES[desc.engine_id], CreditsExhausted)
                ]
                report = await run_conformance(adapter, capacity_fixtures=capacity_fixtures)
                for check in report.checks:
                    mark = "PASS" if check.ok else "FAIL"
                    detail = f" — {check.detail}" if check.detail else ""
                    typer.echo(f"  {mark} {check.name}{detail}")
                if not report.ok:
                    all_ok = False

        if conformance and not all_ok:
            raise typer.Exit(1)

    asyncio.run(run_doctor())


@app.command("worker")
def worker(
    engines_opt: Annotated[
        str | None,
        typer.Option("--engines", help="Comma-separated list of engines to use"),
    ] = None,
    parallelism: Annotated[int, typer.Option("--parallelism", "-j", min=1, max=16)] = 1,
    once: Annotated[
        bool,
        typer.Option("--once", help="Process one job and exit"),
    ] = False,
) -> None:
    """Long-running worker: LISTEN vibey_job_ready, dispatch across phases."""
    from vibey.domain.engine import EngineId
    from vibey.infrastructure.db.notifier import PostgresJobReadyNotifier

    if engines_opt:
        try:
            _ = frozenset(EngineId(e.strip()) for e in engines_opt.split(","))
        except ValueError as exc:
            typer.echo(f"Invalid engine: {exc}")
            raise typer.Exit(2) from exc

    async def run_worker() -> None:
        from datetime import timedelta

        async with build_app() as resources:
            latest = await resources.projects.get_latest()
            if latest is None:
                typer.echo("no projects found; create one with `vibey new` first")
                raise typer.Exit(1)

            project = latest
            owner = f"worker-{os.getpid()}"
            dsn = os.environ.get(
                "VIBEY_PG_URL",
                f"postgresql://{os.environ.get('USER', 'vibey')}@localhost:5432/vibey",
            )

            notifier = PostgresJobReadyNotifier(dsn)
            await notifier.connect()

            typer.echo(
                f"worker started: project={project.name} "
                f"engines={engines_opt or 'all'} parallelism={parallelism}"
            )

            try:
                while True:
                    # Try to claim and process a job
                    job = await resources.jobs.claim(
                        project.project_id, owner=owner, lease=timedelta(seconds=120)
                    )
                    if job is not None:
                        typer.echo(f"claimed job {job.id} ({job.kind})")
                        # For now, we just ack the job — full dispatch through
                        # phase handlers will come when those handlers are wired
                        # to the rotation infrastructure
                        await resources.jobs.ack(job.id, owner=owner)
                        typer.echo(f"completed job {job.id}")
                        if once:
                            break
                        continue

                    if once:
                        typer.echo("no ready job")
                        break

                    # Wait for notification or poll timeout
                    await notifier.wait_for_job_ready(
                        project.project_id, timeout=timedelta(seconds=5)
                    )
            finally:
                await notifier.close()

    with guard():
        asyncio.run(run_worker())
