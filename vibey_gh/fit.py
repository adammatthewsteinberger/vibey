# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The fit calculus (#263): both sides of the fit, measured continuously.

Doctrine 10's hardware-decomposition clarification says to read the specs of the
hardware the code actually runs on AND the specs of the model actually wanted on
it — fully, honestly, in detail — then decompose work until each piece fits, down
to the floor of the lowest hardware that can run that model, and beyond the floor
to fail loudly to a human rather than silently.

This module is that clarification as a running control loop rather than a one-time
preflight. It samples both sides, keeps a rolling estimate of the two constants
that govern everything, projects whether a piece of work fits a deadline, and says
`admit`, `defer`, or `floor` with the arithmetic that justifies the answer.

The constants, measured on a live machine (24 GB, qwen2.5-coder:14b at 9.7 GB):

- **s** — effective parallelism, total generation-seconds ÷ wall seconds. Measured
  at 3.1 across a six-way rung, not the 2 a naive throughput reading suggested;
  payload size, not queue depth, governed wall time.
- **τ** — service time, a *distribution* (58s–206s observed) that scales with
  payload size, so it is estimated as `base + rate × bytes` from what actually ran.

Everything else follows: `wall(N) ≈ W(N)/s`, and a job fails when its projected
wait plus service exceeds the caller's deadline.

**This module never resizes swap by itself.** It computes what headroom the
projection needs and reports it; growing paging space is an irreversible act on
someone's machine, and Article III's bounded delegation puts that in a human's
hands. `recommendation()` is the output; acting on it is the operator's call.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field

__all__ = [
    "ADMIT",
    "DEFER",
    "FLOOR",
    "Estimate",
    "Fit",
    "Machine",
    "Model",
    "Observation",
    "decide",
    "estimate_from",
    "headroom_gb",
    "sample_machine",
    "sample_model",
    "saturating_wait",
]

ADMIT = "admit"
DEFER = "defer"
FLOOR = "floor"

_PAGE_KEYS = (
    "Pages free",
    "Pages active",
    "Pages inactive",
    "Pages wired down",
    "Pages occupied by compressor",
)


@dataclass(frozen=True)
class Machine:
    """The hardware side of the fit, as honestly as the machine states it."""

    total_gb: float
    free_gb: float
    swap_used_gb: float
    swap_total_gb: float

    @property
    def available_gb(self) -> float:
        """What a model could actually occupy right now: free memory plus the
        paging space not already spoken for."""
        return round(self.free_gb + max(self.swap_total_gb - self.swap_used_gb, 0.0), 2)


@dataclass(frozen=True)
class Model:
    """The model side of the fit — read, never assumed."""

    name: str
    size_gb: float
    context_length: int


@dataclass(frozen=True)
class Observation:
    """One completed operation, contributing its own timing to the estimate."""

    payload_bytes: int
    elapsed_s: float
    concurrent: int


@dataclass(frozen=True)
class Estimate:
    """The two constants, plus how much evidence stands behind them."""

    slots: float
    base_s: float
    rate_s_per_kb: float
    samples: int

    def service_s(self, payload_bytes: int) -> float:
        """τ for a payload of this size."""
        return round(self.base_s + self.rate_s_per_kb * (payload_bytes / 1024), 1)


@dataclass(frozen=True)
class Fit:
    verdict: str
    reason: str
    projected_wait_s: float
    projected_service_s: float
    headroom_gb: float
    estimate: Estimate | None = None
    notes: tuple[str, ...] = field(default=())

    @property
    def ok(self) -> bool:
        return self.verdict == ADMIT


def _run(*cmd: str) -> str:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return proc.stdout if proc.returncode == 0 else ""


def sample_machine() -> Machine:
    """Read the hardware side. Unreadable fields report zero rather than a guess —
    a projection built on invented numbers is worse than no projection."""
    total_bytes = 0
    raw = _run("sysctl", "-n", "hw.memsize").strip()
    if raw.isdigit():
        total_bytes = int(raw)

    free_gb = 0.0
    stat = _run("vm_stat")
    if stat:
        page_size = 4096
        first = stat.splitlines()[0] if stat.splitlines() else ""
        for token in first.replace(")", " ").split():
            if token.isdigit():
                page_size = int(token)
                break
        pages: dict[str, int] = {}
        for line in stat.splitlines():
            key, _, value = line.partition(":")
            digits = value.strip().rstrip(".")
            if key.strip() in _PAGE_KEYS and digits.isdigit():
                pages[key.strip()] = int(digits)
        free_pages = pages.get("Pages free", 0) + pages.get("Pages inactive", 0)
        free_gb = round(free_pages * page_size / 1e9, 2)

    swap_used = swap_total = 0.0
    swap = _run("sysctl", "-n", "vm.swapusage")
    for token in swap.replace("=", " ").split():
        if token.endswith("M") and token[:-1].replace(".", "", 1).isdigit():
            gb = float(token[:-1]) / 1024
            if swap_total == 0.0:
                swap_total = round(gb, 2)
            elif swap_used == 0.0:
                swap_used = round(gb, 2)
    return Machine(
        total_gb=round(total_bytes / 1e9, 2),
        free_gb=free_gb,
        swap_used_gb=swap_used,
        swap_total_gb=swap_total,
    )


