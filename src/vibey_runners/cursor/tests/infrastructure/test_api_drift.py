# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

import hashlib
from pathlib import Path

import httpx
import pytest

from cursorloop.infrastructure.api import gateway as gateway_mod
from cursorloop.infrastructure.api.registry import (
    REGISTERED_OPERATIONS,
    VENDORED_SPEC_DIGEST,
)
from cursorloop.infrastructure.api.spec import (
    SpecDigestMismatchError,
    assert_vendored_digest,
    load_spec,
    operation_ids,
    spec_bytes,
)


def test_vendored_spec_digest_matches() -> None:
    assert assert_vendored_digest() == VENDORED_SPEC_DIGEST
    assert hashlib.sha256(spec_bytes()).hexdigest() == VENDORED_SPEC_DIGEST


def test_every_operation_is_registered() -> None:
    found = operation_ids(load_spec())
    assert found == REGISTERED_OPERATIONS
    # Removals must fail: count is part of the contract.
    assert len(found) == 6


def test_digest_mismatch_raises(tmp_path: Path) -> None:
    path = tmp_path / "broken.yaml"
    path.write_text("openapi: 3.0.3\ninfo: {title: x, version: '0'}\npaths: {}\n", encoding="utf-8")
    with pytest.raises(SpecDigestMismatchError):
        assert_vendored_digest(path)


def test_gateway_bearer_and_redaction() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer test-key"
        return httpx.Response(
            200,
            json={"email": "a@b.c", "api_key": "sk-secret-should-redact"},
        )

    transport = httpx.MockTransport(handler)
    client = httpx.Client(base_url="https://api.cursor.com", transport=transport)
    with gateway_mod.CloudAgentsGateway(api_key="test-key", client=client) as gw:
        data = gw.invoke("GET", "/v1/me")
    assert data["api_key"] == "***"
    assert data["email"] == "a@b.c"
