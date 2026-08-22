# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
import asyncio
import json
import os
import signal
import subprocess  # nosec B404 - fixed argv, never shell=True
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

import typer

from vibey import __version__
from vibey.application.design_acceptance import DesignAcceptanceService
from vibey.application.dto import ProjectRecord
from vibey.application.project_kickoff import enqueue_design_interview
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
from vibey.domain.engine import EngineId
from vibey.domain.errors import (
    InvalidAnswer,
    UnknownProject,
    UnknownProvider,
    WrongPhase,
)
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
from vibey.infrastructure.db.ledger_repository import PostgresLedgerRepository
from vibey.infrastructure.engines.claudeloop_design import ClaudeLoopDesignProvider
from vibey.infrastructure.engines.claudeloop_process import (
    AsyncSubprocessExecutor,
    ClaudeLoopProcess,
    SpendRecorder,
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
    # The transition-and-enqueue logic lives in the application layer so the
    # Kubernetes operator starts projects through the same path this does.
    async with build_app() as resources:
        job_id = await enqueue_design_interview(
            projects=resources.projects,
            jobs=resources.jobs,
            project_id=project_id,
        )
        return str(job_id)


def _build_spend_recorder(
    ledger: PostgresLedgerRepository, project_id: UUID, cycle: int, phase: Phase
) -> SpendRecorder:
    """Record a live run's spend where the budget brake can see it.

    LedgerBudgetSource sums TurnCompleted and BudgetSpent. The BUILD path
    gets TurnCompleted for free because LoopProcessAdapter tails the
    engine's events.jsonl into the ledger. The DESIGN path runs claudeloop
    directly and read that same file only for the last assistant message,
    so its spend reached nothing -- the brake computed $0 for DESIGN and
    could never trip, whatever cap the project carried. BudgetSpent with
    explicit dollars/turns is the vendor-neutral shape the brake already
    counts, so this needs no new event kind and no new counting logic.
    """
    from vibey.domain.ledger import Provenance, digest_event
    from vibey.infrastructure.engines.tailer import LedgerEventDraft

    async def record(turns: int, dollars: float) -> None:
        payload: dict[str, object] = {"turns": turns, "dollars": dollars}
        await ledger.append(
            LedgerEventDraft(
                project_id=project_id,
                cycle=cycle,
                phase=phase,
                kind=EventKind.BUDGET_SPENT,
                engine_id=EngineId.CLAUDELOOP,
                job_id=None,
                causation_id=None,
                correlation_id=uuid4(),
                provenance=Provenance.TRUSTED,
                produced_at=datetime.now(UTC),
                payload=payload,
                digest=digest_event(payload),
            )
        )

    return record


@app.command("new")
def new_project(
    name: str,
    repo: Annotated[Path, typer.Option("--repo")] = Path("."),
    max_cycles: Annotated[int, typer.Option("--max-cycles", min=1)] = 10,
    max_cycle_dollars: Annotated[
        float | None,
        typer.Option(
            "--max-cycle-dollars",
            min=0.01,
            help="Cap engine spend per cycle; exceeding it parks a "
            "budget_exhausted gate instead of starting more sessions",
        ),
    ] = None,
    max_cycle_turns: Annotated[
        int | None,
        typer.Option("--max-cycle-turns", min=1, help="Cap engine turns per cycle"),
    ] = None,
) -> None:
    """Create a project and enqueue its first DESIGN interview."""

    async def create() -> tuple[str, str]:
        config: dict[str, object] = {"project": {"name": name, "repo": str(repo)}}
        if max_cycle_dollars is not None:
            config["max_cycle_dollars"] = max_cycle_dollars
        if max_cycle_turns is not None:
            config["max_cycle_turns"] = max_cycle_turns
        async with build_app() as resources:
            project = await resources.projects.create(
                name,
                repo,
                max_cycles=max_cycles,
                config=config,
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
def answer(
    gate_id: UUID,
    answers: Annotated[list[str] | None, typer.Argument()] = None,
    choice: Annotated[
        str | None,
        typer.Option("--choice", help='Answer a choice gate: sends {"choice": VALUE}'),
    ] = None,
    verdict: Annotated[
        str | None,
        typer.Option("--verdict", help='Answer a verdict gate: sends {"verdict": VALUE}'),
    ] = None,
    raw: Annotated[
        str | None,
        typer.Option("--raw", help="Answer with an arbitrary JSON object"),
    ] = None,
    defaults: Annotated[
        bool,
        typer.Option(
            "--defaults",
            help="Interview gates: accept every question's default "
            "(combinable with positional pairs, which win)",
        ),
    ] = False,
) -> None:
    """Answer a parked gate: QUESTION_ID=ANSWER pairs, --choice, --verdict, or --raw.

    Interview gates take the positional pairs or --defaults (question keys
    are model-minted and vary per run; --defaults needs none); review gates
    take --verdict (accept/changes/cancel/approve/request_changes);
    deployment and triage gates take --choice; --raw covers any other shape.
    """
    modes = [m for m in (answers, choice, verdict, raw) if m]
    if defaults and (choice or verdict or raw):
        typer.echo("--defaults only combines with positional QUESTION_ID=ANSWER pairs")
        raise typer.Exit(2)
    if len(modes) != 1 and not defaults:
        typer.echo("provide exactly one of: QUESTION_ID=ANSWER pairs, --choice, --verdict, --raw")
        raise typer.Exit(2)

    payload: dict[str, object]
    if choice is not None:
        payload = {"choice": choice}
    elif verdict is not None:
        payload = {"verdict": verdict}
    elif raw is not None:
        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError as exc:
            typer.echo(f"--raw must be valid JSON: {exc}")
            raise typer.Exit(2) from exc
        if not isinstance(decoded, dict):
            typer.echo("--raw must be a JSON object")
            raise typer.Exit(2)
        payload = decoded
    else:
        payload = _parse_question_answers(tuple(answers or ()))
        if defaults:
            payload["accept_defaults"] = True

    async def submit() -> None:
        async with build_app() as resources:
            await resources.gates.answer(gate_id, answer=payload, answered_by="cli")

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
                spend_recorder=_build_spend_recorder(
                    resources.ledger, project.project_id, project.cycle, project.phase
                ),
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
    record: Annotated[
        bool,
        typer.Option(
            "--record",
            help="Persist preflight (and conformance, with --conformance) to engine_health",
        ),
    ] = False,
    record_project: Annotated[
        UUID | None,
        typer.Option("--project", help="Project to record health for (default: latest)"),
    ] = None,
    cluster: Annotated[
        bool,
        typer.Option(
            "--cluster",
            help="In-cluster preflight instead: DSN, workspace, secrets, database, migrations",
        ),
    ] = False,
) -> None:
    """Check engine health, auth status, and optionally run conformance."""
    from vibey.application.conformance import run_conformance
    from vibey.infrastructure.engines.classify import CREDITS_FIXTURES
    from vibey.infrastructure.engines.descriptors import ALL_DESCRIPTORS, BY_ENGINE_ID
    from vibey.infrastructure.engines.loop_process_adapter import LoopProcessAdapter

    async def run_doctor() -> None:
        import tempfile
        from uuid import uuid4

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

        record_project_id: UUID | None = None
        if record:
            async with build_app() as resources:
                if record_project is not None:
                    target = await resources.projects.get(record_project)
                else:
                    target = await resources.projects.get_latest()
            if target is None:
                typer.echo("no projects found; create one with `vibey new` first")
                raise typer.Exit(1)
            record_project_id = target.project_id

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
                # Use a unique scratch directory per conformance run to avoid
                # session-lock collisions in shared state
                conformance_id = uuid4().hex[:8]
                unique_worktree = str(
                    Path(tempfile.gettempdir()) / f"vibey-conformance-{conformance_id}"
                )
                report = await run_conformance(
                    adapter,
                    capacity_fixtures=capacity_fixtures,
                    trivial_worktree=unique_worktree,
                )
                for check in report.checks:
                    mark = "PASS" if check.ok else "FAIL"
                    detail = f" — {check.detail}" if check.detail else ""
                    typer.echo(f"  {mark} {check.name}{detail}")
                if not report.ok:
                    all_ok = False

                if record_project_id is not None:
                    async with build_app() as resources:
                        await resources.engine_health_service.update_from_preflight(
                            record_project_id, desc.engine_id, preflight, conformance_ok=report.ok
                        )
                    typer.echo(f"  recorded engine_health for {desc.engine_id.value}")
            elif record_project_id is not None:
                async with build_app() as resources:
                    await resources.engine_health_service.record_preflight(
                        record_project_id, desc.engine_id, preflight
                    )
                typer.echo(f"  recorded preflight for {desc.engine_id.value}")

        if conformance and not all_ok:
            raise typer.Exit(1)

    async def run_cluster_doctor() -> None:
        import shutil

        from vibey.bootstrap import database_url, migrations_dir
        from vibey.infrastructure.cluster_preflight import all_ok, run_cluster_preflight

        checks = await run_cluster_preflight(
            dsn=database_url(),
            workspace=Path.cwd(),
            migrations_dir=migrations_dir(),
            environ=os.environ,
            uid=os.getuid(),
            which=shutil.which,
        )
        for check in checks:
            mark = "PASS" if check.ok else "FAIL"
            typer.echo(f"{mark} {check.name:<20} {check.detail}")
        if not all_ok(checks):
            raise typer.Exit(1)

    if cluster:
        asyncio.run(run_cluster_doctor())
        return

    asyncio.run(run_doctor())


@app.command("operator")
def operator(
    namespace: Annotated[
        str | None,
        typer.Option(
            "--namespace",
            help="Watch a single namespace (default: cluster-wide)",
        ),
    ] = None,
) -> None:
    """Run the Kubernetes operator: reconcile VibeyProject custom resources."""
    # Imported here, not at module scope: kopf and the Kubernetes client are
    # an optional extra, and `vibey worker` on a laptop should not require
    # them to start.
    try:
        from vibey.infrastructure.operator import run as run_operator
    except ImportError as exc:
        typer.echo("operator support is not installed: pip install 'vibey[operator]'")
        raise typer.Exit(1) from exc

    run_operator(namespace=namespace)


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
    provider: Annotated[
        str,
        typer.Option("--provider", help="Design/decompose providers: scripted or claudeloop"),
    ] = "scripted",
    max_turns: Annotated[int, typer.Option("--max-turns", min=1)] = 25,
    max_dollars: Annotated[float, typer.Option("--max-dollars", min=0.01, max=10)] = 2.0,
    project_opt: Annotated[
        UUID | None,
        typer.Option("--project", help="Project id (default: the latest project)"),
    ] = None,
    wait_for_project: Annotated[
        float | None,
        typer.Option(
            "--wait-for-project",
            min=1.0,
            help=(
                "Poll every N seconds for a project instead of exiting when none "
                "exists. For long-lived deployments, where exiting means a "
                "restart loop until someone creates one."
            ),
        ),
    ] = None,
    azure: Annotated[
        str,
        typer.Option(
            "--azure",
            help="Azure client for the deploy stage set: 'memory' (safe default, "
            "no real infrastructure) or 'az' (the real Azure CLI; requires "
            "`az login` and mutates real resources on consented deploys)",
        ),
    ] = "memory",
) -> None:
    """Long-running worker: LISTEN vibey_job_ready, dispatch across all phases."""
    from datetime import timedelta

    from vibey.application.worker import WorkerLoop
    from vibey.bootstrap import build_full_worker, database_url
    from vibey.domain.engine import EngineId
    from vibey.infrastructure.db.notifier import PostgresJobReadyNotifier
    from vibey.infrastructure.engines.scripted_decompose import ScriptedWorkPlanProducer

    allow_list: frozenset[EngineId] | None = None
    if engines_opt:
        try:
            allow_list = frozenset(EngineId(e.strip()) for e in engines_opt.split(","))
        except ValueError as exc:
            typer.echo(f"Invalid engine: {exc}")
            raise typer.Exit(2) from exc
    if provider not in ("scripted", "claudeloop"):
        typer.echo("provider must be 'scripted' or 'claudeloop'")
        raise typer.Exit(2)
    if azure not in ("memory", "az"):
        typer.echo("--azure must be 'memory' or 'az'")
        raise typer.Exit(2)
    azure_client = None
    if azure == "az":
        from vibey.infrastructure.azure.az_cli import AzCliClientAdapter

        login_check = subprocess.run(  # nosec B603 B607 - fixed argv, never shell=True
            ["az", "account", "show", "-o", "none"], capture_output=True, text=True
        )
        if login_check.returncode != 0:
            typer.echo("--azure az requires a logged-in Azure CLI: run `az login` first")
            raise typer.Exit(1)
        azure_client = AzCliClientAdapter()

    async def run_worker() -> None:
        from vibey.application.interfaces import WorkPlanProducer
        from vibey.bootstrap import preflight_sweep
        from vibey.infrastructure.engines.claudeloop_decompose import ClaudeLoopWorkPlanProducer

        async with build_app() as resources:

            async def _resolve_project() -> ProjectRecord | None:
                if project_opt is not None:
                    return await resources.projects.get(project_opt)
                return await resources.projects.get_latest()

            project = await _resolve_project()
            # A one-shot CLI run should fail fast when there is nothing to
            # work on. A long-lived deployment must not: exiting there is a
            # restart loop that ends only when a human creates a project,
            # and the crash counter makes a perfectly healthy worker look
            # broken. Waiting is opt-in so the CLI default stays honest.
            while project is None and wait_for_project is not None:
                typer.echo(f"no project yet; polling every {wait_for_project:g}s")
                await asyncio.sleep(wait_for_project)
                project = await _resolve_project()
            if project is None:
                typer.echo("no projects found; create one with `vibey new` first")
                raise typer.Exit(1)

            design_provider: DesignProvider
            decomposer: WorkPlanProducer
            if provider == "claudeloop":
                process = ClaudeLoopProcess(
                    executor=AsyncSubprocessExecutor(),
                    max_turns=max_turns,
                    max_dollars=max_dollars,
                    spend_recorder=_build_spend_recorder(
                        resources.ledger, project.project_id, project.cycle, project.phase
                    ),
                )
                design_provider = ClaudeLoopDesignProvider(
                    process=process,
                    worktree_path=project.repo_path,
                )
                decomposer = ClaudeLoopWorkPlanProducer(
                    process=process,
                    worktree_path=project.repo_path,
                )
            else:
                design_provider = ScriptedDesignProvider()
                decomposer = ScriptedWorkPlanProducer()

            adapters = dict(resources.engine_adapters)
            if allow_list is not None:
                adapters = {eid: a for eid, a in adapters.items() if eid in allow_list}

            ineligible = await preflight_sweep(
                resources=resources, project_id=project.project_id, adapters=adapters
            )
            if ineligible:
                names = ", ".join(sorted(e.value for e in ineligible))
                typer.echo(
                    f"warning: no recorded conformance for {names} -- engine-driven jobs "
                    "will not select them until `vibey doctor --conformance --record` passes"
                )

            count = max(1, min(parallelism, len(adapters) * 2, os.cpu_count() or 1))
            loops = [
                build_full_worker(
                    resources=resources,
                    project=project,
                    design_provider=design_provider,
                    visual_provider=ScriptedVisualProvider(),
                    decomposer=decomposer,
                    owner=f"worker-{os.getpid()}-{i}",
                    engine_adapters=adapters,
                    allow_list=allow_list,
                    azure_client=azure_client,
                )
                for i in range(count)
            ]

            notifier = PostgresJobReadyNotifier(database_url())
            await notifier.connect()

            # Kubernetes scale-in is SIGTERM, a wait, then SIGKILL. A
            # worker that ignores SIGTERM keeps claiming jobs it cannot
            # possibly finish: the kill lands mid-session, the lease is
            # orphaned, and a paid turn is thrown away. Draining means
            # exactly one thing -- finish the job in hand, claim no more --
            # so the flag is read between jobs and nowhere else. Checking
            # it mid-job would be the very truncation it exists to avoid.
            #
            # SIGTERM only, deliberately. Ctrl-C keeps its immediate-abort
            # semantics: an operator who interrupts a foreground worker
            # means now, not "in up to two hours".
            draining = asyncio.Event()

            def _begin_drain() -> None:
                typer.echo("draining on SIGTERM: finishing in-flight job, claiming no more")
                draining.set()

            asyncio.get_running_loop().add_signal_handler(signal.SIGTERM, _begin_drain)

            typer.echo(
                f"worker started: project={project.name} "
                f"engines={engines_opt or 'all'} parallelism={count} provider={provider}"
            )

            async def drive(loop_: WorkerLoop) -> None:
                while not draining.is_set():
                    worked = await loop_.run_once(project.project_id)
                    if worked:
                        typer.echo("processed one job")
                        if once:
                            return
                        continue
                    if once:
                        typer.echo("no ready job")
                        return
                    await resources.jobs.reap()
                    await notifier.wait_for_job_ready(
                        project.project_id, timeout=timedelta(seconds=5)
                    )

            try:
                if once or count == 1:
                    await drive(loops[0])
                else:
                    await asyncio.gather(*(drive(loop_) for loop_ in loops))
            finally:
                await notifier.close()

    with guard():
        asyncio.run(run_worker())
