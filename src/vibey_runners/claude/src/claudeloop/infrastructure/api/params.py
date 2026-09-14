# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Classify SDK method parameters for Typer / Click binding."""

from __future__ import annotations

import inspect
import types
from dataclasses import dataclass
from typing import Any, Union, get_args, get_origin

from anthropic import NotGiven, Omit

SKIP_PARAMETERS = frozenset(
    {
        "self",
        "extra_headers",
        "extra_query",
        "extra_body",
    }
)

_SCALAR_BY_NAME: dict[str, type] = {
    "int": int,
    "float": float,
    "str": str,
    "bool": bool,
}


@dataclass(frozen=True, slots=True)
class ScalarParam:
    name: str
    cli_name: str
    annotation: Any
    required: bool
    default: Any


def _is_omit_default(default: Any) -> bool:
    return isinstance(default, (Omit, NotGiven))


def _is_omit_or_not_given_type(annotation: Any) -> bool:
    return annotation is Omit or annotation is NotGiven


def _normalize_annotation(annotation: Any) -> Any:
    """Reduce Optional / ``X | None`` / ``X | Omit`` forms to one type when unique.

    Anthropic SDK methods are typically annotated under
    ``from __future__ import annotations``, so runtime signatures carry *strings*
    like ``'int | Omit'`` rather than evaluated unions. Without peeling those
    suffixes, list endpoints lose every pagination CLI flag.
    """
    if isinstance(annotation, str):
        text = annotation.strip()
        changed = True
        while changed:
            changed = False
            if text.startswith("Optional[") and text.endswith("]"):
                text = text[len("Optional[") : -1].strip()
                changed = True
                continue
            for prefix in ("None | ", "Omit | ", "NotGiven | "):
                if text.startswith(prefix):
                    text = text[len(prefix) :].strip()
                    changed = True
                    break
            if changed:
                continue
            for suffix in (" | Omit", " | NotGiven", " | None"):
                if text.endswith(suffix):
                    text = text[: -len(suffix)].strip()
                    changed = True
                    break
        if " | " in text or "[" in text:
            return annotation
        return _SCALAR_BY_NAME.get(text, text)

    origin = get_origin(annotation)
    if origin is Union or isinstance(annotation, types.UnionType):
        filtered = [
            arg
            for arg in get_args(annotation)
            if arg is not type(None) and not _is_omit_or_not_given_type(arg)
        ]
        if len(filtered) == 1:
            return _normalize_annotation(filtered[0])
    return annotation


def _unwrap_optional(annotation: Any) -> Any:
    return _normalize_annotation(annotation)


def is_scalar_annotation(annotation: Any) -> bool:
    if annotation is inspect.Parameter.empty:
        return False
    ann = _normalize_annotation(annotation)
    if ann is bool:
        return True
    if ann in (int, float, str):
        return True
    origin = get_origin(ann)
    if origin is not None:
        return False
    if isinstance(ann, str):
        # Forward refs to complex TypedDicts — not scalar.
        return ann in _SCALAR_BY_NAME
    return False


def click_type_for_annotation(annotation: Any) -> Any:
    """Map a (possibly stringified) scalar annotation to a Click type."""
    ann = _normalize_annotation(annotation)
    if ann is bool or ann == "bool":
        return bool
    if ann is int or ann == "int":
        return int
    if ann is float or ann == "float":
        return float
    return str


def scalar_parameters(signature: inspect.Signature) -> tuple[ScalarParam, ...]:
    params: list[ScalarParam] = []
    for name, param in signature.parameters.items():
        if name in SKIP_PARAMETERS:
            continue
        if not is_scalar_annotation(param.annotation):
            continue
        required = param.default is inspect.Parameter.empty
        if not required and _is_omit_default(param.default):
            required = False
        cli_name = name.replace("_", "-")
        params.append(
            ScalarParam(
                name=name,
                cli_name=cli_name,
                annotation=param.annotation,
                required=required,
                default=None if required else param.default,
            )
        )
    return tuple(params)


def build_call_kwargs(
    signature: inspect.Signature,
    *,
    json_payload: dict[str, Any],
    scalar_values: dict[str, Any],
) -> dict[str, Any]:
    kwargs: dict[str, Any] = dict(json_payload)
    for name, value in scalar_values.items():
        if value is None:
            continue
        kwargs[name] = value
    for name, param in signature.parameters.items():
        if name in SKIP_PARAMETERS or name == "self":
            continue
        if name in kwargs:
            continue
        if param.default is not inspect.Parameter.empty and not _is_omit_default(param.default):
            kwargs[name] = param.default
    return kwargs
