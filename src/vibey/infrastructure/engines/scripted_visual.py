# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Offline deterministic VisualInventory producer used by integration tests.

Not presented as a live model-backed screen inventory -- exercises the same
application ports and persistence without network or a provider account, same
role scripted_design.py plays for the DESIGN interview.
"""

from collections.abc import Sequence

from vibey.application.design import DesignEvent
from vibey.domain.visual import (
    MediaManifestEntry,
    MediaModality,
    ScreenSurface,
    SurfaceAction,
    VisualInventory,
)


class ScriptedVisualProvider:
    async def inventory(self, events: Sequence[DesignEvent]) -> VisualInventory:
        return VisualInventory(
            surfaces=(
                ScreenSurface(
                    screen_id="home",
                    name="Home",
                    action=SurfaceAction.CREATE,
                    responsive_states=("mobile", "desktop", "loading", "empty", "error"),
                    accessibility_requirements=("keyboard navigable", "screen-reader labeled"),
                    media_manifest=(
                        MediaManifestEntry(
                            "hero", MediaModality.IMAGE, "Offline scripted hero placeholder"
                        ),
                    ),
                ),
            )
        )
