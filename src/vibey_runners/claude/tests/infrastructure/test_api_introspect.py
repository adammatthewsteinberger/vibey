# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Unit tests for Anthropic SDK introspection (no credentials)."""

from __future__ import annotations

import pytest
from anthropic._compat import cached_property
from anthropic._resource import SyncAPIResource

from claudeloop.infrastructure.api.introspect import (
    LOCAL_HELPER_PATHS,
    DiscoveredMethod,
    _resolve_subresource_class,
    _walk_resource,
    discover_surface,
    method_by_path,
    resolve_callable,
)


def test_discover_surface_includes_core_roots() -> None:
    paths = {m.path for m in discover_surface()}
    assert "messages.create" in paths
    assert "models.list" in paths
    assert "beta.sessions.list" in paths


def test_local_helper_paths_are_marked() -> None:
    by_path = {m.path: m for m in discover_surface()}
    for helper in LOCAL_HELPER_PATHS:
        assert by_path[helper].is_local_helper


def test_resolve_callable_finds_messages_create() -> None:
    method = next(m for m in discover_surface() if m.path == "messages.create")
    fn = resolve_callable(method)
    assert fn.__name__ == "create"


class TestResolveSubresourceClass:
    def test_returns_none_for_non_cached_property(self) -> None:
        class PlainAttr(SyncAPIResource):
            regular_attr = "not a cached property"

        assert _resolve_subresource_class(PlainAttr, "regular_attr") is None

    def test_returns_none_when_no_return_hint(self) -> None:
        class NoReturnHint(SyncAPIResource):
            @cached_property
            def sub(self):  # noqa: ANN202 - deliberately unannotated
                return None

        assert _resolve_subresource_class(NoReturnHint, "sub") is None

    def test_returns_none_when_hint_is_not_a_class(self) -> None:
        class NotAClassHint(SyncAPIResource):
            @cached_property
            def sub(self) -> list[str]:
                return []

        assert _resolve_subresource_class(NotAClassHint, "sub") is None

    def test_returns_none_when_hint_is_not_a_resource_subclass(self) -> None:
        class NotSubclassHint(SyncAPIResource):
            @cached_property
            def sub(self) -> int:
                return 0

        assert _resolve_subresource_class(NotSubclassHint, "sub") is None


class TestWalkResource:
    def test_skips_non_methods_and_discovers_real_ones(self) -> None:
        class WalkTestResource(SyncAPIResource):
            not_callable_attr = "just a string"

            @cached_property
            def bad_subresource(self) -> int:
                return 0

            @staticmethod
            def static_helper() -> None:
                pass

            @classmethod
            def class_helper(cls) -> None:
                pass

            def with_raw_response(self) -> None:
                pass

            def helper_without_self() -> None:  # noqa: N805 - deliberately self-less
                pass

            def real_method(self, x: int = 0) -> None:
                pass

        discovered = _walk_resource(WalkTestResource, ("walktest",))
        paths = {m.path for m in discovered}

        assert paths == {"walktest.real_method"}


def test_discover_surface_filters_by_roots() -> None:
    methods = discover_surface(roots=("messages",))

    assert methods
    assert all(m.path.startswith("messages.") for m in methods)
    assert not any(m.path.startswith("models.") for m in methods)
    assert not any(m.path.startswith("beta.") for m in methods)


def test_method_by_path_indexes_by_path() -> None:
    methods = discover_surface(roots=("models",))
    mapping = method_by_path(methods)

    assert mapping["models.list"].path == "models.list"


class TestResolveCallableErrors:
    def test_empty_resource_path_raises(self) -> None:
        method = DiscoveredMethod(
            path="orphan",
            resource_path=(),
            method_name="orphan",
            qualname="Orphan.orphan",
            is_local_helper=False,
            is_list=False,
        )

        with pytest.raises(RuntimeError, match="empty resource path"):
            resolve_callable(method)

    def test_unknown_root_resource_raises(self) -> None:
        method = DiscoveredMethod(
            path="unknown.thing",
            resource_path=("unknown",),
            method_name="thing",
            qualname="Unknown.thing",
            is_local_helper=False,
            is_list=False,
        )

        with pytest.raises(RuntimeError, match="unknown root resource"):
            resolve_callable(method)

    def test_unresolvable_subresource_raises(self) -> None:
        method = DiscoveredMethod(
            path="messages.nonexistent_sub.create",
            resource_path=("messages", "nonexistent_sub"),
            method_name="create",
            qualname="Messages.nonexistent_sub.create",
            is_local_helper=False,
            is_list=False,
        )

        with pytest.raises(RuntimeError, match="cannot resolve subresource"):
            resolve_callable(method)

    def test_non_callable_method_raises(self) -> None:
        method = DiscoveredMethod(
            path="messages.nonexistent_method",
            resource_path=("messages",),
            method_name="nonexistent_method",
            qualname="Messages.nonexistent_method",
            is_local_helper=False,
            is_list=False,
        )

        with pytest.raises(RuntimeError, match="not found on"):
            resolve_callable(method)
