# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Unit tests for OpenAIApiGateway (no network)."""

from __future__ import annotations

from typing import Any

import pytest

from codexloop.infrastructure.api.gateway import OpenAIApiGateway, _collect_paginated
from codexloop.infrastructure.api.introspect import EndpointSpec


class _FakePage:
    def __init__(
        self,
        data: list[Any],
        *,
        has_more: bool = False,
        next_data: list[Any] | None = None,
    ) -> None:
        self.data = data
        self.has_more = has_more
        self._next_data = next_data or []

    def get_next_page(self) -> _FakePage:
        return _FakePage(self._next_data, has_more=False)


class _FakeModels:
    def list(self, **kwargs: Any) -> _FakePage:
        del kwargs
        return _FakePage([{"id": "a"}, {"id": "b"}], has_more=True, next_data=[{"id": "c"}])


class _FakeClient:
    def __init__(self) -> None:
        self.models = _FakeModels()


def test_invoke_paginates_list(monkeypatch: pytest.MonkeyPatch) -> None:
    gw = OpenAIApiGateway()
    monkeypatch.setattr(
        "codexloop.infrastructure.api.gateway.build_client",
        lambda *a, **k: _FakeClient(),
    )
    method = EndpointSpec(
        resource_path=("models",),
        method_name="list",
        signature="(self)",
        is_list=True,
        is_streaming=False,
    )
    result = gw.invoke("models.list", method=method, max_items=2)
    assert result == [{"id": "a"}, {"id": "b"}]


def test_collect_paginated_without_cap() -> None:
    page = _FakePage([1], has_more=True, next_data=[2, 3])
    assert _collect_paginated(page, max_items=None) == [1, 2, 3]


def test_collect_paginated_non_list_data() -> None:
    class _Page:
        data = None
        has_more = False

    assert _collect_paginated(_Page(), max_items=1) == []


def test_invoke_rejects_disallowed_root(monkeypatch: pytest.MonkeyPatch) -> None:
    gw = OpenAIApiGateway()
    monkeypatch.setattr(
        "codexloop.infrastructure.api.gateway.surface_roots_for_provider",
        lambda provider: ("models",),
    )
    monkeypatch.setattr(
        "codexloop.infrastructure.api.gateway.discover_surface",
        lambda **k: [
            EndpointSpec(
                resource_path=("models",),
                method_name="list",
                signature="(self)",
                is_list=True,
                is_streaming=False,
            )
        ],
    )
    with pytest.raises(ValueError, match="not available"):
        gw.invoke("chat.completions.create", provider="openai")


def test_invoke_and_print_json(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Obj:
        def model_dump(self) -> dict[str, str]:
            return {"ok": "yes"}

    class _Retrieve:
        def retrieve(self, model: str, **kwargs: Any) -> _Obj:
            del kwargs
            assert model == "gpt"
            return _Obj()

    class _Client:
        def __init__(self) -> None:
            self.models = _Retrieve()

    gw = OpenAIApiGateway()
    monkeypatch.setattr(
        "codexloop.infrastructure.api.gateway.build_client",
        lambda *a, **k: _Client(),
    )
    method = EndpointSpec(
        resource_path=("models",),
        method_name="retrieve",
        signature="(self, model: str)",
        is_list=False,
        is_streaming=False,
    )
    text = gw.invoke_and_print(
        "models.retrieve",
        method=method,
        scalar_values={"model": "gpt"},
    )
    assert '"ok"' in text
    assert "yes" in text


def test_gateway_rejects_method_outside_provider_roots(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "codexloop.infrastructure.api.gateway.surface_roots_for_provider",
        lambda provider: ("chat",),
    )
    gw = OpenAIApiGateway()
    with pytest.raises(ValueError, match="not available"):
        gw.invoke("models.list", provider="openai")


def test_gateway_allows_method_inside_restricted_roots(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _List:
        def list(self, **kwargs: Any) -> list[str]:
            del kwargs
            return ["ok"]

    class _Client:
        def __init__(self) -> None:
            self.models = _List()

    monkeypatch.setattr(
        "codexloop.infrastructure.api.gateway.surface_roots_for_provider",
        lambda provider: ("models",),
    )
    monkeypatch.setattr(
        "codexloop.infrastructure.api.gateway.discover_surface",
        lambda **k: [
            EndpointSpec(
                resource_path=("models",),
                method_name="list",
                signature="(self)",
                is_list=True,
                is_streaming=False,
            )
        ],
    )
    monkeypatch.setattr(
        "codexloop.infrastructure.api.gateway.build_client",
        lambda *a, **k: _Client(),
    )
    monkeypatch.setattr(
        "codexloop.infrastructure.api.gateway.resolve_callable",
        lambda method, client_cls=None: _List.list,
    )
    gw = OpenAIApiGateway()
    method = EndpointSpec(
        resource_path=("models",),
        method_name="list",
        signature="(self)",
        is_list=True,
        is_streaming=False,
    )
    assert gw.invoke("models.list", method=method) == ["ok"]


def test_collect_paginated_stops_at_max_items() -> None:
    page = _FakePage([1, 2], has_more=True, next_data=[3, 4])
    assert _collect_paginated(page, max_items=3) == [1, 2, 3]
