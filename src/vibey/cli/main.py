import typer

from vibey import __version__

app = typer.Typer(name="vibey", no_args_is_help=True)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"vibey {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(False, "--version", callback=_version_callback, is_eager=True),
) -> None:
    """vibey: a queue-based, three-phase conductor for autonomous software delivery."""


if __name__ == "__main__":
    app()
