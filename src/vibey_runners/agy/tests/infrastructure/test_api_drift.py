# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Drift gate: every discovery method has a generated ``agyloop api`` command."""

from __future__ import annotations

from agyloop.bootstrap import build_api_click_group
from agyloop.infrastructure.api.discover import discover_surface, load_baseline
from agyloop.infrastructure.api.registry import REGISTERED_COMMAND_PATHS, REGISTERED_VERTEX_PATHS


def test_discovered_count_matches_committed_baseline() -> None:
    baseline = load_baseline()
    discovered = discover_surface()
    assert len(discovered) == baseline["method_count"]
    assert {item.path for item in discovered} == set(baseline["methods"])
    assert baseline["method_count"] == 84
    assert baseline["openapi_operation_count"] == 91
    assert baseline["method_count"] != baseline["openapi_operation_count"]
    assert baseline["revision"] == "20260812"


def test_every_discovered_method_is_registered_on_the_cli() -> None:
    build_api_click_group()
    discovered = {item.path for item in discover_surface()}
    assert discovered == REGISTERED_COMMAND_PATHS


def test_vertex_lane_is_inventoried_and_disjoint() -> None:
    baseline = load_baseline(lane="vertex")
    discovered = discover_surface(lane="vertex")
    assert baseline["method_count"] == 33
    assert baseline["revision"] == "20260801"
    assert len(discovered) == 33
    developer = {item.path for item in discover_surface(lane="developer")}
    vertex = {item.path for item in discovered}
    assert developer.isdisjoint(vertex)
    assert vertex == REGISTERED_VERTEX_PATHS


def test_hiding_one_method_from_registry_fails_drift_gate() -> None:
    build_api_click_group()
    discovered = {item.path for item in discover_surface()}
    hidden = next(iter(discovered))
    REGISTERED_COMMAND_PATHS.discard(hidden)
    assert discovered - REGISTERED_COMMAND_PATHS == {hidden}
