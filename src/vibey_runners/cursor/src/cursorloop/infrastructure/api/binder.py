# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Bind OpenAPI operations to Typer commands — working partial HTTP surface."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import typer

from cursorloop.infrastructure.api.gateway import CloudAgentsGateway
from cursorloop.infrastructure.api.registry import PARTIAL_OPERATIONS


@dataclass(frozen=True, slots=True)
class BoundOperation:
    operation_id: str
    summary: str
    handler: Callable[..., None]


def _require_api_key() -> str:
    key = os.environ.get("CURSOR_API_KEY", "").strip()
    if not key:
        typer.echo("CURSOR_API_KEY is unset", err=True)
        raise typer.Exit(code=1)
    return key


def _echo_json(data: object) -> None:
    typer.echo(json.dumps(data, indent=2, default=str))


def bind_partial_commands(app: typer.Typer) -> list[BoundOperation]:
    """Register the runner-needed Cloud Agents subset as live HTTP commands.

    Full OpenAPI → CLI generation remains deferred (ADR-0006). These commands
    are labelled PARTIAL in help text but invoke the real REST endpoints.
    """
    bound: list[BoundOperation] = []

    @app.command("me")
    def me() -> None:
        """GET /v1/me (PARTIAL surface)."""
        key = _require_api_key()
        try:
            with CloudAgentsGateway(api_key=key) as gw:
                _echo_json(gw.invoke("GET", "/v1/me"))
        except httpx.HTTPError as exc:
            typer.echo(f"getMe failed: {exc}", err=True)
            raise typer.Exit(code=1) from exc

    @app.command("models")
    def models() -> None:
        """GET /v1/models (PARTIAL surface)."""
        key = _require_api_key()
        try:
            with CloudAgentsGateway(api_key=key) as gw:
                _echo_json(gw.invoke("GET", "/v1/models"))
        except httpx.HTTPError as exc:
            typer.echo(f"listModels failed: {exc}", err=True)
            raise typer.Exit(code=1) from exc

    @app.command("create")
    def create(
        body: str | None = typer.Option(
            None, "--json", help="Inline JSON body for POST /v1/agents"
        ),
        json_file: Path | None = typer.Option(
            None, "--json-file", exists=True, readable=True, help="Path to JSON body"
        ),
    ) -> None:
        """POST /v1/agents (PARTIAL surface)."""
        key = _require_api_key()
        payload: dict[str, Any]
        if json_file is not None:
            payload = json.loads(json_file.read_text(encoding="utf-8"))
        elif body:
            payload = json.loads(body)
        else:
            typer.echo("Provide --json or --json-file", err=True)
            raise typer.Exit(code=2)
        try:
            with CloudAgentsGateway(api_key=key) as gw:
                _echo_json(gw.invoke("POST", "/v1/agents", json=payload))
        except httpx.HTTPError as exc:
            typer.echo(f"createAgent failed: {exc}", err=True)
            raise typer.Exit(code=1) from exc

    @app.command("get")
    def get(agent_id: str = typer.Argument(..., help="Cloud agent id")) -> None:
        """GET /v1/agents/{id} (PARTIAL surface)."""
        key = _require_api_key()
        try:
            with CloudAgentsGateway(api_key=key) as gw:
                _echo_json(gw.invoke("GET", f"/v1/agents/{agent_id}"))
        except httpx.HTTPError as exc:
            typer.echo(f"getAgent failed: {exc}", err=True)
            raise typer.Exit(code=1) from exc

    @app.command("cancel")
    def cancel(agent_id: str = typer.Argument(..., help="Cloud agent id")) -> None:
        """POST /v1/agents/{id}/cancel (PARTIAL surface)."""
        key = _require_api_key()
        try:
            with CloudAgentsGateway(api_key=key) as gw:
                _echo_json(gw.invoke("POST", f"/v1/agents/{agent_id}/cancel"))
        except httpx.HTTPError as exc:
            typer.echo(f"cancelAgent failed: {exc}", err=True)
            raise typer.Exit(code=1) from exc

    bound.extend(
        [
            BoundOperation("getMe", "Current authenticated identity", me),
            BoundOperation("listModels", "List available models", models),
            BoundOperation("createAgent", "Create a cloud agent", create),
            BoundOperation("getAgent", "Get a cloud agent by id", get),
            BoundOperation("cancelAgent", "Cancel a running cloud agent", cancel),
        ]
    )
    missing = PARTIAL_OPERATIONS - {b.operation_id for b in bound}
    if missing:
        raise RuntimeError(f"partial binder missing operations: {sorted(missing)}")
    return bound


def operation_to_click_name(operation_id: str) -> str:
    """Map camelCase operationId to a kebab CLI name."""
    chars: list[str] = []
    for i, ch in enumerate(operation_id):
        if ch.isupper() and i > 0:
            chars.append("-")
        chars.append(ch.lower())
    return "".join(chars)


def json_body_option_help() -> dict[str, Any]:
    return {
        "--json": "Inline JSON body",
        "--json-file": "Path to JSON body",
    }
