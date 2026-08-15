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
    VisualProvider,
    build_app,
    build_design_worker,
    build_visual_worker,
)
from vibey.domain.job import idempotency_key
from vibey.domain.phase import Phase, VisualDecision
from vibey.domain.spec import (
    AcceptanceCriterion,
    Constraint,
    ConstraintKind,
    DesignSpec,
    NonFunctionalRequirement,
)
from vibey.infrastructure.engines.claudeloop_design import ClaudeLoopDesignProvider
from vibey.infrastructure.engines.claudeloop_process import (
    AsyncSubprocessExecutor,
    ClaudeLoopProcess,
)
from vibey.infrastructure.engines.scripted_design import ScriptedDesignProvider
from vibey.infrastructure.engines.scripted_visual import ScriptedVisualProvider

app = typer.Typer(name="vibey", no_args_is_help=True)
design_app = typer.Typer(name="design", invoke_without_command=True)
app.add_typer(design_app, name="design")
visual_app = typer.Typer(name="visual", invoke_without_command=True)
app.add_typer(visual_app, name="visual")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"vibey {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(False, "--version", callback=_version_callback, is_eager=True),
) -> None:
    """vibey: a queue-based, three-phase conductor for autonomous software delivery."""


async def _enqueue_design(project_id: UUID) -> str:
    async with build_app() as resources:
        project = await resources.projects.get(project_id)
        if project is None:
            raise ValueError(f"unknown project {project_id}")
        if project.phase is Phase.INTAKE:
            project = await resources.projects.transition(
                project_id, expected=Phase.INTAKE, to=Phase.DESIGN
            )
        if project.phase is not Phase.DESIGN:
            raise ValueError(f"project is in {project.phase.value}, not design")
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
    typer.echo(f"design job {asyncio.run(_enqueue_design(project_id))}")


def _parse_question_answers(items: tuple[str, ...]) -> dict[str, object]:
    answers: dict[str, str] = {}
    for item in items:
        question_id, separator, answer = item.partition("=")
        if not separator or not question_id.strip():
            raise ValueError("each answer must use QUESTION_ID=ANSWER")
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
            raise ValueError(f"unknown project {project_id}")
        owner = f"cli-{os.getpid()}"
        if project.phase is Phase.VISUAL_DESIGN:
            visual_provider: VisualProvider
            if provider == "scripted":
                visual_provider = ScriptedVisualProvider()
            else:
                raise ValueError(
                    "no live VisualProvider is implemented yet; use --provider scripted"
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
            raise ValueError("provider must be 'scripted' or 'claudeloop'")
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
                raise ValueError(f"unknown project {project_id}")
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
    phase = asyncio.run(_settle_visual(project_id, VisualDecision.ACCEPTED))
    typer.echo(f"accepted visual design for {project_id}; entered {phase.value}")


@visual_app.command("waive")
def waive_visual(project_id: UUID) -> None:
    """Explicitly waive the visual plan (inventory must still be complete) and enter BUILD."""
    phase = asyncio.run(_settle_visual(project_id, VisualDecision.WAIVED))
    typer.echo(f"waived visual design for {project_id}; entered {phase.value}")


if __name__ == "__main__":
    app()
