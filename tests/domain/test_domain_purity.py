"""Enforces that vibey.domain contains no I/O, no async, and no wall-clock
reads. Every violation is a static AST check, not a runtime behavior test,
so a planted violation fails even if the offending code path is never
exercised."""

import ast
from pathlib import Path

DOMAIN_ROOT = Path(__file__).resolve().parents[2] / "src" / "vibey" / "domain"

FORBIDDEN_IMPORTS = {
    "asyncio",
    "asyncpg",
    "psycopg",
    "httpx",
    "requests",
    "typer",
    "structlog",
    "pydantic",
    "textual",
    "subprocess",
    "socket",
}

# Calls that reach outside the pure domain even without an import of a
# forbidden third-party module (builtins, or stdlib reached via `import os`
# rather than `from os import ...`).
FORBIDDEN_CALLS = {
    ("builtins", "open"),
    ("os", "environ"),
    ("os", "getenv"),
    ("datetime", "now"),
    ("datetime", "today"),
    ("time", "time"),
}


def _domain_files() -> list[Path]:
    return sorted(DOMAIN_ROOT.rglob("*.py"))


def _iter_violations(tree: ast.AST, filename: str) -> list[str]:
    violations: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in FORBIDDEN_IMPORTS:
                    violations.append(f"{filename}:{node.lineno}: forbidden import {alias.name!r}")
                if root == "pathlib":
                    violations.append(f"{filename}:{node.lineno}: forbidden import 'pathlib'")

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            root = module.split(".")[0]
            if root in FORBIDDEN_IMPORTS:
                violations.append(f"{filename}:{node.lineno}: forbidden import from {module!r}")
            if root == "pathlib":
                violations.append(f"{filename}:{node.lineno}: forbidden import from 'pathlib'")

        elif isinstance(node, ast.AsyncFunctionDef | ast.Await | ast.AsyncWith | ast.AsyncFor):
            violations.append(f"{filename}:{node.lineno}: async construct is forbidden in domain/")

        elif isinstance(node, ast.Call):
            attr = node.func
            if isinstance(attr, ast.Attribute) and isinstance(attr.value, ast.Name):
                pair = (attr.value.id, attr.attr)
                forbidden_pairs = {
                    ("datetime", "now"),
                    ("datetime", "today"),
                    ("time", "time"),
                    ("os", "getenv"),
                }
                if pair in forbidden_pairs:
                    loc = f"{attr.value.id}.{attr.attr}()"
                    violations.append(f"{filename}:{node.lineno}: forbidden call {loc}")
            if isinstance(attr, ast.Name) and attr.id == "open":
                violations.append(f"{filename}:{node.lineno}: forbidden call open()")

    return violations


def test_domain_has_no_io_or_async_or_wallclock_reads() -> None:
    all_violations: list[str] = []
    for path in _domain_files():
        source = path.read_text()
        tree = ast.parse(source, filename=str(path))
        all_violations.extend(_iter_violations(tree, str(path.relative_to(DOMAIN_ROOT.parents[1]))))

    assert not all_violations, "domain/ purity violations:\n" + "\n".join(all_violations)


def test_domain_purity_check_fails_on_a_planted_violation(tmp_path: Path) -> None:
    planted = tmp_path / "planted.py"
    planted.write_text("import asyncpg\n\nasync def f():\n    await asyncpg.connect()\n")

    tree = ast.parse(planted.read_text(), filename=str(planted))
    violations = _iter_violations(tree, str(planted))

    assert violations, "expected the purity checker to flag a planted violation"
