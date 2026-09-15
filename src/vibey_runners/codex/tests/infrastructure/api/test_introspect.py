# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Unit tests for OpenAI SDK introspection (no credentials)."""

from __future__ import annotations

import os

from codexloop.infrastructure.api.introspect import (
    LOCAL_HELPER_PATHS,
    discover_surface,
    resolve_callable,
)


def test_discover_surface_works_without_api_key(monkeypatch: object) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)  # type: ignore[attr-defined]
    assert "OPENAI_API_KEY" not in os.environ
    paths = {m.path for m in discover_surface()}
    assert "chat.completions.create" in paths
    assert "models.list" in paths
    assert "responses.create" in paths
    assert "embeddings.create" in paths


def test_local_helper_paths_are_marked() -> None:
    by_path = {m.path: m for m in discover_surface()}
    for helper in LOCAL_HELPER_PATHS:
        assert by_path[helper].is_local_helper


def test_resolve_callable_finds_chat_completions_create() -> None:
    method = next(m for m in discover_surface() if m.path == "chat.completions.create")
    fn = resolve_callable(method)
    assert fn.__name__ == "create"
