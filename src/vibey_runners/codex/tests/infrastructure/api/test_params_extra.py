# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Extra coverage for API params helpers."""

from __future__ import annotations

import inspect

from openai import NotGiven, Omit

from codexloop.infrastructure.api.params import (
    build_call_kwargs,
    is_scalar_annotation,
    typer_type_for_annotation,
)

_OMIT = Omit()
_NOT_GIVEN = NotGiven()


def test_union_and_optional_normalization() -> None:
    assert is_scalar_annotation(int | None)
    assert is_scalar_annotation(str | Omit)
    assert typer_type_for_annotation("bool") is bool
    assert typer_type_for_annotation("float") is float


def test_build_call_kwargs_merges_scalars_and_skips_none() -> None:
    def sample(
        self,
        model: str,
        n: int | Omit = _OMIT,
        extra_headers: object | None = None,
    ) -> None:
        del self, model, n, extra_headers

    kwargs = build_call_kwargs(
        inspect.signature(sample),
        json_payload={"model": "gpt"},
        scalar_values={"n": None},
    )
    assert kwargs == {"model": "gpt"}


def test_not_given_default_is_omit_like() -> None:
    def sample(self, timeout: float | NotGiven = _NOT_GIVEN) -> None:
        del self, timeout

    kwargs = build_call_kwargs(
        inspect.signature(sample),
        json_payload={},
        scalar_values={"timeout": 1.5},
    )
    assert kwargs["timeout"] == 1.5


def test_normalize_string_forms_and_defaults() -> None:
    from codexloop.infrastructure.api import params as p

    assert p._normalize_annotation("Optional[int]") is int
    assert p._normalize_annotation("None | str") is str
    assert p._normalize_annotation("Omit | float") is float
    assert p._normalize_annotation("int | Omit") is int
    assert p._normalize_annotation("list[str] | None") == "list[str] | None"
    assert p._normalize_annotation(int | str) == (int | str)
    assert p.is_scalar_annotation(inspect.Parameter.empty) is False
    assert p.is_scalar_annotation("mystery") is False
    assert p.is_scalar_annotation("int") is True
    assert p.is_scalar_annotation(list[str]) is False
    assert p.is_scalar_annotation(object) is False
    assert p.typer_type_for_annotation("int") is int

    def sample(self, n: int = 3, extra_headers: object | None = None) -> None:
        del self, n, extra_headers

    kwargs = p.build_call_kwargs(
        inspect.signature(sample),
        json_payload={},
        scalar_values={},
    )
    assert kwargs["n"] == 3
