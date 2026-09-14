# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Unit tests for AnthropicApiGateway helpers and invoke edge cases."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from claudeloop.infrastructure.api.gateway import (
    AnthropicApiGateway,
    _collect_paginated,
    _serialize,
)
from claudeloop.infrastructure.api.introspect import DiscoveredMethod


@dataclass
class _Model:
    value: str

    def model_dump(self) -> dict[str, str]:
        return {"value": self.value}


class _Stream:
    def read(self) -> bytes:
        return b"chunk"


class _Page:
    def __init__(
        self, data: list[Any], *, has_more: bool, next_data: list[Any] | None = None
    ) -> None:
        self.data = data
        self.has_more = has_more
        self._next_data = next_data or []

    def get_next_page(self) -> _Page:
        return _Page(self._next_data, has_more=False)


def test_serialize_model_dump_stream_and_nested_containers() -> None:
    assert _serialize(_Model("x")) == {"value": "x"}
    assert _serialize(_Stream()) == {"stream": "<streaming response>"}
    assert _serialize([_Model("a"), {"k": _Model("b")}]) == [
        {"value": "a"},
        {"k": {"value": "b"}},
    ]
    assert _serialize(7) == 7


def test_collect_paginated_honors_max_items_across_pages() -> None:
    first = _Page(["a", "b"], has_more=True, next_data=["c", "d", "e"])
    assert _collect_paginated(first, max_items=3) == ["a", "b", "c"]
    first_again = _Page(["a", "b"], has_more=True, next_data=["c", "d"])
    assert _collect_paginated(first_again, max_items=None) == ["a", "b", "c", "d"]


def test_invoke_rejects_method_outside_provider_surface() -> None:
    gateway = AnthropicApiGateway()
    method = DiscoveredMethod(
        path="models.list",
        resource_path=("models",),
        method_name="list",
        qualname="models.list",
        is_local_helper=False,
        is_list=True,
    )
    with pytest.raises(ValueError, match="not available for provider"):
        gateway.invoke("models.list", provider="bedrock", method=method)


def test_navigate_resource() -> None:
    from types import SimpleNamespace

    from claudeloop.infrastructure.api.gateway import _navigate_resource

    # Create nested mock client structure
    client = SimpleNamespace()
    client.messages = SimpleNamespace()
    client.messages.create = lambda: "created"

    result = _navigate_resource(client, ("messages",))
    assert hasattr(result, "create")
    assert result.create() == "created"

    result_nested = _navigate_resource(client, ("messages", "create"))
    assert result_nested() == "created"


def test_collect_paginated_stops_early_when_max_items_reached() -> None:
    """Cover the break statement when max_items is hit mid-page."""
    first = _Page(["a", "b"], has_more=True, next_data=["c"])
    # Request only 2 items, should stop before fetching next page
    result = _collect_paginated(first, max_items=2)
    assert result == ["a", "b"]


def test_collect_paginated_with_data_attribute_none() -> None:
    """Cover the 'or []' fallback when page.data is None."""

    class _PageNone:
        data = None
        has_more = False

    result = _collect_paginated(_PageNone(), max_items=None)
    assert result == []


def test_invoke_with_method_none_auto_discovers() -> None:
    """Test invoke when method parameter is None - auto-discovery path."""
    from unittest.mock import MagicMock, patch

    gateway = AnthropicApiGateway()

    with (
        patch("claudeloop.infrastructure.api.gateway.build_client") as mock_client,
        patch("claudeloop.infrastructure.api.gateway.resolve_callable") as mock_resolve,
        patch("claudeloop.infrastructure.api.gateway.load_json_payload") as mock_load,
    ):
        # Set up mocks with proper signature
        mock_load.return_value = {}

        def mock_fn() -> dict:
            return {}

        mock_resolve.return_value = mock_fn

        client_mock = MagicMock()
        client_mock.messages.create.return_value = {"id": "msg_123"}
        mock_client.return_value = client_mock

        # Call without method parameter - should auto-discover
        result = gateway.invoke("messages.create", method=None, json_body="{}")

        assert mock_resolve.called
        assert result == {"id": "msg_123"}


def test_invoke_with_json_body() -> None:
    """Test invoke with inline json_body parameter."""
    from unittest.mock import MagicMock, patch

    gateway = AnthropicApiGateway()
    method = DiscoveredMethod(
        path="messages.create",
        resource_path=("messages",),
        method_name="create",
        qualname="messages.create",
        is_local_helper=False,
        is_list=False,
    )

    with (
        patch("claudeloop.infrastructure.api.gateway.build_client") as mock_client,
        patch("claudeloop.infrastructure.api.gateway.resolve_callable") as mock_resolve,
        patch("claudeloop.infrastructure.api.gateway.load_json_payload") as mock_load,
        patch("claudeloop.infrastructure.api.gateway.build_call_kwargs") as mock_kwargs,
    ):
        mock_load.return_value = {"model": "claude-3-sonnet-20240620"}
        mock_kwargs.return_value = {"model": "claude-3-sonnet-20240620"}

        def mock_fn(model: str) -> dict:
            return {}

        mock_resolve.return_value = mock_fn

        client_mock = MagicMock()
        client_mock.messages.create.return_value = {"id": "msg_456"}
        mock_client.return_value = client_mock

        body = '{"model": "claude-3-sonnet-20240620"}'
        result = gateway.invoke(
            "messages.create",
            method=method,
            json_body=body,
        )

        mock_load.assert_called_once_with(
            inline=body,
            json_file=None,
        )
        assert result == {"id": "msg_456"}


