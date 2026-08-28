# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Media-provider capability discovery and per-modality rotation (M5 tasks
5.9/5.10). Capability-based, not model-name-based: a provider advertises
modalities, reference-input limits, output formats, region/data policy,
retention, safety, cost, and whether generation is long-running, per
phase-protocols.md's VISUAL_DESIGN media-generation section.

The selection algorithm is nginx's Smooth Weighted Round Robin, the same one
domain/rotation.py uses for engines -- reimplemented here rather than shared
because the two rotate different identity types (EngineId vs. a provider id)
and the two must be free to diverge (media has no capacity/circuit-breaker
concept yet). Media generation jobs, providers, and moderation (task 5.11)
are not built here; this module only covers "which provider, if any."
"""

from collections.abc import Sequence
from dataclasses import dataclass, replace

from vibey.domain.errors import NoEligibleEngine
from vibey.domain.visual import MediaModality


@dataclass(frozen=True, slots=True)
class MediaProviderDescriptor:
    provider_id: str
    modalities: frozenset[MediaModality]
    reference_input_limit: int
    output_formats: frozenset[str]
    region: str
    retention_policy: str
    safety_policy: str
    cost_per_unit: float
    long_running: bool
    external: bool  # False: local/self-hosted, tried first. True: hosted fallback.


@dataclass(frozen=True, slots=True)
class MediaRequirement:
    modality: MediaModality
    allow_external: bool = False
    max_cost_per_unit: float | None = None


@dataclass(frozen=True, slots=True)
class MediaProviderRuntime:
    descriptor: MediaProviderDescriptor
    circuit_open: bool = False


def eligible(
    runtimes: Sequence[MediaProviderRuntime], *, requirement: MediaRequirement
) -> tuple[MediaProviderRuntime, ...]:
    result = []
    for runtime in runtimes:
        descriptor = runtime.descriptor
        if runtime.circuit_open:
            continue
        if requirement.modality not in descriptor.modalities:
            continue
        if descriptor.external and not requirement.allow_external:
            continue
        if (
            requirement.max_cost_per_unit is not None
            and descriptor.cost_per_unit > requirement.max_cost_per_unit
        ):
            continue
        result.append(runtime)
    return tuple(result)


@dataclass(frozen=True, slots=True)
class MediaCandidate:
    provider_id: str
    base_weight: int
    current: int
    order: int

    @property
    def effective_weight(self) -> int:
        return max(0, self.base_weight)


@dataclass(frozen=True, slots=True)
class MediaSelection:
    provider_id: str
    candidates: tuple[MediaCandidate, ...]  # updated SWRR state


def select(candidates: Sequence[MediaCandidate]) -> MediaSelection:
    """Smooth Weighted Round Robin over eligible providers for one modality.

    Each modality rotates independently: callers pass only the candidates for
    the modality being selected, with a cursor scoped to (project, modality).
    Requires unique provider_id per candidate, same precondition as
    rotation.select() and for the same reason -- duplicate weights would
    silently collide in the dict-keyed bump step below.
    """
    if not candidates:
        raise NoEligibleEngine("no media-provider candidates to select from")

    provider_ids = [c.provider_id for c in candidates]
    if len(set(provider_ids)) != len(provider_ids):
        raise ValueError("select() requires unique provider_id per candidate")

    if all(c.effective_weight == 0 for c in candidates):
        raise NoEligibleEngine("every media-provider candidate has effective_weight 0")

    total_weight = sum(c.effective_weight for c in candidates)
    bumped = {c.provider_id: c.current + c.effective_weight for c in candidates}

    winner = max(candidates, key=lambda c: (bumped[c.provider_id], -c.order))
    bumped[winner.provider_id] -= total_weight

    updated = tuple(replace(c, current=bumped[c.provider_id]) for c in candidates)
    return MediaSelection(provider_id=winner.provider_id, candidates=updated)