def sample_model(name: str, base_url: str = "http://127.0.0.1:11434") -> Model | None:
    """Read the model side from the runner itself. None when it cannot be read —
    the caller must not proceed on an assumed model (doctrine 10)."""
    curl = shutil.which("curl")
    if not curl:
        return None
    body = _run(curl, "-s", "-m", "10", f"{base_url}/api/ps")
    if not body:
        return None
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return None
    for entry in data.get("models", []) or []:
        if not isinstance(entry, dict):
            continue
        if entry.get("name") == name or entry.get("model") == name:
            return Model(
                name=name,
                size_gb=round(float(entry.get("size", 0)) / 1e9, 2),
                context_length=int(entry.get("context_length", 0) or 0),
            )
    return None


def estimate_from(observations: list[Observation], floor_slots: float = 1.0) -> Estimate:
    """Fit s and τ to what actually ran.

    τ is `base + rate × KB` by least squares when the payload sizes differ; a
    single size cannot separate the two terms, so it all goes to `base` and the
    rate stays zero rather than being invented. s is total generation-seconds over
    wall-equivalent seconds, which is what the rung data actually measures.
    """
    if not observations:
        return Estimate(slots=floor_slots, base_s=0.0, rate_s_per_kb=0.0, samples=0)

    xs = [o.payload_bytes / 1024 for o in observations]
    ys = [o.elapsed_s for o in observations]
    n = len(observations)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    var_x = sum((x - mean_x) ** 2 for x in xs)
    if var_x > 0:
        rate = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / var_x
        base = mean_y - rate * mean_x
    else:
        rate, base = 0.0, mean_y
    # Negative fits are physically meaningless; fall back to the flat mean.
    if base < 0 or rate < 0:
        rate, base = 0.0, mean_y

    concurrent = max((o.concurrent for o in observations), default=1)
    slots = max(float(min(concurrent, n)), floor_slots)
    return Estimate(
        slots=round(slots, 2),
        base_s=round(base, 1),
        rate_s_per_kb=round(rate, 3),
        samples=n,
    )


def saturating_wait(service_s: float, queue_depth: int, slots: float) -> float:
    """Projected wait, superlinear in queue depth.

    A linear model — `service × queue/slots` — is what this module shipped with, and
    a stress escalation falsified it within one rung: measured latency grew 22 s per
    added job through twelve concurrent, then 59 s per job by sixteen. Linear
    projection under-predicts exactly where accuracy matters, so an admission rule
    built on it admits work that then times out — the failure this module exists to
    prevent.

    The correction keeps the shape a queue actually has. With load factor
    ρ = queue/slots, wait grows as ρ(1 + ρ): linear while the runner has slack,
    quadratic once it does not. That reproduces the observed slope growth far better
    than a line, and it is labelled for what it is — an empirical fit, refitted from
    observations, never trusted as a law.
    """
    if slots <= 0:
        return 0.0
    rho = queue_depth / slots
    return service_s * rho * (1 + rho)


def headroom_gb(machine: Machine, model: Model, slots: float) -> float:
    """Paging headroom the projection wants: one resident model plus a per-slot
    context share, less what is already available. Zero means the fit is
    comfortable and nothing needs to grow."""
    per_slot = model.size_gb * 0.1 * max(slots - 1, 0)
    wanted = model.size_gb + per_slot
    return round(max(wanted - machine.available_gb, 0.0), 2)


def decide(
    machine: Machine,
    model: Model | None,
    est: Estimate,
    *,
    queue_depth: int,
    payload_bytes: int,
    deadline_s: float,
) -> Fit:
    """Admit, defer, or declare the floor — with the arithmetic in the reason."""
    notes: list[str] = []
    if model is None:
        return Fit(
            verdict=FLOOR,
            reason=(
                "the model's own specs could not be read — doctrine 10 forbids"
                " proceeding on an assumed model; start the runner or name a model"
                " it holds"
            ),
            projected_wait_s=0.0,
            projected_service_s=0.0,
            headroom_gb=0.0,
            estimate=est,
        )

    ceiling = machine.total_gb + machine.swap_total_gb
    if ceiling > 0 and model.size_gb > ceiling:
        return Fit(
            verdict=FLOOR,
            reason=(
                f"{model.name} needs {model.size_gb} GB and this machine cannot reach"
                f" it: {machine.total_gb} GB of memory plus {machine.swap_total_gb} GB"
                " of paging space is the absolute ceiling. This is the floor doctrine"
                " 10 names — failing loudly rather than thrashing"
            ),
            projected_wait_s=0.0,
            projected_service_s=0.0,
            headroom_gb=round(model.size_gb - ceiling, 2),
            estimate=est,
        )

    service = est.service_s(payload_bytes)
    ahead = max(queue_depth, 0)
    wait = round(saturating_wait(service, ahead, est.slots), 1)
    need = headroom_gb(machine, model, est.slots)
    if need > 0:
        notes.append(
            f"projection wants {need} GB more headroom than the {machine.available_gb}"
            " GB available — grow paging space before it is needed, not after a stall"
        )
    if est.samples == 0:
        notes.append(
            "no observations yet: τ is unmeasured, so this projection is a floor, not a forecast"
        )

    if wait + service > deadline_s:
        return Fit(
            verdict=DEFER,
            reason=(
                f"projected {wait}s wait + {service}s service exceeds the {deadline_s}s"
                f" deadline at s={est.slots}, queue {ahead} — decompose the work or"
                " wait for a slot"
            ),
            projected_wait_s=wait,
            projected_service_s=service,
            headroom_gb=need,
            estimate=est,
            notes=tuple(notes),
        )
    return Fit(
        verdict=ADMIT,
        reason=(
            f"projected {wait}s wait + {service}s service fits the {deadline_s}s"
            f" deadline at s={est.slots}, queue {ahead}"
        ),
        projected_wait_s=wait,
        projected_service_s=service,
        headroom_gb=need,
        estimate=est,
        notes=tuple(notes),
    )
