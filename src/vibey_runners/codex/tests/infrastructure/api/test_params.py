# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Unit tests for scalar parameter classification."""

from __future__ import annotations

import inspect

from codexloop.infrastructure.api.introspect import discover_surface, resolve_callable
from codexloop.infrastructure.api.params import is_scalar_annotation, scalar_parameters


def test_stringified_omit_union_is_scalar() -> None:
    assert is_scalar_annotation("int | Omit")
    assert is_scalar_annotation("str | None")


def test_files_retrieve_exposes_file_id_scalar() -> None:
    method = next(m for m in discover_surface() if m.path == "files.retrieve")
    fn = resolve_callable(method)
    scalars = {p.name for p in scalar_parameters(inspect.signature(fn))}
    assert "file_id" in scalars
