# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Decoders shared by every DESIGN provider.

Extracted so the sovereign provider does not have to import from the paid one. Both
cross the same boundary — model text becoming domain objects — and both must refuse
malformed input in the same way, so the refusals belong in one place.
"""

import json
from collections.abc import Sequence

from vibey.application.design import DesignEvent


def events_json(events: Sequence[DesignEvent]) -> str:
    """The ledger a provider reasons over, as JSON it can be shown."""
    return json.dumps(
        [
            {
                "kind": event.kind.value,
                "provenance": event.provenance.value,
                "produced_at": event.produced_at.isoformat(),
                "payload": event.payload,
            }
            for event in events
        ],
        default=str,
    )


def as_list(value: object, field: str) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    return value


def as_object_list(value: object, field: str) -> list[dict[str, object]]:
    values = as_list(value, field)
    if not all(isinstance(item, dict) for item in values):
        raise ValueError(f"every {field} item must be an object")
    return [item for item in values if isinstance(item, dict)]
