# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Render a short man-page style reference for ``cursorloop --man``."""

from __future__ import annotations

MAN_TEXT = """\
CURSORLOOP(1)                    User Commands                   CURSORLOOP(1)

NAME
       cursorloop — autonomous Cursor Agent session runner

SYNOPSIS
       cursorloop run --plan FILE [--cwd DIR] [options]
       cursorloop resume [--run-id ID]
       cursorloop stop | prompt | status | logs | watch | runs
       cursorloop doctor [--json] [--explain-error FILE]
       cursorloop cloud STATUS|me|models|...
       cursorloop --version | --man | --help

DESCRIPTION
       Never blocks on a human. Distinguishes waitable rate-limit windows from
       non-waitable exhausted credits. Composer-first (composer-2.5); Grok is a
       model profile, not a product.

EXIT STATUS
       0   success
       1   failed
       3   authentication failed
       4   max wait exceeded
       130 stopped by operator

ENVIRONMENT
       CURSOR_API_KEY                 vendor auth (Cursor only; no Anthropic envs)
       CURSORLOOP_*                   product configuration
       CURSORLOOP_ALLOW_TEST_AGENT    must be 1 with TEST_AGENT_SCRIPT
       CURSORLOOP_TEST_AGENT_SCRIPT   path to scripted agent JSON

SEE ALSO
       docs/ at the project root; ADR-0006 for Cloud Agents deferral.
"""


def render_man_page() -> str:
    return MAN_TEXT
