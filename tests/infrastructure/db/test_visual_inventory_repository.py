# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from pathlib import Path
from uuid import UUID

import asyncpg

from vibey.domain.visual import (
    MediaManifestEntry,
    MediaModality,
    ScreenSurface,
    SurfaceAction,
    VisualInventory,
)
from vibey.infrastructure.db.project_repository import PostgresProjectRepository
from vibey.infrastructure.db.visual_inventory_repository import FileVisualInventoryRepository


def complete_inventory() -> VisualInventory:
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


async def test_save_load_and_publish_visual_artifacts(
    migrated_pool: asyncpg.Pool, tmp_path: Path
) -> None:
    projects = PostgresProjectRepository(migrated_pool)
    project = await projects.create("demo", tmp_path, max_cycles=10, config={})
    inventories = FileVisualInventoryRepository(projects)

    await inventories.save(project.project_id, 1, complete_inventory())
    assert await inventories.load(project.project_id, 1) == complete_inventory()
    await inventories.publish(project.project_id, 1, complete_inventory())

    assert (tmp_path / ".vibey/context/visual/screen-inventory.md").exists()


async def test_load_missing_inventory_returns_none_and_unknown_project_fails(
    migrated_pool: asyncpg.Pool, tmp_path: Path
) -> None:
    projects = PostgresProjectRepository(migrated_pool)
    project = await projects.create("demo", tmp_path, max_cycles=10, config={})
    inventories = FileVisualInventoryRepository(projects)
    assert await inventories.load(project.project_id, 1) is None

    try:
        await inventories.save(UUID(int=0), 1, complete_inventory())
    except LookupError as exc:
        assert "project" in str(exc)
    else:
        raise AssertionError("expected unknown project failure")

    try:
        await inventories.publish(UUID(int=0), 1, complete_inventory())
    except LookupError as exc:
        assert "project" in str(exc)
    else:
        raise AssertionError("expected unknown project failure")
