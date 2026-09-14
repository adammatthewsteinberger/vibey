# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

import shutil
import subprocess  # nosec B404 - optional TTS via fixed `say`/`espeak` argv
import sys

import typer

app = typer.Typer(help="Voice input/output (optional claudeloop[voice] extras)")


def _voice_hint() -> None:
    typer.echo(
        "Voice features require optional dependencies. Install with:\n"
        "  pip install 'claudeloop[voice]'",
        err=True,
    )


@app.command("start")
def start() -> None:
    """Start voice input (not yet implemented)."""
    typer.echo(
        "Voice input is not wired yet. "
        "Install claudeloop[voice] for future support; use prompt/stop for now.",
        err=True,
    )
    _voice_hint()
    raise typer.Exit(code=1)


@app.command("stop")
def stop() -> None:
    """Stop voice input (not yet implemented)."""
    typer.echo("Voice input is not active (stub).", err=True)
    raise typer.Exit(code=1)


@app.command("status")
def status() -> None:
    """Show voice subsystem status."""
    typer.echo("Voice subsystem: not running (stub)")


def speak(
    text: str = typer.Argument(..., help="Text to speak aloud"),
) -> None:
    """Speak text using the system TTS (macOS say or espeak)."""
    if sys.platform == "darwin" and shutil.which("say"):
        subprocess.run(["say", text], check=False)  # nosec B603 B607
        return
    if shutil.which("espeak"):
        subprocess.run(["espeak", text], check=False)  # nosec B603 B607
        return
    _voice_hint()
    typer.echo("No TTS backend found (need macOS 'say' or 'espeak').", err=True)
    raise typer.Exit(code=1)
