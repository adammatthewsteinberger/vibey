"""Live dashboard TUI implemented with Textual."""

from collections.abc import Callable, Mapping, Sequence
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar
from uuid import UUID, uuid4

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
        state_fetcher: Callable[[], DashboardState | None] | Callable[[], Any] | None = None,
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
            self.set_interval(self._refresh_interval, self._do_refresh)

    async def _do_refresh(self) -> None:
        if self._state_fetcher is None:
            return
        import inspect

        result = self._state_fetcher()
        if inspect.isawaitable(result):
            new_state: DashboardState | None = await result
        else:
            new_state = result
        if new_state is not None:
            self._current_state = new_state
            self._update_all_widgets(new_state)

    def action_refresh(self) -> None:
        self.run_worker(self._do_refresh())

    def _update_all_widgets(self, state: DashboardState | None) -> None:
        if state is None:
            return
        with suppress(Exception):
            self.query_one("#status-panel", StatusPanel).state = state
            self.query_one("#queue-panel", QueuePanel).state = state
            self.query_one("#circuits-panel", CircuitsPanel).state = state
            self.query_one("#worktrees-panel", WorktreesPanel).state = state
            self.query_one("#ledger-panel", LedgerPanel).state = state


def build_replay_states(
    project: Any,
    events: Sequence[LedgerEvent],
) -> list[DashboardState]:
    """Reconstructs state history step-by-step from ledger events."""
    states: list[DashboardState] = []

    current_phase = Phase.INTAKE
    current_cycle = 1
    visual_decision: str | None = None
    deployment_decision: str | None = None
    queue_counts: dict[JobState, int] = {s: 0 for s in JobState}
    circuits: list[EngineHealthRecord] = []
    active_worktrees: list[str] = []
    tail: list[LedgerEvent] = []

    initial_state = DashboardState(
        project_id=project.project_id,
        project_name=project.name,
        repo_path=project.repo_path,
        phase=current_phase,
        cycle=current_cycle,
        max_cycles=project.max_cycles,
        visual_decision=visual_decision,
        deployment_decision=deployment_decision,
        queue_depth=dict(queue_counts),
        circuits=tuple(circuits),
        active_worktrees=tuple(active_worktrees),
        ledger_tail=(),
    )
    states.append(initial_state)

    for ev in events:
        tail.append(ev)
        current_phase = ev.phase
        current_cycle = ev.cycle

        if ev.kind == EventKind.VISUAL_DESIGN_OPTED_IN:
            visual_decision = "OPTED_IN"
        elif ev.kind in {EventKind.VISUAL_DESIGN_WAIVED, EventKind.VISUAL_DESIGN_DECLINED}:
            visual_decision = "WAIVED"
        elif ev.kind == EventKind.DEPLOYMENT_OPTED_IN:
            deployment_decision = "OPTED_IN"
        elif ev.kind == EventKind.DEPLOYMENT_DECLINED:
            deployment_decision = "DECLINED"

        snap = DashboardState(
            project_id=project.project_id,
            project_name=project.name,
            repo_path=project.repo_path,
            phase=current_phase,
            cycle=current_cycle,
            max_cycles=project.max_cycles,
            visual_decision=visual_decision,
            deployment_decision=deployment_decision,
            queue_depth=dict(queue_counts),
            circuits=tuple(circuits),
            active_worktrees=tuple(active_worktrees),
            ledger_tail=tuple(tail[-20:]),
        )
        states.append(snap)

    return states


class VibeyReplayApp(App[None]):
    CSS = VibeyDashboardApp.CSS

    BINDINGS: ClassVar[list[BindingType]] = [
        ("q", "quit", "Quit"),
        ("space", "toggle_play", "Play/Pause"),
        ("right", "next_step", "Next Step"),
        ("n", "next_step", "Next Step"),
        ("left", "prev_step", "Prev Step"),
        ("p", "prev_step", "Prev Step"),
    ]

    current_step: reactive[int] = reactive(0)
    is_playing: reactive[bool] = reactive(False)

    def __init__(
        self,
        *,
        states: Sequence[DashboardState],
        playback_speed_hz: float = 1.0,
    ) -> None:
        super().__init__()
        self._states = list(states) or [
            DashboardState(
                project_id=uuid4(),
                project_name="unknown",
                repo_path=Path("."),
                phase=Phase.INTAKE,
                cycle=1,
                max_cycles=1,
                visual_decision=None,
                deployment_decision=None,
                queue_depth={s: 0 for s in JobState},
                circuits=(),
                active_worktrees=(),
                ledger_tail=(),
            )
        ]
        self._playback_speed = playback_speed_hz

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            with Vertical(id="left-pane"):
                yield StatusPanel(id="status-panel")
                yield QueuePanel(id="queue-panel")
                yield CircuitsPanel(id="circuits-panel")
                yield WorktreesPanel(id="worktrees-panel")
            yield LedgerPanel(id="ledger-panel")
        yield Footer()

    def on_mount(self) -> None:
        self._update_ui()
        if self._playback_speed > 0:
            interval = 1.0 / self._playback_speed
            self.set_interval(interval, self._tick)

    def _tick(self) -> None:
        if self.is_playing and self.current_step < len(self._states) - 1:
            self.current_step += 1

    def watch_current_step(self, new_val: int) -> None:
        self._update_ui()

    def _update_ui(self) -> None:
        if not self._states:
            return
        state = self._states[self.current_step]
        max_step = len(self._states) - 1
        with suppress(Exception):
            status_panel = self.query_one("#status-panel", StatusPanel)
            status_panel.state = state
            vis = f" | Visual: {state.visual_decision}" if state.visual_decision else ""
            dep = f" | Deploy: {state.deployment_decision}" if state.deployment_decision else ""
            status_panel.update(
                f"[bold cyan]vibey (REPLAY)[/bold cyan]  Step {self.current_step}/{max_step}\n"
                f"Project: {state.project_name}  ({state.project_id})\n"
                f"Phase:   [bold green]{state.phase.name}[/bold green]  | "
                f"Cycle: {state.cycle}/{state.max_cycles}{vis}{dep}\n"
                f"Repo:    {state.repo_path}"
            )

            self.query_one("#queue-panel", QueuePanel).state = state
            self.query_one("#circuits-panel", CircuitsPanel).state = state
            self.query_one("#worktrees-panel", WorktreesPanel).state = state
            self.query_one("#ledger-panel", LedgerPanel).state = state

    def action_next_step(self) -> None:
        if self.current_step < len(self._states) - 1:
            self.current_step += 1

    def action_prev_step(self) -> None:
        if self.current_step > 0:
            self.current_step -= 1

    def action_toggle_play(self) -> None:
        self.is_playing = not self.is_playing
