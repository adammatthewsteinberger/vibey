# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Real DoctorEnvironment — the only infrastructure adapter for the `doctor`
use case. Shells out to `claude` itself for version/MCP info rather than
re-implementing config-file parsing, since that surface is exactly the kind
the docs warn changes between Claude Code releases (see
docs/architecture/decisions/0002-agent-sdk-over-subprocess.md)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess  # nosec B404 - fixed-argument calls to the `claude` CLI only, never shell=True
from pathlib import Path


class RealDoctorEnvironment:
    def find_claude_cli(self) -> str | None:
        return shutil.which("claude")

    def claude_cli_version(self, path: str) -> str | None:
        try:
            result = subprocess.run(  # nosec B603
                [path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        if result.returncode != 0:
            return None
        return result.stdout.strip() or None

    def is_authenticated(self) -> bool:
        if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"):
            return True
        # `claude auth status` is the authoritative source — it reports true
        # for claude.ai/OAuth-profile logins (e.g. `ant auth login`) that
        # never touch ANTHROPIC_API_KEY or a .credentials.json file at all,
        # which the two checks above would otherwise miss entirely.
        cli_path = self.find_claude_cli()
        if cli_path is not None:
            try:
                result = subprocess.run(  # nosec B603
                    [cli_path, "auth", "status"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )
                status = json.loads(result.stdout)
                if isinstance(status, dict) and status.get("loggedIn") is True:
                    return True
            except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
                pass
        credentials_path = Path.home() / ".claude" / ".credentials.json"
        return credentials_path.is_file()

    def configured_mcp_servers(self) -> list[str]:
        cli_path = self.find_claude_cli()
        if cli_path is None:
            return []
        try:
            # `claude mcp list` actively health-checks every configured server
            # (observed ~14s for 37 servers) — doctor is an explicit
            # pre-flight command, not latency-sensitive, so this gets a
            # generous timeout rather than racing the check itself.
            result = subprocess.run(  # nosec B603
                [cli_path, "mcp", "list"],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return []
        if result.returncode != 0:
            return []
        servers = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line or ":" not in line:
                continue
            servers.append(line.split(":", 1)[0].strip())
        return servers

    def anthropic_sdk_version(self) -> str | None:
        try:
            import anthropic
        except ImportError:
            return None
        return anthropic.__version__

    def api_surface_method_count(self) -> int | None:
        try:
            from claudeloop.infrastructure.api.introspect import discover_surface
        except ImportError:
            return None
        return len(discover_surface())
