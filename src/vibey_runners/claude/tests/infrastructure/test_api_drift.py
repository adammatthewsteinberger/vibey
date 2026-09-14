# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Drift gate: every SDK endpoint must have a generated ``claudeloop api`` command."""

from __future__ import annotations

import json
from importlib import resources

from claudeloop.bootstrap import build_api_click_group
from claudeloop.infrastructure.api.introspect import LOCAL_HELPER_PATHS, discover_surface
from claudeloop.infrastructure.api.registry import REGISTERED_COMMAND_PATHS


def _load_baseline() -> dict[str, object]:
    pkg = resources.files("claudeloop.infrastructure.api")
    text = pkg.joinpath("surface_baseline.json").read_text(encoding="utf-8")
    return json.loads(text)


def test_discovered_count_matches_committed_baseline() -> None:
    baseline = _load_baseline()
    discovered = discover_surface()
    assert len(discovered) == baseline["method_count"]
    assert {m.path for m in discovered} == set(baseline["methods"])  # type: ignore[arg-type]


def test_local_helpers_are_explicitly_enumerated() -> None:
    discovered = {m.path for m in discover_surface() if m.is_local_helper}
    assert discovered == set(LOCAL_HELPER_PATHS)


def test_every_discovered_method_is_registered_on_the_cli() -> None:
    build_api_click_group()
    discovered = {m.path for m in discover_surface()}
    assert discovered == REGISTERED_COMMAND_PATHS


def test_hiding_one_method_from_registry_fails_drift_gate() -> None:
    build_api_click_group()
    discovered = {m.path for m in discover_surface()}
    assert discovered - REGISTERED_COMMAND_PATHS == set()