def test_invoke_with_raw_response() -> None:
    """Test invoke with raw=True."""
    from unittest.mock import MagicMock, patch

    gateway = AnthropicApiGateway()
    method = DiscoveredMethod(
        path="messages.create",
        resource_path=("messages",),
        method_name="create",
        qualname="messages.create",
        is_local_helper=False,
        is_list=False,
    )

    with (
        patch("claudeloop.infrastructure.api.gateway.build_client") as mock_client,
        patch("claudeloop.infrastructure.api.gateway.resolve_callable") as mock_resolve,
        patch("claudeloop.infrastructure.api.gateway.load_json_payload") as mock_load,
        patch("claudeloop.infrastructure.api.gateway.build_call_kwargs") as mock_kwargs,
    ):
        mock_load.return_value = {}
        mock_kwargs.return_value = {}

        def mock_fn() -> dict:
            return {}

        mock_resolve.return_value = mock_fn

        client_mock = MagicMock()
        raw_resource = MagicMock()
        raw_resource.create.return_value = {"raw": True}
        client_mock.messages.with_raw_response = raw_resource
        mock_client.return_value = client_mock

        result = gateway.invoke("messages.create", method=method, raw=True)

        assert result == {"raw": True}


def test_invoke_with_streaming_response() -> None:
    """Test invoke with stream=True."""
    from unittest.mock import MagicMock, patch

    gateway = AnthropicApiGateway()
    method = DiscoveredMethod(
        path="messages.create",
        resource_path=("messages",),
        method_name="create",
        qualname="messages.create",
        is_local_helper=False,
        is_list=False,
    )

    with (
        patch("claudeloop.infrastructure.api.gateway.build_client") as mock_client,
        patch("claudeloop.infrastructure.api.gateway.resolve_callable") as mock_resolve,
        patch("claudeloop.infrastructure.api.gateway.load_json_payload") as mock_load,
        patch("claudeloop.infrastructure.api.gateway.build_call_kwargs") as mock_kwargs,
    ):
        mock_load.return_value = {}
        mock_kwargs.return_value = {}

        def mock_fn() -> dict:
            return {}

        mock_resolve.return_value = mock_fn

        client_mock = MagicMock()
        stream_resource = MagicMock()
        stream_resource.create.return_value = {"stream": True}
        client_mock.messages.with_streaming_response = stream_resource
        mock_client.return_value = client_mock

        result = gateway.invoke("messages.create", method=method, stream=True)

        assert result == {"stream": True}


def test_invoke_with_pagination() -> None:
    """Test invoke with is_list=True and max_items triggers pagination."""
    from unittest.mock import MagicMock, patch

    gateway = AnthropicApiGateway()
    method = DiscoveredMethod(
        path="messages.list",
        resource_path=("messages",),
        method_name="list",
        qualname="messages.list",
        is_local_helper=False,
        is_list=True,
    )

    with (
        patch("claudeloop.infrastructure.api.gateway.build_client") as mock_client,
        patch("claudeloop.infrastructure.api.gateway.resolve_callable") as mock_resolve,
        patch("claudeloop.infrastructure.api.gateway.load_json_payload") as mock_load,
        patch("claudeloop.infrastructure.api.gateway.build_call_kwargs") as mock_kwargs,
    ):
        mock_load.return_value = {}
        mock_kwargs.return_value = {}

        def mock_fn() -> dict:
            return {}

        mock_resolve.return_value = mock_fn

        client_mock = MagicMock()
        first_page = _Page(["item1", "item2"], has_more=True, next_data=["item3"])
        client_mock.messages.list.return_value = first_page
        mock_client.return_value = client_mock

        result = gateway.invoke("messages.list", method=method, max_items=2)

        # Should use _collect_paginated and respect max_items
        assert result == ["item1", "item2"]


def test_invoke_and_print_with_regular_result() -> None:
    """Test invoke_and_print with a regular dict result."""
    from unittest.mock import patch

    gateway = AnthropicApiGateway()

    with patch.object(gateway, "invoke") as mock_invoke:
        mock_invoke.return_value = {"id": "msg_789", "content": "Hello"}

        result = gateway.invoke_and_print("messages.create")

        import json

        parsed = json.loads(result)
        assert parsed["id"] == "msg_789"
        assert parsed["content"] == "Hello"


def test_invoke_and_print_with_streaming_result() -> None:
    """Test invoke_and_print with a streaming response (has read method)."""
    from unittest.mock import patch

    gateway = AnthropicApiGateway()

    with patch.object(gateway, "invoke") as mock_invoke:
        stream_mock = _Stream()
        mock_invoke.return_value = stream_mock

        result = gateway.invoke_and_print("messages.create", stream=True)

        assert result == "chunk"


def test_invoke_and_print_with_bytes_stream() -> None:
    """Test invoke_and_print decodes bytes from stream.read()."""
    from unittest.mock import MagicMock, patch

    gateway = AnthropicApiGateway()

    with patch.object(gateway, "invoke") as mock_invoke:
        stream_mock = MagicMock()
        stream_mock.read.return_value = b"binary data"
        mock_invoke.return_value = stream_mock

        result = gateway.invoke_and_print("messages.create")

        assert result == "binary data"
