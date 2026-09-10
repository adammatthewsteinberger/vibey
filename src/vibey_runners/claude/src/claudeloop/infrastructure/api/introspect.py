# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Discover endpoint-backed methods on the anthropic SDK resource class tree.

Walks ``cached_property`` subresources on resource classes — no live client
or credentials required. See ADR 0006 and the ``claudeloop-rest-surface`` skill.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, get_type_hints

import anthropic
from anthropic._compat import cached_property
from anthropic._resource import SyncAPIResource
from anthropic.resources.beta.beta import Beta
from anthropic.resources.messages.messages import Messages
from anthropic.resources.models import Models

SDK_VERSION = anthropic.__version__

SKIP_RESOURCE_PROPS = frozenset({"with_raw_response", "with_streaming_response"})
SKIP_METHOD_NAMES = frozenset({"with_raw_response", "with_streaming_response"})

# Six SDK helpers with no HTTP endpoint — still exposed as CLI commands but
# enumerated explicitly so the drift gate cannot silently forget them.
LOCAL_HELPER_PATHS = frozenset(
    {
        "messages.stream",
        "messages.parse",
        "beta.messages.stream",
        "beta.messages.parse",
        "beta.messages.tool_runner",
        "beta.webhooks.unwrap",
    }
)

ROOT_RESOURCES: tuple[tuple[str, type[SyncAPIResource]], ...] = (
    ("messages", Messages),
    ("models", Models),
    ("beta", Beta),
)

LIMITED_PROVIDER_ROOTS: frozenset[str] = frozenset({"messages", "beta"})


@dataclass(frozen=True, slots=True)
class DiscoveredMethod:
    path: str
    resource_path: tuple[str, ...]
    method_name: str
    qualname: str
    is_local_helper: bool
    is_list: bool


def _resolve_subresource_class(
    owner_cls: type[SyncAPIResource],
    prop_name: str,
) -> type[SyncAPIResource] | None:
    prop = owner_cls.__dict__.get(prop_name)
    if not isinstance(prop, cached_property):
        return None
    hints = get_type_hints(prop.func, globalns=prop.func.__globals__)  # type: ignore[attr-defined]
    ret = hints.get("return")
    if ret is None or not inspect.isclass(ret) or not issubclass(ret, SyncAPIResource):
        return None
    return ret


def _walk_resource(
    cls: type[SyncAPIResource],
    prefix: tuple[str, ...],
) -> list[DiscoveredMethod]:
    discovered: list[DiscoveredMethod] = []
    for name, val in cls.__dict__.items():
        if name.startswith("_"):
            continue
        if isinstance(val, cached_property):
            if name in SKIP_RESOURCE_PROPS:
                continue
            sub = _resolve_subresource_class(cls, name)
            if sub is not None:
                discovered.extend(_walk_resource(sub, prefix + (name,)))
            continue
        if not callable(val) or isinstance(val, (classmethod, staticmethod)):
            continue
        if name in SKIP_METHOD_NAMES:
            continue
        sig = inspect.signature(val)
        if "self" not in sig.parameters:
            continue
        path = ".".join(prefix + (name,))
        discovered.append(
            DiscoveredMethod(
                path=path,
                resource_path=prefix,
                method_name=name,
                qualname=f"{cls.__qualname__}.{name}",
                is_local_helper=path in LOCAL_HELPER_PATHS,
                is_list=name == "list",
            )
        )
    return discovered


def discover_surface(*, roots: tuple[str, ...] | None = None) -> tuple[DiscoveredMethod, ...]:
    """Return every SDK method under the given top-level resource roots."""
    allowed = frozenset(roots) if roots is not None else None
    methods: list[DiscoveredMethod] = []
    for root_name, root_cls in ROOT_RESOURCES:
        if allowed is not None and root_name not in allowed:
            continue
        methods.extend(_walk_resource(root_cls, (root_name,)))
    return tuple(sorted(methods, key=lambda m: m.path))


def method_by_path(methods: tuple[DiscoveredMethod, ...]) -> dict[str, DiscoveredMethod]:
    return {m.path: m for m in methods}


def resolve_callable(method: DiscoveredMethod) -> Any:
    """Resolve the unbound SDK method function for a discovered path."""
    if not method.resource_path:
        msg = f"empty resource path for {method.path!r}"
        raise RuntimeError(msg)
    cls: type[SyncAPIResource] | None = None
    for root_name, root_cls in ROOT_RESOURCES:
        if method.resource_path[0] == root_name:
            cls = root_cls
            break
    if cls is None:
        msg = f"unknown root resource in {method.path!r}"
        raise RuntimeError(msg)
    for segment in method.resource_path[1:]:
        sub = _resolve_subresource_class(cls, segment)
        if sub is None:
            msg = f"cannot resolve subresource {segment!r} on {cls!r}"
            raise RuntimeError(msg)
        cls = sub
    fn = cls.__dict__.get(method.method_name)
    if not callable(fn):
        msg = f"method {method.method_name!r} not found on {cls!r}"
        raise RuntimeError(msg)
    return fn
