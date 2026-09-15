# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
import tomllib
from pathlib import Path

ROOT = Path(__file__).parents[1]
FORBIDDEN_DEPENDENCIES = (
    "anthro" + "pic",
    "claude-" + "agent-sdk",
)
FORBIDDEN_IMPORTS = (
    "anthro" + "pic",
    "claude_" + "agent_sdk",
)


def test_forbidden_vendor_dependencies_are_absent() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())
    dependencies = project["project"]["dependencies"]

    assert not any(
        dependency.startswith(forbidden)
        for dependency in dependencies
        for forbidden in FORBIDDEN_DEPENDENCIES
    )


def test_forbidden_vendor_imports_are_absent() -> None:
    source = "\n".join(path.read_text() for path in (ROOT / "src").rglob("*.py"))

    assert not any(forbidden in source for forbidden in FORBIDDEN_IMPORTS)
