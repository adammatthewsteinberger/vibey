# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Guard: Anthropic / Claude / claudeloop names must never enter this tree."""

from __future__ import annotations

import ast
import tomllib
from importlib.metadata import distribution, requires
from pathlib import Path

from packaging.requirements import Requirement

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
_PYPROJECT = _ROOT / "pyproject.toml"

_FORBIDDEN_IMPORT_ROOTS = frozenset({"anthropic", "claude_agent_sdk", "claudeloop"})
_FORBIDDEN_DIST_NAMES = frozenset({"anthropic", "claude-agent-sdk", "claudeloop"})
_FORBIDDEN_TOKENS = ("anthropic", "claude_agent_sdk", "claude-agent-sdk", "claudeloop")


def _normalize_dist_name(name: str) -> str:
    return name.lower().replace("_", "-")


def _is_forbidden_dist_name(name: str) -> bool:
    return _normalize_dist_name(name) in _FORBIDDEN_DIST_NAMES


def _requirement_name(spec: str) -> str:
    return Requirement(spec).name


def _src_python_files() -> list[Path]:
    assert _SRC.is_dir(), f"expected source tree at {_SRC}"
    return sorted(path for path in _SRC.rglob("*.py") if path.is_file())


def test_no_vendor_import_statements_under_src() -> None:
    offenders: list[str] = []
    for path in _src_python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                root = name.split(".")[0]
                if root in _FORBIDDEN_IMPORT_ROOTS:
                    rel = path.relative_to(_ROOT)
                    offenders.append(f"{rel}: {name}")
        text = path.read_text(encoding="utf-8")
        for token in _FORBIDDEN_TOKENS:
            if token in text:
                rel = path.relative_to(_ROOT)
                offenders.append(f"{rel}: token {token!r}")
    assert offenders == []


def test_no_vendor_in_pyproject_dependencies() -> None:
    assert _PYPROJECT.is_file(), f"expected {_PYPROJECT}"
    data = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))
    project = data["project"]
    specs: list[str] = list(project.get("dependencies", []))
    for extra_specs in project.get("optional-dependencies", {}).values():
        specs.extend(extra_specs)
    leaked = [spec for spec in specs if _is_forbidden_dist_name(_requirement_name(spec))]
    assert leaked == []


def test_no_vendor_in_installed_distribution_metadata() -> None:
    dist = distribution("codexloop")
    assert _normalize_dist_name(dist.metadata["Name"]) == "codexloop"
    leaked = [
        req
        for req in (requires("codexloop") or [])
        if _is_forbidden_dist_name(_requirement_name(req))
    ]
    assert leaked == []
