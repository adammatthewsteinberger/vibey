# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Invoke generated ``claudeloop api`` commands against the Anthropic SDK."""

from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any

from anthropic import Omit

from claudeloop.infrastructure.api.introspect import (
    LOCAL_HELPER_PATHS,
    DiscoveredMethod,
    resolve_callable,
)
from claudeloop.infrastructure.api.json_io import load_json_payload
from claudeloop.infrastructure.api.params import build_call_kwargs
from claudeloop.infrastructure.api.providers import build_client, surface_roots_for_provider


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
    items: list[Any] = list(getattr(first_page, "data", first_page) or [])
    page = first_page
    while getattr(page, "has_more", False):
        if max_items is not None and len(items) >= max_items:
            break
        page = page.get_next_page()
        items.extend(page.data)
    if max_items is not None:
        items = items[:max_items]
    return items


class AnthropicApiGateway:
    """Concrete ``ApiGateway`` adapter for the generated REST surface."""

    def invoke(
        self,
        method_path: str,
        *,
        provider: str = "first-party",
        json_body: str | None = None,
        json_file: Path | None = None,
        raw: bool = False,
        stream: bool = False,
        max_items: int | None = None,
        scalar_values: dict[str, Any] | None = None,
        method: DiscoveredMethod | None = None,
    ) -> Any:
        if method is None:
            segments = method_path.split(".")
            method = DiscoveredMethod(
                path=method_path,
                resource_path=tuple(segments[:-1]),
                method_name=segments[-1],
                qualname=method_path,
                is_local_helper=method_path in LOCAL_HELPER_PATHS,
                is_list=segments[-1] == "list",
            )
        roots = surface_roots_for_provider(provider)
        if method.path.split(".", 1)[0] not in roots:
            msg = f"method {method.path!r} is not available for provider {provider!r}"
            raise ValueError(msg)

        client = build_client(provider)
        payload = load_json_payload(inline=json_body, json_file=json_file)
        fn = resolve_callable(method)
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


def default_gateway() -> AnthropicApiGateway:
    return AnthropicApiGateway()
