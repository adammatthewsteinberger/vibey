# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The operator-seat failover engine (#208): paid lane down ⇒ hand the seat to a local agent.

When the paid IDE lane runs out of credit, the operator seat moves — autonomously and
losslessly — to the first healthy local agent (qwenloop, then opencode, by default), and
moves back the moment the paid lane answers again. Lossless because the seats share one
working tree and the local-authority loop (#207) keeps both fronts synced the whole time:
the handoff never appears in git history as anything but uninterrupted work.

Sub-doctrine 10.a reads this as the censorship-resistance ladder for the seat itself:
hosted agent → open-source local agent → raw local model, each rung less refusable than
the last.

Deliberately machine-level, not repository-level: seats and probes describe the
operator's machine, so configuration lives in ``~/.config/vibey-gh/failover.toml`` (or
``--config``), never in a repository's ``.vibey-gh.toml``. Off until that file says
``enabled = true`` — nothing here ever self-activates.

The engine is three decisions, kept pure so they are testable byte-for-byte:

- paid lane answers and a seat is active  → RECLAIM (stop the seat; the paid lane leads);
- paid lane down and no seat is active    → ENGAGE the first healthy seat;
- anything else                           → HOLD.

Every probe, launch, and health check is an operator-supplied shell command judged only
by its exit status, so any agent, any IDE, and any future lane fits without a code
change.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import time
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

__all__ = [
    "ENGAGE",
    "HOLD",
    "RECLAIM",
    "FailoverConfig",
    "Seat",
    "load",
    "probe",
    "run",
    "run_once",
    "step",
]

ENGAGE = "engage"
HOLD = "hold"
RECLAIM = "reclaim"

_DEFAULT_CONFIG = Path("~/.config/vibey-gh/failover.toml")
_DEFAULT_STATE = Path("~/.local/state/vibey-gh/failover.json")


@dataclass(frozen=True)
class Seat:
    """One relief agent: how to start it, and how to know it could work here."""

    name: str
    launch: str
    # Empty means "assume healthy": the seat is engaged without a preflight.
    health: str = ""


@dataclass(frozen=True)
class FailoverConfig:
    # Off until the operator writes the file and says so; the engine never assumes a
    # machine wants its seat managed (doctrine 10: never assumed, always confirmed).
    enabled: bool = False
    # Exit 0 = the paid lane is alive. The 296ms "Credit balance is too low" refusal
    # (vibey-gh#201) is exactly what this command exists to distinguish from health.
    paid_probe: str = ""
    interval_seconds: int = 300
    seats: tuple[Seat, ...] = field(
        default_factory=lambda: (
            Seat(name="qwenloop", launch="qwenloop run"),
            Seat(name="opencode", launch="opencode"),
        )
    )


def load(path: Path | None = None) -> FailoverConfig:
    """Read the machine-level config; a missing file is a disabled engine, not an error."""
    where = (path or _DEFAULT_CONFIG).expanduser()
    if not where.is_file():
        return FailoverConfig()
    data = tomllib.loads(where.read_text(encoding="utf-8"))
    seats = tuple(
        Seat(
            name=str(entry.get("name", "")),
            launch=str(entry.get("launch", "")),
            health=str(entry.get("health", "")),
        )
        for entry in data.get("seats", [])
        if entry.get("name") and entry.get("launch")
    )
    return FailoverConfig(
        enabled=bool(data.get("enabled", False)),
        paid_probe=str(data.get("paid_probe", "")),
        interval_seconds=int(data.get("interval_seconds", 300)),
        seats=seats or FailoverConfig().seats,
    )


def probe(command: str, timeout: int = 120) -> bool:
    """Exit 0 within the timeout = alive. Everything else — including a hang — is down."""
    if not command:
        return False
    try:
        # `command` is [failover] paid_probe / seats[].health from this repository's own
        # .vibey-gh.toml. A seat's probe IS a shell command line by design, written by the
        # operator; anyone who can edit that file can already edit the workflows that run
        # it, so this is a configuration boundary, not an input one.
        run_ = subprocess.run(  # nosec B602
            command, shell=True, capture_output=True, timeout=timeout, check=False
        )
    except subprocess.TimeoutExpired:
        return False
    return run_.returncode == 0


def step(paid_ok: bool, seat_active: bool) -> str:
    """The whole policy, pure: the paid lane leads whenever it answers."""
    if paid_ok and seat_active:
        return RECLAIM
    if not paid_ok and not seat_active:
        return ENGAGE
    return HOLD


def _read_state(state_path: Path) -> dict:
    try:
        value = json.loads(state_path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _write_state(state_path: Path, state: dict) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def _seat_alive(state: dict) -> bool:
    pid = state.get("pid")
    if not isinstance(pid, int):
        return False
    try:
        os.kill(pid, 0)
    except (ProcessLookupError, PermissionError):
        return False
    return True


def _engage(cfg: FailoverConfig, state_path: Path, report) -> None:
    for seat in cfg.seats:
        if seat.health and not probe(seat.health):
            report(f"vibey-gh failover: seat {seat.name} failed its health check; next")
            continue
        # Same boundary: `launch` is the operator's own seat command line.
        child = subprocess.Popen(seat.launch, shell=True, start_new_session=True)  # nosec B602
        _write_state(
            state_path,
            {"seat": seat.name, "pid": child.pid, "since": int(time.time())},
        )
        report(
            f"vibey-gh failover: paid lane down — seat handed to {seat.name} "
            f"(pid {child.pid}); local-authority keeps both fronts synced"
        )
        return
    # No seat could take over. Say so loudly: a silent gap here is an operator with no
    # agent at all, which is the one outcome this engine exists to prevent.
    report("vibey-gh failover: paid lane down and NO seat is healthy — operator needed")


def _reclaim(state: dict, state_path: Path, report) -> None:
    pid = state.get("pid")
    if isinstance(pid, int):
        try:
            os.killpg(pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            try:
                os.kill(pid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                pass
    _write_state(state_path, {})
    report(
        f"vibey-gh failover: paid lane recovered — seat reclaimed from "
        f"{state.get('seat', 'unknown')}; healing needed nothing but the funding"
    )


def run_once(
    cfg: FailoverConfig,
    state_path: Path | None = None,
    report=print,
) -> str:
    """One probe, one decision, one transition. Returns the action taken."""
    if not cfg.enabled:
        report("vibey-gh failover: disabled (enable it in ~/.config/vibey-gh/failover.toml)")
        return HOLD
    where = (state_path or _DEFAULT_STATE).expanduser()
    state = _read_state(where)
    seat_active = _seat_alive(state)
    if state and not seat_active:
        # The seat died on its own; clear the record so ENGAGE can run again.
        _write_state(where, {})
        state = {}
    action = step(probe(cfg.paid_probe), seat_active)
    if action == ENGAGE:
        _engage(cfg, where, report)
    elif action == RECLAIM:
        _reclaim(state, where, report)
    else:
        report(f"vibey-gh failover: hold ({'seat active' if seat_active else 'paid lane leads'})")
    return action


def run(
    cfg: FailoverConfig,
    state_path: Path | None = None,
    once: bool = False,
    report=print,
    sleep=time.sleep,
) -> None:
    """The supervised loop: what a LaunchAgent or systemd unit runs."""
    while True:
        run_once(cfg, state_path=state_path, report=report)
        if once:
            return
        sleep(cfg.interval_seconds)
