# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Forecasting how much capacity is left, so a run can stop *before* it runs out.

The existing capacity states answer "am I blocked right now?". By the time one
says yes it is too late to hand off cleanly: the snapshot, the stop summary and
the final save point all need capacity to produce. This module answers the
earlier question -- "am I about to be blocked?" -- so the wind-down happens
while there is still room to do it properly.

Pure. Five laws hold regardless of vendor, each one a test:

F1  Unknown is never exhausted. A missing vendor field must not stop a run.
    This is the counterpart of "a credits balance has no clock": we do not
    invent a number we were not given.
F2  Stale degrades to unknown, not to stale. Utilization arrives on an event;
    between events it is a lie, so past `max_staleness` it becomes unknown.
F3  Never before the first completed turn. Otherwise a run that starts at 90%
    utilization hands off an empty brief, and engines pass nothing to each
    other forever.
F4  Monotone. Lowering any headroom can never turn a wind-down back off.
F5  The binding dimension is the minimum *known* one -- never the minimum
    including unknowns.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from claudeloop.domain.capacity import Available

UNKNOWN = None


@dataclass(frozen=True, slots=True)
class Headroom:
    """One dimension's remaining capacity, normalised to [0.0, 1.0].

    ``fraction is None`` means UNKNOWN and never 0.0 -- conflating "we cannot
    see it" with "there is none left" is exactly how a healthy run gets
    stopped for no reason.
    """

    fraction: float | None
    source: str
    as_of: datetime | None = None
    resets_at: datetime | None = None

    @property
    def known(self) -> bool:
        return self.fraction is not None

    def staled(self, *, now: datetime, max_staleness: timedelta) -> Headroom:
        """F2: past its shelf life a reading becomes unknown, not stale."""
        if self.as_of is None or self.fraction is None:
            return self
        if now - self.as_of > max_staleness:
            return Headroom(UNKNOWN, self.source, self.as_of, self.resets_at)
        return self


@dataclass(frozen=True, slots=True)
class BurnRate:
    """What the run has actually spent, for projecting what is left."""

    turns: int
    elapsed_seconds: float
    dollars: float = 0.0

    @property
    def dollars_per_turn(self) -> float | None:
        if self.turns <= 0:
            return None
        return self.dollars / self.turns


@dataclass(frozen=True, slots=True)
class CapacityForecast:
    binding: Headroom
    dimensions: tuple[Headroom, ...]
    turns_until_exhaustion: float | None
    seconds_until_reset: float | None

    @property
    def known(self) -> bool:
        return self.binding.known


@dataclass(frozen=True, slots=True)
class WindDownPolicy:
    """When to stop early.

    ``enabled`` defaults to False on purpose. A predictive stop shipped without
    real forecast data to tune it against is a guess applied to every run; the
    first release only measures.
    """

    enabled: bool = False
    headroom_floor: float = 0.15
    min_turns_reserve: int = 2
    max_staleness: timedelta = timedelta(minutes=15)


@dataclass(frozen=True, slots=True)
class WindDown:
    reason: str
    forecast: CapacityForecast


def _vendor_headrooms(
    available: Available,
    *,
    now: datetime,
    as_of: datetime | None,
    resets_at: datetime | None = None,
) -> tuple[Headroom, ...]:
    """Vendor-reported headroom, from ``Available.utilization``.

    ``as_of`` must be supplied by the caller: utilization arrives on a
    rate-limit event, so without knowing when it was read we cannot tell a
    fresh 0.9 from an hour-old one (F2). ``resets_at`` comes from the same
    event -- the vendor reports it even while still allowing traffic, and
    nothing consumed it before now.
    """
    del now
    if available.utilization is None:
        return (Headroom(UNKNOWN, "utilization", as_of, resets_at),)
    remaining = max(0.0, min(1.0, 1.0 - available.utilization))
    return (Headroom(remaining, "utilization", as_of, resets_at),)


