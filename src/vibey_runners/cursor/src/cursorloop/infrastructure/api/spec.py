# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Load and digest-assert the vendored Cloud Agents OpenAPI document."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml

from cursorloop.infrastructure.api.registry import SPEC_PATH, VENDORED_SPEC_DIGEST


class SpecDigestMismatchError(RuntimeError):
    """Vendored bytes no longer match the pinned SHA-256."""


def spec_bytes(path: Path = SPEC_PATH) -> bytes:
    return path.read_bytes()


def digest_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def assert_vendored_digest(path: Path = SPEC_PATH) -> str:
    digest = digest_of(spec_bytes(path))
    if digest != VENDORED_SPEC_DIGEST:
        raise SpecDigestMismatchError(
            f"vendored OpenAPI digest {digest} != pinned {VENDORED_SPEC_DIGEST}"
        )
    return digest


def load_spec(path: Path = SPEC_PATH) -> dict[str, Any]:
    assert_vendored_digest(path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("OpenAPI root must be a mapping")
    return raw


def operation_ids(spec: dict[str, Any] | None = None) -> frozenset[str]:
    document = spec if spec is not None else load_spec()
    found: set[str] = set()
    paths = document.get("paths", {})
    if not isinstance(paths, dict):
        return frozenset()
    for path_item in paths.values():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method.startswith("x-") or not isinstance(operation, dict):
                continue
            op_id = operation.get("operationId")
            if isinstance(op_id, str) and op_id:
                found.add(op_id)
    return frozenset(found)
