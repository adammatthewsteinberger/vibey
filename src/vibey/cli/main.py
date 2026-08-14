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
from vibey.bootstrap import DesignProvider, build_app, build_design_worker
from vibey.domain.job import idempotency_key
from vibey.domain.phase import Phase
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

app = typer.Typer(name="vibey", no_args_is_help=True)
design_app = typer.Typer(name="design", invoke_without_command=True)
app.add_typer(design_app, name="design")


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


@design_app.callback()
def design(project_id: Annotated[UUID | None, typer.Argument()] = None) -> None:
    """Enqueue or resume the project's DESIGN interview."""
    if project_id is not None:
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
            owner=f"cli-{os.getpid()}",
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
) -> None:
    """Accept the synthesized spec, optionally importing JSON first, and enter BUILD."""

    async def accept() -> Path:
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
            ).accept(project_id)
            return accepted.repo_path

    repo_path = asyncio.run(accept())
    typer.echo(f"accepted design for {project_id}; context written under {repo_path}")


if __name__ == "__main__":
    app()
