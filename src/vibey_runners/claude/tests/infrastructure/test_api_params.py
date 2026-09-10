# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Unit tests for generated-API parameter classification and kwargs merge."""

from __future__ import annotations

import inspect
from typing import Any

from anthropic import NotGiven, Omit

from claudeloop.infrastructure.api.introspect import discover_surface, resolve_callable
from claudeloop.infrastructure.api.params import (
    build_call_kwargs,
    click_type_for_annotation,
    is_scalar_annotation,
    scalar_parameters,
)

_OMIT = Omit()
_NOT_GIVEN = NotGiven()


def test_is_scalar_annotation_accepts_primitives_and_optionals() -> None:
    assert is_scalar_annotation(str) is True
    assert is_scalar_annotation(int) is True
    assert is_scalar_annotation(float) is True
    assert is_scalar_annotation(bool) is True
    assert is_scalar_annotation(float | None) is True
    assert is_scalar_annotation(int | None) is True
    assert is_scalar_annotation("str") is True
    assert is_scalar_annotation("bool") is True


def test_is_scalar_annotation_accepts_stringified_omit_unions() -> None:
    # Anthropic SDK methods keep annotations as strings under future annotations.
    assert is_scalar_annotation("int | Omit") is True
    assert is_scalar_annotation("str | Omit") is True
    assert is_scalar_annotation("Optional[str] | Omit") is True
    assert is_scalar_annotation("None | int") is True
    assert is_scalar_annotation("Omit | float") is True
    assert is_scalar_annotation("NotGiven | str") is True
    assert is_scalar_annotation(int | Omit) is True
    assert click_type_for_annotation("int | Omit") is int
    assert click_type_for_annotation("Omit | float") is float
    assert click_type_for_annotation("str | Omit") is str


def test_is_scalar_annotation_rejects_complex_and_empty() -> None:
    assert is_scalar_annotation(inspect.Parameter.empty) is False
    assert is_scalar_annotation(list[str]) is False
    assert is_scalar_annotation(dict[str, Any]) is False
    assert is_scalar_annotation("MessageCreateParams") is False
    assert is_scalar_annotation("float | httpx.Timeout | None | NotGiven") is False
    assert is_scalar_annotation("Literal[False] | Literal[True] | Omit") is False


def test_scalar_parameters_skips_self_and_extra_star_kwargs() -> None:
    def sample(
        self: object,
        model: str,
        max_tokens: int,
        temperature: float | None = None,
        messages: list[dict[str, str]] | None = None,
        extra_headers: dict[str, str] | None = None,
        extra_query: dict[str, str] | None = None,
        extra_body: dict[str, Any] | None = None,
        stream: bool | Omit = _OMIT,
    ) -> None:
        raise NotImplementedError

    params = scalar_parameters(inspect.signature(sample))
    names = [p.name for p in params]
    assert names == ["model", "max_tokens", "temperature", "stream"]
    assert params[0].required is True
    assert params[0].cli_name == "model"
    assert params[2].required is False
    assert params[2].cli_name == "temperature"
    # Omit defaults stay optional for the CLI (not forced required).
    assert params[3].required is False


def test_models_list_exposes_pagination_scalars_from_sdk_strings() -> None:
    method = next(m for m in discover_surface() if m.path == "models.list")
    params = scalar_parameters(inspect.signature(resolve_callable(method)))
    names = {p.name for p in params}
    assert {"after_id", "before_id", "limit"} <= names


def test_build_call_kwargs_merges_json_and_scalars_without_none_scalars() -> None:
    def sample(
        model: str,
        max_tokens: int = 1024,
        temperature: float | None = None,
        top_p: float | NotGiven = _NOT_GIVEN,
    ) -> None:
        raise NotImplementedError

    kwargs = build_call_kwargs(
        inspect.signature(sample),
        json_payload={"model": "claude-opus", "messages": [{"role": "user", "content": "hi"}]},
        scalar_values={"max_tokens": 50, "temperature": None, "top_p": 0.9},
    )
    assert kwargs["model"] == "claude-opus"
    assert kwargs["messages"] == [{"role": "user", "content": "hi"}]
    assert kwargs["max_tokens"] == 50
    # Explicit None scalars are skipped, but a None *default* is still filled
    # when the key is absent — gateway.invoke strips Nones afterward.
    assert kwargs["temperature"] is None
    assert kwargs["top_p"] == 0.9


