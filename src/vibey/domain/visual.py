# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The visual-design interstitial's inventory (M5 task 5.7).

A ``VisualInventory`` is the screen/state matrix a ``visual.inventory`` job
produces: every surface the spec implies, each with the responsive states,
accessibility requirements, and media manifest entries the visual-plan and
generation stages (tasks 5.8-5.11, not yet built) will consume. This module
only carries the shape and its completeness check -- generation, providers,
and review are separate, not-yet-implemented milestones.
"""

from dataclasses import dataclass
from enum import StrEnum


class MediaModality(StrEnum):
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


class SurfaceAction(StrEnum):
    CREATE = "create"
    UPDATE = "update"


@dataclass(frozen=True, slots=True)
class MediaManifestEntry:
    asset_key: str
    modality: MediaModality
    prompt: str


@dataclass(frozen=True, slots=True)
class ScreenSurface:
    screen_id: str
    name: str
    action: SurfaceAction
    responsive_states: tuple[str, ...]
    accessibility_requirements: tuple[str, ...]
    media_manifest: tuple[MediaManifestEntry, ...]


@dataclass(frozen=True, slots=True)
class VisualInventory:
    surfaces: tuple[ScreenSurface, ...]

    def is_complete(self) -> tuple[str, ...]:
        """Returns violations; empty means the inventory can enter visual.plan.

        Task 5.7's done condition, verbatim: every create/update surface,
        responsive state, accessibility requirement, and media manifest entry
        must be represented.
        """
        violations = []
        if not self.surfaces:
            violations.append("at least one screen surface is required")
        for surface in self.surfaces:
            if not surface.responsive_states:
                violations.append(f"screen {surface.screen_id!r} has no responsive states")
            if not surface.accessibility_requirements:
                violations.append(f"screen {surface.screen_id!r} has no accessibility requirements")
            if not surface.media_manifest:
                violations.append(f"screen {surface.screen_id!r} has no media manifest entries")
        return tuple(violations)
