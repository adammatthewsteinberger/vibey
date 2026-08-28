# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""SubprocessGateRunner: real subprocesses, and the greeter4 live finding --
a gate command whose binary does not exist is a FAILING GATE (127, so the
repair loop can tell the engine to fix its own command), never an exception
that escapes to become a retried-then-dead vibey failure."""

from pathlib import Path

from vibey.infrastructure.build.gate_runner import SubprocessGateRunner


async def test_runs_a_real_command_and_captures_output(tmp_path: Path) -> None:
    result = await SubprocessGateRunner().run(("sh", "-c", "echo ok"), cwd=tmp_path)

    assert result.returncode == 0
    assert result.stdout.strip() == "ok"


async def test_a_failing_command_reports_its_exit_code(tmp_path: Path) -> None:
    result = await SubprocessGateRunner().run(("sh", "-c", "echo no >&2; exit 3"), cwd=tmp_path)

    assert result.returncode == 3
    assert "no" in result.stderr


async def test_a_missing_binary_is_a_failing_gate_not_an_exception(tmp_path: Path) -> None:
    result = await SubprocessGateRunner().run(
        ("definitely-not-a-real-binary-xyz", "--version"), cwd=tmp_path
    )

    assert result.returncode == 127
    assert "could not start" in result.stderr