def test_build_call_kwargs_fills_non_omit_defaults_when_absent() -> None:
    def sample(model: str, max_tokens: int = 256, top_p: float | Omit = _OMIT) -> None:
        raise NotImplementedError

    kwargs = build_call_kwargs(
        inspect.signature(sample),
        json_payload={"model": "claude-sonnet"},
        scalar_values={},
    )
    assert kwargs == {"model": "claude-sonnet", "max_tokens": 256}
    assert "top_p" not in kwargs


def test_normalize_annotation_with_single_filtered_type() -> None:
    """_normalize_annotation handles Optional[str] by extracting str."""
    from typing import Optional

    from claudeloop.infrastructure.api.params import _normalize_annotation

    # Deliberately the legacy typing.Optional spelling, not `str | None` --
    # this is the exact input shape being normalized, not a real annotation.
    result = _normalize_annotation(Optional[str])  # noqa: UP045
    assert result is str


def test_is_scalar_annotation_with_unknown_forward_ref() -> None:
    """is_scalar_annotation rejects string forward refs not in _SCALAR_BY_NAME."""
    from claudeloop.infrastructure.api.params import is_scalar_annotation

    # A forward ref that's not a known scalar type name
    result = is_scalar_annotation("UnknownComplexType")
    assert result is False


def test_build_call_kwargs_skips_already_present_kwargs() -> None:
    """build_call_kwargs doesn't override kwargs already present from json_payload."""

    def sample(model: str, max_tokens: int = 500) -> None:
        raise NotImplementedError

    kwargs = build_call_kwargs(
        inspect.signature(sample),
        json_payload={"model": "claude-opus", "max_tokens": 200},
        scalar_values={},
    )
    # max_tokens from json_payload should be preserved, not overridden by default
    assert kwargs["max_tokens"] == 200


def test_build_call_kwargs_skips_self_parameter() -> None:
    """A bound-method-shaped signature (with `self`) must not surface `self`
    in the merged kwargs -- it's in SKIP_PARAMETERS."""

    def sample(self: object, model: str, max_tokens: int = 100) -> None:
        raise NotImplementedError

    kwargs = build_call_kwargs(
        inspect.signature(sample),
        json_payload={"model": "claude-opus"},
        scalar_values={},
    )
    assert "self" not in kwargs
    assert kwargs == {"model": "claude-opus", "max_tokens": 100}


def test_unwrap_optional_delegates_to_normalize_annotation() -> None:
    """_unwrap_optional is a thin alias over _normalize_annotation."""
    from typing import Optional

    from claudeloop.infrastructure.api.params import _unwrap_optional

    result = _unwrap_optional(Optional[int])  # noqa: UP045
    assert result is int


def test_is_scalar_annotation_false_for_non_string_non_type_annotation() -> None:
    """After normalization, an annotation that is neither bool/int/float/str,
    has no typing origin, and isn't a string forward-ref falls through to the
    final `return False` (distinct from the `ann in _SCALAR_BY_NAME` string
    branch covered by the "unknown forward ref" case)."""
    assert is_scalar_annotation(None) is False

    class NotAScalar:
        pass

    assert is_scalar_annotation(NotAScalar) is False


def test_normalize_annotation_multi_arg_union_returns_original() -> None:
    """Union with 2+ non-None filtered args is returned as-is (86->88)."""
    from claudeloop.infrastructure.api.params import _normalize_annotation

    result = _normalize_annotation(str | int)
    assert result is not str
    assert result is not int
