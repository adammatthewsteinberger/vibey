# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Bind discovered SDK methods to a nested Typer command tree."""

from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any

import typer

from codexloop.infrastructure.api.gateway import OpenAIApiGateway, default_gateway
from codexloop.infrastructure.api.introspect import EndpointSpec, discover_surface, resolve_callable
from codexloop.infrastructure.api.params import (
    ScalarParam,
    scalar_parameters,
    typer_type_for_annotation,
)
from codexloop.infrastructure.api.providers import (
    PROVIDER_FACTORIES,
    client_class_for_provider,
    surface_roots_for_provider,
)
from codexloop.infrastructure.api.registry import clear_registry, register_command_path


def _scalar_default_src(scalar: ScalarParam) -> str:
    py_type = typer_type_for_annotation(scalar.annotation).__name__
    return (
        f"{scalar.name}: {py_type} | None = typer.Option("
        f'None, "--{scalar.cli_name}", help="SDK parameter {scalar.name!r}.")'
    )


def _make_typer_command(
    method: EndpointSpec,
    gateway: OpenAIApiGateway,
    *,
    client_cls: type,
) -> Any:
    fn = resolve_callable(method, client_cls=client_cls)
    signature = inspect.signature(fn)
    scalars = scalar_parameters(signature)
    param_names = [s.name for s in scalars]

    def bound_callback(ctx: typer.Context, **kwargs: Any) -> None:
        root: Any = ctx
        while root.parent is not None:
            root = root.parent
        obj = root.obj if isinstance(root.obj, dict) else {}
        provider = str(obj.get("provider", "openai"))
        base_url = obj.get("base_url")
        json_body = kwargs.pop("json_body", None)
        json_file = kwargs.pop("json_file", None)
        raw = bool(kwargs.pop("raw", False))
        stream = bool(kwargs.pop("stream", False))
        max_items = kwargs.pop("max_items", None)
        scalar_values = {name: kwargs.get(name) for name in param_names}
        try:
            text = gateway.invoke_and_print(
                method.path,
                provider=provider,
                base_url=base_url if isinstance(base_url, str) else None,
                json_body=json_body,
                json_file=json_file,
                raw=raw,
                stream=stream,
                max_items=max_items,
                scalar_values=scalar_values,
                method=method,
            )
        except (ValueError, TypeError, OSError) as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(2) from exc
        typer.echo(text)

    # Option-as-default (not Annotated) so Typer works under postponed annotations.
    args_src = [
        "ctx: typer.Context",
        'json_body: str | None = typer.Option(None, "--json", help="Inline JSON object.")',
        'json_file: Path | None = typer.Option(None, "--json-file", help="JSON file path.")',
        'raw: bool = typer.Option(False, "--raw", help="Use with_raw_response.")',
        'stream: bool = typer.Option(False, "--stream", help="Use with_streaming_response.")',
        'max_items: int | None = typer.Option(None, "--max-items", help="Auto-pagination cap.")',
    ]
    args_src.extend(_scalar_default_src(s) for s in scalars)
    scalar_dict = ", ".join(f"{n!r}: {n}" for n in param_names)
    body = (
        f"def command({', '.join(args_src)}) -> None:\n"
        f"    scalar_values = {{{scalar_dict}}}\n"
        "    bound_callback(\n"
        "        ctx,\n"
        "        json_body=json_body,\n"
        "        json_file=json_file,\n"
        "        raw=raw,\n"
        "        stream=stream,\n"
        "        max_items=max_items,\n"
        "        **scalar_values,\n"
        "    )\n"
    )
    ns: dict[str, Any] = {
        "Path": Path,
        "typer": typer,
        "bound_callback": bound_callback,
    }
    exec(body, ns)  # nosec B102 — binder-owned source string builds Typer callbacks
    command_fn = ns["command"]
    command_fn.__name__ = method.method_name
    command_fn.__doc__ = f"SDK `{method.path}`."
    return command_fn


def _ensure_group(parent: typer.Typer, name: str, groups: dict[str, typer.Typer]) -> typer.Typer:
    key = f"{id(parent)}:{name}"
    existing = groups.get(key)
    if existing is not None:
        return existing
    child = typer.Typer(name=name, help=f"OpenAI `{name}` resource.", no_args_is_help=True)
    parent.add_typer(child, name=name)
    groups[key] = child
    return child


def build_api_typer_app(
    *,
    gateway: OpenAIApiGateway | None = None,
    provider: str = "openai",
) -> typer.Typer:
    """Build the nested Typer app mounted at ``codexloop api``."""
    clear_registry()
    gw = gateway or default_gateway()
    client_cls = client_class_for_provider(provider)
    roots = surface_roots_for_provider(provider)

    api = typer.Typer(
        name="api",
        help="Generated 1:1 OpenAI SDK REST surface.",
        no_args_is_help=True,
    )

    @api.callback()
    def _api_callback(
        ctx: typer.Context,
        provider_opt: str = typer.Option(
            "openai",
            "--provider",
            help="SDK client (azure, custom, openai).",
        ),
        base_url: str | None = typer.Option(
            None,
            "--base-url",
            help="Override API base URL (custom / openai).",
        ),
    ) -> None:
        if provider_opt not in PROVIDER_FACTORIES:
            typer.echo(f"unknown provider {provider_opt!r}", err=True)
            raise typer.Exit(2)
        ctx.ensure_object(dict)
        ctx.obj["provider"] = provider_opt
        ctx.obj["base_url"] = base_url

    groups: dict[str, typer.Typer] = {}
    for method in discover_surface(roots=roots, client_cls=client_cls):
        parts = method.path.split(".")
        current = api
        for segment in parts[:-1]:
            current = _ensure_group(current, segment, groups)
        current.command(method.method_name)(_make_typer_command(method, gw, client_cls=client_cls))
        register_command_path(method.path)

    return api
