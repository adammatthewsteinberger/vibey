# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for cli/man_page.py — manual page rendering."""

from __future__ import annotations

import io
import sys

from claudeloop import __version__
from claudeloop.cli.man_page import render_man_page, write_man_page


def test_render_man_page_includes_all_required_sections() -> None:
    """render_man_page returns a string with all manual page sections."""
    output = render_man_page()
    # Check for required man page sections
    assert "NAME" in output
    assert "SYNOPSIS" in output
    assert "DESCRIPTION" in output
    assert "COMMANDS" in output
    assert "LOGGING" in output
    assert "EXIT STATUS" in output
    assert "EXAMPLES" in output
    assert "FILES" in output
    assert "ENVIRONMENT" in output
    assert "SEE ALSO" in output
    assert "VERSION" in output


def test_render_man_page_includes_version() -> None:
    """render_man_page includes the current version."""
    output = render_man_page()
    assert __version__ in output


def test_render_man_page_includes_command_name() -> None:
    """render_man_page includes 'claudeloop' command name."""
    output = render_man_page()
    assert "claudeloop" in output.lower()


def test_render_man_page_includes_common_commands() -> None:
    """render_man_page lists common commands in SYNOPSIS."""
    output = render_man_page()
    assert "claudeloop run" in output
    assert "claudeloop resume" in output
    assert "claudeloop stop" in output
    assert "claudeloop prompt" in output


def test_render_man_page_includes_exit_codes() -> None:
    """render_man_page documents exit status codes."""
    output = render_man_page()
    assert "0" in output  # Success
    assert "1" in output  # General error
    assert "75" in output  # Wind-down
    assert "130" in output  # Stop


def test_render_man_page_includes_config_file_locations() -> None:
    """render_man_page documents configuration file paths."""
    output = render_man_page()
    assert ".claudeloop" in output or "claudeloop.toml" in output


def test_render_man_page_is_plain_text() -> None:
    """render_man_page returns plain text without escape sequences."""
    output = render_man_page()
    # Man pages use plain text, no ANSI codes
    assert "\x1b[" not in output


def test_write_man_page_outputs_to_stdout(monkeypatch) -> None:
    """write_man_page writes the rendered manual to stdout."""
    buffer = io.StringIO()
    monkeypatch.setattr(sys, "stdout", buffer)
    write_man_page()
    output = buffer.getvalue()
    assert len(output) > 0
    assert "NAME" in output
    assert "claudeloop" in output


def test_write_man_page_ends_with_newline(monkeypatch) -> None:
    """write_man_page ensures output ends with newline."""
    buffer = io.StringIO()
    monkeypatch.setattr(sys, "stdout", buffer)
    write_man_page()
    output = buffer.getvalue()
    assert output.endswith("\n")


def test_write_man_page_appends_newline_when_missing(monkeypatch) -> None:
    """When render_man_page() doesn't end with a newline, write_man_page adds one."""
    import claudeloop.cli.man_page as man_page_mod

    monkeypatch.setattr(man_page_mod, "render_man_page", lambda: "no trailing newline")
    buffer = io.StringIO()
    monkeypatch.setattr(sys, "stdout", buffer)
    man_page_mod.write_man_page()
    assert buffer.getvalue() == "no trailing newline\n"
