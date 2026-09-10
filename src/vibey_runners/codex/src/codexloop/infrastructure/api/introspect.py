# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Discover endpoint-backed methods on the OpenAI SDK resource class tree.

Walks ``cached_property`` subresources on resource classes — no live client
or credentials required. See architecture §15 / R11.
"""

from __future__ import annotations

import importlib
import inspect
from dataclasses import dataclass
from functools import cached_property
from typing import Any

import openai
import openai.resources as resources
from openai import OpenAI
from openai._resource import SyncAPIResource

SDK_VERSION = openai.__version__

SKIP_RESOURCE_PROPS = frozenset(
    {
        "with_raw_response",
        "with_streaming_response",
        "with_options",
        "auth_headers",
        "default_headers",
        "qs",
        "copy",
    }
)
SKIP_METHOD_NAMES = frozenset({"with_raw_response", "with_streaming_response"})

# SDK helpers with no plain HTTP endpoint — still exposed as CLI commands but
# enumerated explicitly so the drift gate cannot silently forget them.
LOCAL_HELPER_PATHS = frozenset(
    {
        "chat.completions.parse",
        "chat.completions.stream",
        "responses.parse",
        "responses.stream",
        "beta.chat.completions.parse",
        "beta.chat.completions.stream",
        "beta.threads.runs.create_and_stream",
        "beta.threads.runs.stream",
        "beta.threads.runs.submit_tool_outputs_stream",
        "beta.threads.create_and_run_stream",
        "webhooks.unwrap",
        "webhooks.verify_signature",
    }
)


@dataclass(frozen=True, slots=True)
class EndpointSpec:
    """One discovered SDK method under ``openai.resources``."""

    resource_path: tuple[str, ...]
    method_name: str
    signature: str
    is_list: bool
    is_streaming: bool
    path: str = ""
    is_local_helper: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", ".".join((*self.resource_path, self.method_name)))
        object.__setattr__(self, "is_local_helper", self.path in LOCAL_HELPER_PATHS)


def _resolve_annotation_class(
    owner_cls: type,
    prop_name: str,
    annotation: str,
    *,
    globals_ns: dict[str, Any],
) -> type[SyncAPIResource] | None:
    ret: Any = globals_ns.get(annotation)
    if ret is None:
        ret = getattr(resources, annotation, None)
    if ret is None:
        owner_mod = owner_cls.__module__
        parent_pkg = owner_mod.rsplit(".", 1)[0]
        candidates = (
            f"openai.resources.{prop_name}",
            f"{parent_pkg}.{prop_name}",
            f"{parent_pkg}.{prop_name}.{prop_name}",
            f"openai.resources.{prop_name}.{prop_name}",
        )
        for cand in candidates:
            try:
                mod = importlib.import_module(cand)
            except ImportError:  # pragma: no cover — try next candidate
                continue
            if hasattr(mod, annotation):  # pragma: no branch
                ret = getattr(mod, annotation)
                break
    if (
        ret is None or not inspect.isclass(ret) or not issubclass(ret, SyncAPIResource)
    ):  # pragma: no cover
        return None
    return ret


def _resolve_subresource_class(
    owner_cls: type,
    prop_name: str,
) -> type[SyncAPIResource] | None:
    prop = None
    for base in owner_cls.__mro__:
        if prop_name in base.__dict__:  # pragma: no branch
            prop = base.__dict__[prop_name]
            break
    if not isinstance(prop, cached_property):  # pragma: no cover
        return None
    ann = prop.func.__annotations__.get("return")
    if isinstance(ann, type) and issubclass(
        ann, SyncAPIResource
    ):  # pragma: no cover — live type ann
        return ann
    if not isinstance(ann, str):  # pragma: no cover
        return None
    return _resolve_annotation_class(
        owner_cls,
        prop_name,
        ann,
        globals_ns=dict(prop.func.__globals__),
    )


def _iter_public_members(cls: type) -> list[tuple[str, Any]]:
    """Walk SyncAPIResource MRO so empty re-export subclasses still expose methods."""
    seen: set[str] = set()
    members: list[tuple[str, Any]] = []
    for base in cls.__mro__:  # pragma: no branch — SyncAPIResource always terminates walk
        if base is SyncAPIResource or base is object:
            break
        if not issubclass(base, SyncAPIResource):  # pragma: no cover
            continue
        for name, val in base.__dict__.items():
            if name.startswith("_") or name in seen:
                continue
            seen.add(name)
            members.append((name, val))
    return members


def _is_streaming_name(name: str) -> bool:
    return name == "stream" or name.endswith("_stream") or "stream" in name.split("_")


def _walk_resource(cls: type[SyncAPIResource], prefix: tuple[str, ...]) -> list[EndpointSpec]:
    discovered: list[EndpointSpec] = []
    for name, val in _iter_public_members(cls):
        if isinstance(val, cached_property):
            if name in SKIP_RESOURCE_PROPS:  # pragma: no cover
                continue
            sub = _resolve_subresource_class(cls, name)
            if sub is not None:  # pragma: no branch
                discovered.extend(_walk_resource(sub, prefix + (name,)))
            continue
        if not callable(val) or isinstance(val, (classmethod, staticmethod)):  # pragma: no cover
            continue
        if name in SKIP_METHOD_NAMES:  # pragma: no cover
            continue
        try:
            sig = inspect.signature(val)
        except (TypeError, ValueError):  # pragma: no cover
            continue
        if "self" not in sig.parameters:  # pragma: no cover
            continue
        discovered.append(
            EndpointSpec(
                resource_path=prefix,
                method_name=name,
                signature=str(sig),
                is_list=name == "list",
                is_streaming=_is_streaming_name(name),
            )
        )
    return discovered


def _root_resources(
    client_cls: type = OpenAI,
) -> tuple[tuple[str, type[SyncAPIResource]], ...]:
    roots: list[tuple[str, type[SyncAPIResource]]] = []
    seen: set[str] = set()
    for base in client_cls.__mro__:
        for name, val in base.__dict__.items():
            if name in seen or name.startswith("_") or name in SKIP_RESOURCE_PROPS:
                continue
            if not isinstance(val, cached_property):  # pragma: no cover
                continue
            seen.add(name)
            sub = _resolve_subresource_class(base, name)
            if sub is not None:  # pragma: no branch
                roots.append((name, sub))
    return tuple(roots)


def discover_surface(
    *,
    roots: tuple[str, ...] | None = None,
    client_cls: type = OpenAI,
) -> tuple[EndpointSpec, ...]:
    """Return every SDK method under the given top-level resource roots."""
    allowed = frozenset(roots) if roots is not None else None
    methods: list[EndpointSpec] = []
    for root_name, root_cls in _root_resources(client_cls):
        if allowed is not None and root_name not in allowed:
            continue
        methods.extend(_walk_resource(root_cls, (root_name,)))
    return tuple(sorted(methods, key=lambda m: m.path))


def method_by_path(methods: tuple[EndpointSpec, ...]) -> dict[str, EndpointSpec]:
    return {m.path: m for m in methods}


def resolve_callable(method: EndpointSpec, *, client_cls: type = OpenAI) -> Any:
    """Resolve the unbound SDK method function for a discovered path."""
    if not method.resource_path:
        msg = f"empty resource path for {method.path!r}"
        raise RuntimeError(msg)
    cls: type[SyncAPIResource] | None = None
    for root_name, root_cls in _root_resources(client_cls):
        if method.resource_path[0] == root_name:
            cls = root_cls
            break
    if cls is None:
        msg = f"unknown root resource in {method.path!r}"
        raise RuntimeError(msg)
    for segment in method.resource_path[1:]:
        sub = _resolve_subresource_class(cls, segment)
        if sub is None:  # pragma: no cover — malformed EndpointSpec
            msg = f"cannot resolve subresource {segment!r} on {cls!r}"
            raise RuntimeError(msg)
        cls = sub
    for base in cls.__mro__:
        if base is SyncAPIResource or base is object:  # pragma: no cover — always return earlier
            break
        fn = base.__dict__.get(method.method_name)
        if callable(fn) and not isinstance(fn, (classmethod, staticmethod)):
            return fn
    msg = f"method {method.method_name!r} not found on {cls!r}"  # pragma: no cover
    raise RuntimeError(msg)  # pragma: no cover
