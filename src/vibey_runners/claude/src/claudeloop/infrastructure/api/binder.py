# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Bind discovered SDK methods to a nested Click command tree."""

from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any

import click

from claudeloop.infrastructure.api.gateway import AnthropicApiGateway, default_gateway
from claudeloop.infrastructure.api.introspect import DiscoveredMethod, discover_surface
from claudeloop.infrastructure.api.params import click_type_for_annotation, scalar_parameters
from claudeloop.infrastructure.api.providers import PROVIDER_FACTORIES
from claudeloop.infrastructure.api.registry import clear_registry, register_command_path


def _make_click_command(
    method: DiscoveredMethod,
    gateway: AnthropicApiGateway,
) -> click.Command:
    from claudeloop.infrastructure.api.introspect import resolve_callable

    fn = resolve_callable(method)
    signature = inspect.signature(fn)
    scalars = scalar_parameters(signature)

    params: list[click.Parameter] = [
        click.Option(["--json"], default=None, help="Inline JSON object for request fields."),
        click.Option(
            ["--json-file"],
            type=click.Path(path_type=Path),
            default=None,
            help="JSON file path, or @/path for file indirection.",
        ),
        click.Option(["--raw"], is_flag=True, default=False, help="Use with_raw_response."),
        click.Option(
            ["--stream"],
            is_flag=True,
            default=False,
            help="Use with_streaming_response.",
        ),
        click.Option(
            ["--max-items"],
            type=int,
            default=None,
            help="Auto-pagination cap for list endpoints.",
        ),
    ]
    for scalar in scalars:
        params.append(
            click.Option(
                [f"--{scalar.cli_name}"],
                scalar.name,
                type=click_type_for_annotation(scalar.annotation),
                required=False,
                default=None,
                help=f"SDK parameter {scalar.name!r}.",
            )
        )

    @click.pass_context
    def callback(ctx: click.Context, /, **kwargs: Any) -> None:
        root = ctx
        while root.parent is not None:
            root = root.parent
        provider = root.obj.get("provider", "first-party") if root.obj else "first-party"
        scalar_values = {scalar.name: kwargs.pop(scalar.name, None) for scalar in scalars}
        json_body = kwargs.pop("json")
        json_file = kwargs.pop("json_file")
        raw = kwargs.pop("raw")
        stream = kwargs.pop("stream")
        max_items = kwargs.pop("max_items")
        try:
            text = gateway.invoke_and_print(
                method.path,
                provider=provider,
                json_body=json_body,
                json_file=json_file,
                raw=raw,
                stream=stream,
                max_items=max_items,
                scalar_values=scalar_values,
                method=method,
            )
        except (ValueError, TypeError, OSError) as exc:
            raise click.ClickException(str(exc)) from exc
        click.echo(text)

    return click.Command(
        name=method.method_name,
        callback=callback,
        params=params,
        help=f"SDK `{method.path}`.",
    )


def _ensure_group(parent: click.Group, name: str) -> click.Group:
    cmd = parent.commands.get(name)
    if isinstance(cmd, click.Group):
        return cmd
    group = click.Group(name)
    parent.add_command(group, name=name)
    return group


def build_api_click_group(*, gateway: AnthropicApiGateway | None = None) -> click.Group:
    """Build the nested Click group mounted at ``claudeloop api``."""
    clear_registry()
    gw = gateway or default_gateway()
    provider_names = ", ".join(sorted(PROVIDER_FACTORIES))

    @click.group(
        "api",
        help="Generated 1:1 Anthropic SDK REST surface.",
        context_settings={"help_option_names": ["-h", "--help"]},
    )
    @click.option(
        "--provider",
        default="first-party",
        show_default=True,
        help=f"SDK client ({provider_names}).",
    )
    @click.pass_context
    def api_group(ctx: click.Context, provider: str) -> None:
        if provider not in PROVIDER_FACTORIES:
            raise click.ClickException(f"unknown provider {provider!r}")
        ctx.ensure_object(dict)
        ctx.obj["provider"] = provider

    root: click.Group = api_group
    for method in discover_surface():
        parts = method.path.split(".")
        current = root
        for segment in parts[:-1]:
            current = _ensure_group(current, segment)
        current.add_command(_make_click_command(method, gw))
        register_command_path(method.path)

    return root
