# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Invoke generated ``codexloop api`` commands against the OpenAI SDK."""

from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any

from openai import Omit

from codexloop.infrastructure.api.introspect import (
    LOCAL_HELPER_PATHS,
    EndpointSpec,
    discover_surface,
    resolve_callable,
)
from codexloop.infrastructure.api.json_io import load_json_payload
from codexloop.infrastructure.api.params import build_call_kwargs
from codexloop.infrastructure.api.providers import (
    build_client,
    client_class_for_provider,
    surface_roots_for_provider,
)


def _serialize(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "read"):
        return {"stream": "<streaming response>"}
    if isinstance(value, (list, tuple)):
        return [_serialize(v) for v in value]
    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}
    return value


def _navigate_resource(client: Any, resource_path: tuple[str, ...]) -> Any:
    resource: Any = client
    for segment in resource_path:
        resource = getattr(resource, segment)
    return resource


def _collect_paginated(
    first_page: Any,
    *,
    max_items: int | None,
) -> list[Any]:
    data = getattr(first_page, "data", first_page)
    items: list[Any] = list(data or []) if not isinstance(data, list) else list(data)
    page = first_page
    while getattr(page, "has_more", False):
        if max_items is not None and len(items) >= max_items:
            break
        page = page.get_next_page()
        items.extend(page.data)
    if max_items is not None:
        items = items[:max_items]
    return items


class OpenAIApiGateway:
    """Concrete adapter for the generated REST surface."""

    def invoke(
        self,
        method_path: str,
        *,
        provider: str = "openai",
        base_url: str | None = None,
        json_body: str | None = None,
        json_file: Path | None = None,
        raw: bool = False,
        stream: bool = False,
        max_items: int | None = None,
        scalar_values: dict[str, Any] | None = None,
        method: EndpointSpec | None = None,
    ) -> Any:
        client_cls = client_class_for_provider(provider)
        if method is None:
            segments = method_path.split(".")
            method = EndpointSpec(
                resource_path=tuple(segments[:-1]),
                method_name=segments[-1],
                signature="",
                is_list=segments[-1] == "list",
                is_streaming=False,
            )
        roots = surface_roots_for_provider(provider)
        if roots is not None:
            allowed = {m.path for m in discover_surface(roots=roots, client_cls=client_cls)}
            if method.path not in allowed:
                msg = f"method {method.path!r} is not available for provider {provider!r}"
                raise ValueError(msg)

        client = build_client(provider, base_url=base_url)
        payload = load_json_payload(inline=json_body, json_file=json_file)
        fn = resolve_callable(method, client_cls=client_cls)
        signature = inspect.signature(fn)
        kwargs = build_call_kwargs(
            signature,
            json_payload=payload,
            scalar_values=scalar_values or {},
        )
        cleaned = {k: v for k, v in kwargs.items() if v is not None and not isinstance(v, Omit)}

        resource = _navigate_resource(client, method.resource_path)
        if raw:
            resource = resource.with_raw_response
        elif stream:
            resource = resource.with_streaming_response
        bound = getattr(resource, method.method_name)
        result = bound(**cleaned)

        if not raw and not stream and method.is_list and max_items is not None:
            return _collect_paginated(result, max_items=max_items)
        return result

    def invoke_and_print(
        self,
        method_path: str,
        **options: Any,
    ) -> str:
        result = self.invoke(method_path, **options)
        if hasattr(result, "read"):
            text = result.read()
            return text.decode() if isinstance(text, bytes) else str(text)
        return json.dumps(_serialize(result), indent=2, default=str)


def default_gateway() -> OpenAIApiGateway:
    return OpenAIApiGateway()


# Re-export for callers that need helper membership checks without importing introspect.
__all__ = [
    "LOCAL_HELPER_PATHS",
    "OpenAIApiGateway",
    "default_gateway",
]
