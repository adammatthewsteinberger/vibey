# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Discovery-document surface for the generated Gemini REST CLI."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from typing import Any, Literal

ApiLane = Literal["developer", "vertex"]

DISCOVERY_URL = "https://generativelanguage.googleapis.com/$discovery/rest?version=v1beta"
OPENAPI_URL = "https://generativelanguage.googleapis.com/$discovery/OPENAPI3_0?version=v1beta"
VERTEX_DISCOVERY_URL = "https://aiplatform.googleapis.com/$discovery/rest?version=v1"


@dataclass(frozen=True, slots=True)
class DiscoveredMethod:
    path: str
    http_method: str
    http_path: str
    method_id: str
    lane: ApiLane = "developer"


def parse_api_lane(value: str) -> ApiLane:
    key = value.strip().lower()
    if key == "developer":
        return "developer"
    if key == "vertex":
        return "vertex"
    raise ValueError(f"unknown API lane {value!r}; expected 'developer' or 'vertex'")


def load_baseline(*, lane: ApiLane = "developer") -> dict[str, Any]:
    pkg = resources.files("agyloop.infrastructure.api")
    name = "vertex_baseline.json" if lane == "vertex" else "surface_baseline.json"
    data = json.loads(pkg.joinpath(name).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"baseline {name} must be a JSON object")
    return data


def discover_surface(*, lane: ApiLane = "developer") -> list[DiscoveredMethod]:
    """Return the committed discovery inventory for ``lane`` (no live fetch)."""
    baseline = load_baseline(lane=lane)
    methods: list[DiscoveredMethod] = []
    details = baseline.get("details") or []
    if details:
        for item in details:
            methods.append(
                DiscoveredMethod(
                    path=str(item["path"]),
                    http_method=str(item.get("httpMethod") or "POST"),
                    http_path=str(item.get("httpPath") or ""),
                    method_id=str(item.get("id") or item["path"]),
                    lane=lane,
                )
            )
        return methods
    for path in baseline.get("methods") or []:
        methods.append(
            DiscoveredMethod(
                path=str(path),
                http_method="POST",
                http_path="",
                method_id=str(path),
                lane=lane,
            )
        )
    return methods