def _budget_headrooms(
    *,
    turns_spent: int,
    max_turns: int | None,
    dollars_spent: float,
    max_dollars: float | None,
) -> tuple[Headroom, ...]:
    """Budget caps are exact, so they never go stale and carry no as_of."""
    dimensions: list[Headroom] = []
    if max_turns is not None and max_turns > 0:
        remaining = max(0, max_turns - turns_spent) / max_turns
        dimensions.append(Headroom(remaining, "turns"))
    else:
        dimensions.append(Headroom(UNKNOWN, "turns"))
    if max_dollars is not None and max_dollars > 0:
        remaining = max(0.0, max_dollars - dollars_spent) / max_dollars
        dimensions.append(Headroom(remaining, "dollars"))
    else:
        dimensions.append(Headroom(UNKNOWN, "dollars"))
    return tuple(dimensions)


def _binding(dimensions: tuple[Headroom, ...]) -> Headroom:
    """F5: the tightest *known* dimension, or an unknown one if none are."""
    known = [d for d in dimensions if d.known]
    if not known:
        return dimensions[0] if dimensions else Headroom(UNKNOWN, "none")
    return min(known, key=lambda d: d.fraction if d.fraction is not None else 1.0)


def forecast(
    available: Available,
    *,
    turns_spent: int,
    max_turns: int | None = None,
    dollars_spent: float = 0.0,
    max_dollars: float | None = None,
    observed: BurnRate | None = None,
    capacity_as_of: datetime | None = None,
    capacity_resets_at: datetime | None = None,
    now: datetime,
    policy: WindDownPolicy | None = None,
) -> CapacityForecast:
    """Project remaining capacity.

    Takes ``Available`` specifically, not the whole capacity union. That is the
    enforcement mechanism for the rule that vendor utilization is informational
    and must never itself block a turn: forecasting only ever runs when the
    vendor has already said we are *not* blocked, and it decides whether to
    stop after a turn completes rather than whether to send one.
    """
    active = policy or WindDownPolicy()
    dimensions = tuple(
        h.staled(now=now, max_staleness=active.max_staleness)
        for h in _vendor_headrooms(
            available, now=now, as_of=capacity_as_of, resets_at=capacity_resets_at
        )
    ) + _budget_headrooms(
        turns_spent=turns_spent,
        max_turns=max_turns,
        dollars_spent=dollars_spent,
        max_dollars=max_dollars,
    )
    binding = _binding(dimensions)

    turns_left: float | None = None
    if max_turns is not None and max_turns > 0:
        turns_left = float(max(0, max_turns - turns_spent))
    if (
        observed is not None
        and max_dollars is not None
        and (per_turn := observed.dollars_per_turn)
        and per_turn > 0
    ):
        by_dollars = max(0.0, max_dollars - dollars_spent) / per_turn
        turns_left = by_dollars if turns_left is None else min(turns_left, by_dollars)

    seconds_until_reset: float | None = None
    resets = [d.resets_at for d in dimensions if d.resets_at is not None]
    if resets:
        seconds_until_reset = max(0.0, (min(resets) - now).total_seconds())

    return CapacityForecast(
        binding=binding,
        dimensions=dimensions,
        turns_until_exhaustion=turns_left,
        seconds_until_reset=seconds_until_reset,
    )


def should_wind_down(
    projection: CapacityForecast,
    policy: WindDownPolicy,
    *,
    turns_spent: int,
) -> WindDown | None:
    """Decide whether to hand off now rather than risk being cut off mid-turn."""
    if not policy.enabled:
        return None
    # F3: an engine must do some work before it can hand any over.
    if turns_spent < 1:
        return None
    # F1: unknown is not exhausted.
    if not projection.known:
        return None

    for dimension in projection.dimensions:
        fraction = dimension.fraction
        if fraction is None:
            continue
        # Turns are covered by the reserve check below, which is expressed in
        # turns remaining rather than as a fraction of the cap.
        if dimension.source == "turns" and policy.min_turns_reserve > 0:
            continue
        if fraction <= policy.headroom_floor:
            return WindDown(reason=f"headroom:{dimension.source}", forecast=projection)

    if (
        projection.turns_until_exhaustion is not None
        and projection.turns_until_exhaustion <= policy.min_turns_reserve
    ):
        return WindDown(reason="turn_reserve", forecast=projection)
    return None
