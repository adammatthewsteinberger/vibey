"""Scaffold CLI — copy package-data templates into the user's repo."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from vibey_bootstrap import __version__


def _templates_root() -> Path:
    return Path(__file__).resolve().parent / "templates"


def list_templates() -> list[str]:
    root = _templates_root()
    if not root.is_dir():
        return []
    names: list[str] = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            names.append(str(path.relative_to(root)))
    return names


def _substitute(text: str, variables: dict[str, str]) -> str:
    for key, value in variables.items():
        text = text.replace(f"{{{{ {key} }}}}", value)
        text = text.replace(f"{{{{{key}}}}}", value)
    return text


def scaffold(name: str, out_dir: Path, variables: dict[str, str]) -> Path:
    root = _templates_root()
    src = root / name
    if not src.is_file():
        # Allow shorthand without category prefix when unique
        matches = list(root.rglob(Path(name).name))
        if len(matches) == 1:
            src = matches[0]
        else:
            raise FileNotFoundError(f"template not found: {name}")
    out_dir.mkdir(parents=True, exist_ok=True)
    dest_name = Path(name).name.replace(".template", "")
    dest = out_dir / dest_name
    content = _substitute(src.read_text(encoding="utf-8"), variables)
    dest.write_text(content, encoding="utf-8")
    return dest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="vibey-bootstrap", description="vibey-bootstrap scaffold CLI"
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("version", help="Print package version")
    sub.add_parser("list", help="List available templates")

    scaf = sub.add_parser("scaffold", help="Copy a template to --out")
    scaf.add_argument("name", help="Template path, e.g. helm/worker/Chart.yaml.template")
    scaf.add_argument("--out", type=Path, default=Path("."), help="Output directory")
    scaf.add_argument("--var", action="append", default=[], help="Substitution k=v")

    args = parser.parse_args(argv)
    if args.command == "version":
        print(__version__)
        return 0
    if args.command == "list":
        for t in list_templates():
            print(t)
        return 0
    if args.command == "scaffold":
        variables: dict[str, str] = {}
        for item in args.var:
            key, _, value = item.partition("=")
            if key:
                variables[key.strip()] = value
        dest = scaffold(args.name, args.out, variables)
        print(f"scaffolded {dest}")
        return 0
    parser.print_help()
    return 1


_ALIAS_WARNED = False


def main_azbootstrap(argv: list[str] | None = None) -> int:
    """Deprecated ``azbootstrap`` console script (pre-4.0 name).

    Prints a one-line deprecation warning once per process, then delegates to
    :func:`main`. Kept so existing scripts keep working; use ``vibey-bootstrap``.
    """
    global _ALIAS_WARNED
    if not _ALIAS_WARNED:
        _ALIAS_WARNED = True
        print(
            "azbootstrap: deprecated alias (renamed in 4.0.0) — use 'vibey-bootstrap' instead.",
            file=sys.stderr,
        )
    return main(argv)


if __name__ == "__main__":
    sys.exit(main())
