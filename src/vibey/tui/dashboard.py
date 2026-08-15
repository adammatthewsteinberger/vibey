"""Live dashboard TUI implemented with Textual."""

from collections.abc import Callable, Mapping, Sequence
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar
from uuid import UUID

from textual.app import App, ComposeResult
from textual.binding import BindingType
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Header, Static

from vibey.application.dto import EngineHealthRecord
from vibey.application.ports import EngineHealthRepository, JobRepository
from vibey.domain.job import JobState
from vibey.domain.ledger import EventKind, LedgerEvent
from vibey.domain.phase import Phase
from vibey.infrastructure.db.ledger_repository import PostgresLedgerRepository
from vibey.infrastructure.db.project_repository import PostgresProjectRepository


@dataclass(frozen=True, slots=True)
class DashboardState:
    project_id: UUID
    project_name: str
    repo_path: Path
    phase: Phase
    cycle: int
    max_cycles: int
    visual_decision: str | None
    deployment_decision: str | None
    queue_depth: Mapping[JobState, int]
    circuits: tuple[EngineHealthRecord, ...]
    active_worktrees: tuple[str, ...]
    ledger_tail: tuple[LedgerEvent, ...]


def format_circuit_summary(circuits: Mapping[str, str] | Sequence[EngineHealthRecord]) -> str:
    lines: list[str] = []
    if isinstance(circuits, Mapping):
        for engine, state in sorted(circuits.items()):
            lines.append(f"  • {engine}: {state}")
    else:
        for record in circuits:
            state_str = (
                record.circuit.value if hasattr(record.circuit, "value") else str(record.circuit)
            )
            extra = f" (fails={record.consecutive_fail}, cost=${record.cost_usd_cycle:.2f})"
            lines.append(f"  • {record.engine_id}: {state_str}{extra}")
    return "\n".join(lines) if lines else "  (no engines recorded)"


def format_queue_summary(queue: Mapping[JobState, int]) -> str:
    lines: list[str] = []
    for state in (
        JobState.READY,
        JobState.LEASED,
        JobState.AWAITING_HUMAN,
        JobState.AWAITING_CAPACITY,
        JobState.SUCCEEDED,
        JobState.FAILED,
    ):
        count = queue.get(state, 0)
        lines.append(f"  • {state.name}: {count}")
    return "\n".join(lines)


def format_event_row(event: LedgerEvent) -> str:
    ts = event.produced_at.strftime("%H:%M:%S")
    engine = f"[{event.engine_id.value}]" if event.engine_id else ""
    return f"#{event.seq:<4} {ts} [{event.phase.name}] {event.kind.value} {engine}"


async def fetch_dashboard_state(
    *,
    projects: PostgresProjectRepository,
    jobs: JobRepository,
    health: EngineHealthRepository,
    ledger: PostgresLedgerRepository,
    project_id: UUID,
) -> DashboardState:
    project = await projects.get(project_id)
    if project is None:
        raise ValueError(f"unknown project {project_id}")

    queue_depth = await jobs.queue_depth(project_id)
    circuits = await health.list_for_project(project_id)
    events = await ledger.all_for_project(project_id)

    # Determine visual and deployment decisions from ledger events
    visual_dec: str | None = None
    deploy_dec: str | None = None
    for ev in events:
        if ev.kind == EventKind.VISUAL_DESIGN_OPTED_IN:
            visual_dec = "OPTED_IN"
        elif ev.kind == EventKind.VISUAL_DESIGN_DECLINED:
            visual_dec = "DECLINED"
        elif ev.kind == EventKind.VISUAL_DESIGN_ACCEPTED:
            visual_dec = "ACCEPTED"
        elif ev.kind == EventKind.VISUAL_DESIGN_WAIVED:
            visual_dec = "WAIVED"
        elif ev.kind == EventKind.DEPLOYMENT_OPTED_IN:
            deploy_dec = "OPTED_IN"
        elif ev.kind == EventKind.DEPLOYMENT_DECLINED:
            deploy_dec = "DECLINED"

    # Scan active worktrees
    managed_root = project.repo_path / ".vibey" / "worktrees" / str(project.cycle)
    worktrees: list[str] = []
    if managed_root.exists():
        worktrees = sorted([p.name for p in managed_root.iterdir() if p.is_dir()])

    # Recent tail (last 15 events)
    tail = events[-15:] if len(events) > 15 else events

    return DashboardState(
        project_id=project.project_id,
        project_name=project.name,
        repo_path=project.repo_path,
        phase=project.phase,
        cycle=project.cycle,
        max_cycles=project.max_cycles,
        visual_decision=visual_dec,
        deployment_decision=deploy_dec,
        queue_depth=queue_depth,
        circuits=circuits,
        active_worktrees=tuple(worktrees),
        ledger_tail=tuple(tail),
    )


