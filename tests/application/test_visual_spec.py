# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
import pytest

from vibey.application.visual_spec import render_visual_artifacts
from vibey.domain.visual import (
    MediaManifestEntry,
    MediaModality,
    ScreenSurface,
    SurfaceAction,
    VisualInventory,
)


def _inventory() -> VisualInventory:
    return VisualInventory(
        surfaces=(
            ScreenSurface(
                screen_id="home",
                name="Home",
                action=SurfaceAction.CREATE,
                responsive_states=("mobile", "desktop"),
                accessibility_requirements=("keyboard navigable",),
                media_manifest=(MediaManifestEntry("hero", MediaModality.IMAGE, "a hero image"),),
            ),
        )
    )


def test_render_visual_artifacts_produces_screen_inventory() -> None:
    artifacts = render_visual_artifacts(_inventory())

    assert set(artifacts) == {"screen-inventory.md"}
    body = artifacts["screen-inventory.md"]
    assert "home: Home (create)" in body
    assert "mobile" in body
    assert "keyboard navigable" in body
    assert "hero" in body


def test_render_visual_artifacts_rejects_incomplete_inventory() -> None:
    with pytest.raises(ValueError, match="screen surface"):
        render_visual_artifacts(VisualInventory(()))
