# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
from vibey.domain.visual import (
    MediaManifestEntry,
    MediaModality,
    ScreenSurface,
    SurfaceAction,
    VisualInventory,
)


def _surface(**overrides: object) -> ScreenSurface:
    defaults: dict[str, object] = {
        "screen_id": "s1",
        "name": "Home",
        "action": SurfaceAction.CREATE,
        "responsive_states": ("mobile", "desktop"),
        "accessibility_requirements": ("keyboard navigable",),
        "media_manifest": (MediaManifestEntry("hero", MediaModality.IMAGE, "a hero image"),),
    }
    defaults.update(overrides)
    return ScreenSurface(**defaults)  # type: ignore[arg-type]


def test_is_complete_empty_when_all_guards_pass() -> None:
    assert VisualInventory((_surface(),)).is_complete() == ()


def test_is_complete_flags_no_surfaces() -> None:
    violations = VisualInventory(()).is_complete()
    assert any("screen surface" in v for v in violations)


def test_is_complete_flags_missing_responsive_states() -> None:
    violations = VisualInventory((_surface(responsive_states=()),)).is_complete()
    assert any("s1" in v and "responsive states" in v for v in violations)


def test_is_complete_flags_missing_accessibility_requirements() -> None:
    violations = VisualInventory((_surface(accessibility_requirements=()),)).is_complete()
    assert any("s1" in v and "accessibility" in v for v in violations)


def test_is_complete_flags_missing_media_manifest() -> None:
    violations = VisualInventory((_surface(media_manifest=()),)).is_complete()
    assert any("s1" in v and "media manifest" in v for v in violations)


def test_is_complete_reports_every_violation_across_multiple_surfaces() -> None:
    bad_one = _surface(screen_id="s1", responsive_states=())
    bad_two = _surface(screen_id="s2", accessibility_requirements=())
    violations = VisualInventory((bad_one, bad_two)).is_complete()
    assert any("s1" in v for v in violations)
    assert any("s2" in v for v in violations)


def test_update_action_is_supported() -> None:
    surface = _surface(action=SurfaceAction.UPDATE)
    assert surface.action is SurfaceAction.UPDATE
    assert VisualInventory((surface,)).is_complete() == ()
