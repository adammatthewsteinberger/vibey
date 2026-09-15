# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Slash-command allowlist — pure validation, no I/O."""

from __future__ import annotations

from dataclasses import dataclass

# Claude Code–style commands plus claudeloop extensions. Never executed as shell.
ALLOWED_SLASH_COMMANDS = frozenset(
    {
        "help",
        "clear",
        "compact",
        "cost",
        "doctor",
        "memory",
        "model",
        "permissions",
        "plan",
        "review",
        "status",
        "config",
        "vim",
        "terminal-setup",
        # claudeloop extensions
        "claudeloop-status",
        "claudeloop-savepoint",
    }
)


@dataclass(frozen=True, slots=True)
class ParsedSlash:
    name: str
    args: str


def parse_slash(text: str) -> ParsedSlash:
    raw = text.strip()
    if not raw.startswith("/"):
        raise ValueError("slash command must start with '/'")
    body = raw[1:].strip()
    if not body:
        raise ValueError("slash command name must not be blank")
    parts = body.split(None, 1)
    name = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    if name not in ALLOWED_SLASH_COMMANDS:
        raise ValueError(
            f"unknown slash command /{name}; allowed: {sorted(ALLOWED_SLASH_COMMANDS)}"
        )
    return ParsedSlash(name=name, args=args)


def slash_to_prompt(parsed: ParsedSlash) -> str:
    """Materialize a slash command as an operator prompt injection."""
    if parsed.args:
        return f"Execute the /{parsed.name} command with arguments: {parsed.args}"
    return f"Execute the /{parsed.name} command."
