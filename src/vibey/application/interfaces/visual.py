# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""The optional visual-design interstitial."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable
from uuid import UUID

from vibey.application.design import (
    DesignEvent,
)
from vibey.domain.visual import VisualInventory


@runtime_checkable
class VisualInventoryProducer(Protocol):
    async def inventory(self, events: Sequence[DesignEvent]) -> VisualInventory: ...


@runtime_checkable
class VisualInventoryRepository(Protocol):
    async def save(self, project_id: UUID, cycle: int, inventory: VisualInventory) -> None: ...

    async def load(self, project_id: UUID, cycle: int) -> VisualInventory | None: ...

    async def publish(self, project_id: UUID, cycle: int, inventory: VisualInventory) -> None: ...