class StatusPanel(Static):
    state: reactive[DashboardState | None] = reactive(None)

    def watch_state(self, state: DashboardState | None) -> None:
        if state is None:
            self.update("[bold]Status[/bold]\n  Loading...")
            return
        vis = f" | Visual: {state.visual_decision}" if state.visual_decision else ""
        dep = f" | Deploy: {state.deployment_decision}" if state.deployment_decision else ""
        text = (
            f"[bold cyan]Project:[/] {state.project_name} ({state.project_id})\n"
            f"[bold cyan]Phase:[/] [green]{state.phase.name}[/] | "
            f"[bold cyan]Cycle:[/] {state.cycle}/{state.max_cycles}{vis}{dep}\n"
            f"[bold cyan]Repo:[/] {state.repo_path}"
        )

        self.update(f"[bold underline]PROJECT STATUS[/bold underline]\n{text}")


class QueuePanel(Static):
    state: reactive[DashboardState | None] = reactive(None)

    def watch_state(self, state: DashboardState | None) -> None:
        if state is None:
            self.update("[bold]Queue[/bold]\n  Loading...")
            return
        text = format_queue_summary(state.queue_depth)
        self.update(f"[bold underline]QUEUE DEPTH[/bold underline]\n{text}")


class CircuitsPanel(Static):
    state: reactive[DashboardState | None] = reactive(None)

    def watch_state(self, state: DashboardState | None) -> None:
        if state is None:
            self.update("[bold]Circuits[/bold]\n  Loading...")
            return
        text = format_circuit_summary(state.circuits)
        self.update(f"[bold underline]ENGINE CIRCUITS[/bold underline]\n{text}")


class WorktreesPanel(Static):
    state: reactive[DashboardState | None] = reactive(None)

    def watch_state(self, state: DashboardState | None) -> None:
        if state is None:
            self.update("[bold]Worktrees[/bold]\n  Loading...")
            return
        if not state.active_worktrees:
            text = "  (none active)"
        else:
            text = "\n".join(f"  • {wt}" for wt in state.active_worktrees)
        self.update(f"[bold underline]ACTIVE WORKTREES[/bold underline]\n{text}")


class LedgerPanel(Static):
    state: reactive[DashboardState | None] = reactive(None)

    def watch_state(self, state: DashboardState | None) -> None:
        if state is None:
            self.update("[bold]Ledger Tail[/bold]\n  Loading...")
            return
        if not state.ledger_tail:
            text = "  (no ledger events yet)"
        else:
            text = "\n".join(format_event_row(ev) for ev in reversed(state.ledger_tail))
        self.update(f"[bold underline]LEDGER TAIL (Recent Events)[/bold underline]\n{text}")


class VibeyDashboardApp(App[None]):
    TITLE = "vibey supervisor"
    CSS = """
    Screen {
        background: $surface;
    }
    #top-bar {
        height: auto;
        border: solid $accent;
        margin: 1;
        padding: 1;
    }
    #middle-bar {
        height: auto;
        margin: 0 1;
    }
    #queue-panel {
        width: 30%;
        border: solid $secondary;
        padding: 1;
    }
    #circuits-panel {
        width: 35%;
        border: solid $secondary;
        padding: 1;
    }
    #worktrees-panel {
        width: 35%;
        border: solid $secondary;
        padding: 1;
    }
    #ledger-panel {
        height: 1fr;
        border: solid $primary;
        margin: 1;
        padding: 1;
        overflow-y: auto;
    }
    """
    BINDINGS: ClassVar[list[BindingType]] = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
    ]

    def __init__(
        self,
        *,
        initial_state: DashboardState | None = None,
        state_fetcher: Callable[[], DashboardState | None] | None = None,
        refresh_interval: float = 1.0,
    ) -> None:
        super().__init__()
        self._current_state = initial_state
        self._state_fetcher = state_fetcher
        self._refresh_interval = refresh_interval

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical():
            yield StatusPanel(id="status-panel")
            with Horizontal(id="middle-bar"):
                yield QueuePanel(id="queue-panel")
                yield CircuitsPanel(id="circuits-panel")
                yield WorktreesPanel(id="worktrees-panel")
            yield LedgerPanel(id="ledger-panel")
        yield Footer()

    def on_mount(self) -> None:
        self._update_all_widgets(self._current_state)
        if self._state_fetcher is not None and self._refresh_interval > 0:
            self.set_interval(self._refresh_interval, self.action_refresh)

    def action_refresh(self) -> None:
        if self._state_fetcher is not None:
            new_state = self._state_fetcher()
            if new_state is not None:
                self._current_state = new_state
                self._update_all_widgets(new_state)

    def _update_all_widgets(self, state: DashboardState | None) -> None:
        if state is None:
            return
        with suppress(Exception):
            self.query_one("#status-panel", StatusPanel).state = state
            self.query_one("#queue-panel", QueuePanel).state = state
            self.query_one("#circuits-panel", CircuitsPanel).state = state
            self.query_one("#worktrees-panel", WorktreesPanel).state = state
            self.query_one("#ledger-panel", LedgerPanel).state = state
