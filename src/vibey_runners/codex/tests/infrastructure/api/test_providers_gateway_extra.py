# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Broader provider and gateway coverage for the M4 surface."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import pytest

from codexloop.infrastructure.api.gateway import OpenAIApiGateway, _serialize
from codexloop.infrastructure.api.introspect import EndpointSpec, method_by_path, resolve_callable
from codexloop.infrastructure.api.providers import (
    build_client,
    client_class_for_provider,
    surface_roots_for_provider,
)


def test_serialize_nested() -> None:
    assert _serialize({"a": [1, {"b": 2}]}) == {"a": [1, {"b": 2}]}

    class _Stream:
        def read(self) -> bytes:
            return b"hi"

    assert _serialize(_Stream()) == {"stream": "<streaming response>"}


def test_azure_and_custom_clients(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.setenv("OPENAI_API_VERSION", "2024-06-01")
    azure = build_client("azure")
    assert "azure" in type(azure).__name__.lower() or hasattr(azure, "api_version")

    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.test/v1")
    custom = build_client("custom")
    assert urlparse(str(custom.base_url)).hostname == "example.test"

    with_url = build_client("openai", base_url="https://override.test/v1")
    assert "override.test" in str(with_url.base_url)


def test_unknown_provider_roots() -> None:
    with pytest.raises(ValueError, match="unknown provider"):
        surface_roots_for_provider("nope")
    with pytest.raises(ValueError, match="unknown provider"):
        client_class_for_provider("nope")


def test_method_by_path_and_resolve_errors() -> None:
    methods = method_by_path(
        (
            EndpointSpec(
                resource_path=("models",),
                method_name="list",
                signature="()",
                is_list=True,
                is_streaming=False,
            ),
        )
    )
    assert "models.list" in methods
    with pytest.raises(RuntimeError, match="empty resource path"):
        resolve_callable(
            EndpointSpec(
                resource_path=(),
                method_name="x",
                signature="()",
                is_list=False,
                is_streaming=False,
            )
        )
    with pytest.raises(RuntimeError, match="unknown root"):
        resolve_callable(
            EndpointSpec(
                resource_path=("not_a_root",),
                method_name="x",
                signature="()",
                is_list=False,
                is_streaming=False,
            )
        )


def test_gateway_raw_and_stream_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    class _Raw:
        def list(self, **kwargs: Any) -> dict[str, str]:
            del kwargs
            calls.append("raw")
            return {"mode": "raw"}

    class _Stream:
        def list(self, **kwargs: Any) -> dict[str, str]:
            del kwargs
            calls.append("stream")
            return {"mode": "stream"}

    class _Models:
        @property
        def with_raw_response(self) -> _Raw:
            return _Raw()

        @property
        def with_streaming_response(self) -> _Stream:
            return _Stream()

        def list(self, **kwargs: Any) -> list[str]:
            del kwargs
            return ["plain"]

    class _Client:
        def __init__(self) -> None:
            self.models = _Models()

    monkeypatch.setattr(
        "codexloop.infrastructure.api.gateway.build_client",
        lambda *a, **k: _Client(),
    )
    gw = OpenAIApiGateway()
    method = EndpointSpec(
        resource_path=("models",),
        method_name="list",
        signature="(self)",
        is_list=True,
        is_streaming=False,
    )
    assert gw.invoke("models.list", method=method, raw=True) == {"mode": "raw"}
    assert gw.invoke("models.list", method=method, stream=True) == {"mode": "stream"}
    assert calls == ["raw", "stream"]


def test_invoke_and_print_bytes(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Resp:
        def read(self) -> bytes:
            return b"bytes-out"

    class _Models:
        def list(self, **kwargs: Any) -> _Resp:
            del kwargs
            return _Resp()

    class _Client:
        def __init__(self) -> None:
            self.models = _Models()

    monkeypatch.setattr(
        "codexloop.infrastructure.api.gateway.build_client",
        lambda *a, **k: _Client(),
    )
    text = OpenAIApiGateway().invoke_and_print(
        "models.list",
        method=EndpointSpec(
            resource_path=("models",),
            method_name="list",
            signature="(self)",
            is_list=True,
            is_streaming=False,
        ),
    )
    assert text == "bytes-out"
