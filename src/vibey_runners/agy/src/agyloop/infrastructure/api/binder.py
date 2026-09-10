# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Bind discovered Gemini REST methods to a nested Typer command tree."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Annotated, Any

import typer

from agyloop.infrastructure.api.discover import (
    ApiLane,
    DiscoveredMethod,
    discover_surface,
    parse_api_lane,
)
from agyloop.infrastructure.api.gateway import GeminiRestGateway, default_gateway
from agyloop.infrastructure.api.registry import clear_registry, register_command_path

_CAMEL = re.compile(r"(.)([A-Z][a-z]+)")
_CAMEL2 = re.compile(r"([a-z0-9])([A-Z])")


def kebab(name: str) -> str:
    stepped = _CAMEL.sub(r"\1-\2", name)
    return _CAMEL2.sub(r"\1-\2", stepped).replace("_", "-").lower()


def _attach_method(
    group: typer.Typer,
    method: DiscoveredMethod,
    gateway: GeminiRestGateway,
) -> None:
    method_path = method.path
    method_lane = method.lane
    cmd_name = kebab(method.path.rsplit(".", 1)[-1])
    help_text = (
        f"REST `{method.path}` ({method.http_method} {method.http_path}, lane={method.lane})."
    )

    def command(
        ctx: typer.Context,
        json_body: Annotated[
            str | None, typer.Option("--json", help="Inline JSON object for request fields.")
        ] = None,
        json_file: Annotated[
            Path | None,
            typer.Option("--json-file", help="JSON file path for the request body."),
        ] = None,
    ) -> None:
        root = ctx.find_root()
        obj = root.obj if isinstance(root.obj, dict) else {}
        lane = str(obj.get("lane", "developer"))
        if lane != method_lane:
            typer.echo(
                f"{method_path} belongs to --lane {method_lane}, not {lane}.",
                err=True,
            )
            raise typer.Exit(code=1)
        try:
            text = gateway.invoke_and_print(
                method_path,
                lane=lane,
                json_body=json_body,
                json_file=json_file,
                method=method,
            )
        except (ValueError, TypeError, OSError) as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=1) from exc
        typer.echo(text)

    command.__doc__ = help_text
    group.command(name=cmd_name, help=help_text)(command)


def _bind_lane(
    api: typer.Typer,
    *,
    lane: ApiLane,
    gateway: GeminiRestGateway,
    groups: dict[tuple[str, ...], typer.Typer],
) -> None:
    for method in discover_surface(lane=lane):
        parts = method.path.split(".")
        parent = api
        key: tuple[str, ...] = ()
        for segment in parts[:-1]:
            key = (*key, kebab(segment))
            if key not in groups:
                child = typer.Typer(
                    help=f"{segment} methods",
                    add_completion=False,
                    no_args_is_help=True,
                )
                parent.add_typer(child, name=kebab(segment))
                groups[key] = child
            parent = groups[key]
        _attach_method(parent, method, gateway)
        register_command_path(method.path, lane=lane)


def build_api_app(*, gateway: GeminiRestGateway | None = None) -> typer.Typer:
    """Build the nested Typer app mounted at ``agyloop api``."""
    clear_registry()
    gw = gateway or default_gateway()
    api = typer.Typer(
        name="api",
        help=(
            "Generated 1:1 Gemini REST surface. Developer discovery by default; "
            "pass --lane vertex for the disjoint Vertex Gemini subset (ADR 0015)."
        ),
        add_completion=False,
        no_args_is_help=True,
    )

    @api.callback()
    def api_root(
        ctx: typer.Context,
        lane: Annotated[
            str,
            typer.Option(
                "--lane",
                help="API family: developer (GOOGLE_API_KEY) or vertex (ADC / access token).",
            ),
        ] = "developer",
    ) -> None:
        try:
            parsed = parse_api_lane(lane)
        except ValueError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=1) from exc
        ctx.ensure_object(dict)
        ctx.obj["lane"] = parsed
        ctx.obj["gateway"] = gw

    groups: dict[tuple[str, ...], typer.Typer] = {(): api}
    _bind_lane(api, lane="developer", gateway=gw, groups=groups)
    _bind_lane(api, lane="vertex", gateway=gw, groups=groups)
    return api


def build_api_click_group(*, gateway: GeminiRestGateway | None = None) -> Any:
    """Alias kept for bootstrap / drift tests that historically used Click."""
    return build_api_app(gateway=gateway)
