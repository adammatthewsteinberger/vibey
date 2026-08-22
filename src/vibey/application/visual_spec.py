# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Render the accepted VISUAL_DESIGN inventory without performing I/O."""

from vibey.domain.visual import VisualInventory


def render_visual_artifacts(inventory: VisualInventory) -> dict[str, str]:
    violations = inventory.is_complete()
    if violations:
        raise ValueError("; ".join(violations))

    sections = []
    for surface in inventory.surfaces:
        states = "\n".join(f"- {state}" for state in surface.responsive_states)
        a11y = "\n".join(f"- {item}" for item in surface.accessibility_requirements)
        media = "\n".join(
            f"- [{entry.modality.value}] {entry.asset_key}: {entry.prompt}"
            for entry in surface.media_manifest
        )
        sections.append(
            f"## {surface.screen_id}: {surface.name} ({surface.action.value})\n\n"
            f"### Responsive states\n\n{states}\n\n"
            f"### Accessibility requirements\n\n{a11y}\n\n"
            f"### Media manifest\n\n{media}\n"
        )

    screen_inventory_md = "# Screen inventory\n\n" + "\n".join(sections)
    return {"screen-inventory.md": screen_inventory_md}
