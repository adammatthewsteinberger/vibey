# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Command-line interface for vibey-skills.

``argparse`` and the stdlib only — installing a pile of Markdown should not drag in a
dependency tree.

Commands:
    list         show plugins, their skills, and trigger descriptions
    install      copy skill directories into ~/.claude/skills (or --dest)
    path         print the packaged plugins root
    marketplace  print the packaged marketplace.json path, for /plugin marketplace add

The console script is ``vibey-skills``. ``vibe-skills`` — the short alias from the
``vibe-engineering-skills`` era — is kept as a deprecated entry point that prints one
warning line and then delegates here unchanged.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from . import (
    __version__,
    iter_skills,
    marketplace_manifest,
    marketplace_manifest_path,
    plugins_root,
)

DEFAULT_DEST = Path.home() / ".claude" / "skills"
DEFAULT_INDEX = Path(".vibey-skills/index")


# --------------------------------------------------------------------------- helpers


def _plugin_names() -> list[str]:
    return [entry["name"] for entry in marketplace_manifest().get("plugins", [])]


def _resolve_within(base: Path, name: str) -> Path:
    """Join ``name`` onto ``base`` and refuse anything that escapes it.

    Skill names come from directory names inside the package, so this should never trip —
    but an installer that writes outside its target directory is the one bug in this tool
    that would actually matter, so it is checked rather than assumed.
    """
    candidate = (base / name).resolve()
    if candidate != base.resolve() and base.resolve() not in candidate.parents:
        raise ValueError(f"refusing to write outside {base}: {name!r}")
    return candidate


def _copy_skill(source: Path, dest: Path, *, link: bool) -> None:
    if link:
        dest.symlink_to(source, target_is_directory=True)
    else:
        shutil.copytree(source, dest)


# --------------------------------------------------------------------------- commands


def cmd_list(args: argparse.Namespace) -> int:
    manifest = marketplace_manifest()
    entries = manifest.get("plugins", [])
    if args.plugin:
        entries = [e for e in entries if e["name"] == args.plugin]
        if not entries:
            print(
                f"vibey-skills: no such plugin {args.plugin!r}. "
                f"Known plugins: {', '.join(_plugin_names())}",
                file=sys.stderr,
            )
            return 1

    skills_by_plugin: dict[str, list] = {}
    for skill in iter_skills(args.plugin):
        skills_by_plugin.setdefault(skill.plugin, []).append(skill)

    if args.json:
        payload = {
            "version": manifest.get("metadata", {}).get("version", __version__),
            "plugins": [
                {
                    "name": entry["name"],
                    "version": entry.get("version"),
                    "category": entry.get("category"),
                    "description": entry.get("description"),
                    "skills": [
                        {"name": s.name, "description": s.description}
                        for s in skills_by_plugin.get(entry["name"], [])
                    ],
                }
                for entry in entries
            ],
        }
        json.dump(payload, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
        return 0

    total = 0
    for entry in entries:
        skills = skills_by_plugin.get(entry["name"], [])
        total += len(skills)
        header = f"{entry['name']}  ({entry.get('version', '?')}"
        if entry.get("category"):
            header += f", {entry['category']}"
        header += f", {len(skills)} skill{'s' if len(skills) != 1 else ''})"
        print(header)
        for skill in skills:
            print(f"  - {skill.name}")
            if args.plugin and skill.description:
                # Only the focused view prints triggers; the full list would be unreadable.
                print(f"      {skill.description}")
        print()

    plural = "s" if len(entries) != 1 else ""
    print(f"{len(entries)} plugin{plural}, {total} skills")
    if not args.plugin:
        print("Run 'vibey-skills list --plugin <name>' to see trigger descriptions.")
    return 0


def cmd_install(args: argparse.Namespace) -> int:
    known = _plugin_names()

    if args.all:
        selected: list[str] | None = None
    elif args.plugins:
        unknown = [p for p in args.plugins if p not in known]
        if unknown:
            print(
                f"vibey-skills: unknown plugin(s): {', '.join(unknown)}\n"
                f"Known plugins: {', '.join(known)}",
                file=sys.stderr,
            )
            return 1
        selected = args.plugins
    else:
        print(
            "vibey-skills: name at least one plugin, or pass --all.\n"
            f"Known plugins: {', '.join(known)}",
            file=sys.stderr,
        )
        return 1

    skills = []
    if selected is None:
        skills = list(iter_skills())
    else:
        for name in selected:
            skills.extend(iter_skills(name))

    if not skills:
        print("vibey-skills: nothing to install.", file=sys.stderr)
        return 1

    dest_root = Path(args.dest).expanduser()

    planned: list[tuple[Path, Path]] = []
    skipped: list[str] = []
    for skill in skills:
        try:
            target = _resolve_within(dest_root, skill.name)
        except ValueError as exc:
            print(f"vibey-skills: {exc}", file=sys.stderr)
            return 1
        # cp -n semantics: an existing directory is left completely alone unless --force.
        # A hand-edited local skill is worth more than this package's copy of it.
        if target.exists() or target.is_symlink():
            if args.force:
                planned.append((skill.directory, target))
            else:
                skipped.append(skill.name)
        else:
            planned.append((skill.directory, target))

    verb, verbed = ("link", "linked") if args.link else ("copy", "copied")
    if args.dry_run:
        print(f"vibey-skills: dry run — nothing will be written to {dest_root}")
        for source, target in planned:
            action = f"replace (--force) and {verb}" if target.exists() else verb
            print(f"  {action}: {source} -> {target}")
        if skipped:
            print(f"  skip (already present): {', '.join(sorted(skipped))}")
        print(
            f"\n{len(planned)} skill(s) would be {verbed}, {len(skipped)} skipped, into {dest_root}"
        )
        return 0

    dest_root.mkdir(parents=True, exist_ok=True)

    installed = 0
    for source, target in planned:
        if target.exists() or target.is_symlink():
            if target.is_symlink() or target.is_file():
                target.unlink()
            else:
                shutil.rmtree(target)
        _copy_skill(source, target, link=args.link)
        installed += 1

    if installed or not skipped:
        print(f"vibey-skills: {verbed} {installed} skill(s) into {dest_root}")
    if skipped:
        names = ", ".join(sorted(skipped))
        print(
            f"{len(skipped)} skill(s) already present, skipped: {names} "
            "— re-run with --force to overwrite"
        )
    return 0


def cmd_path(_args: argparse.Namespace) -> int:
    print(plugins_root())
    return 0


def cmd_marketplace(_args: argparse.Namespace) -> int:
    print(marketplace_manifest_path())
    return 0


def cmd_index_build(args: argparse.Namespace) -> int:
    from .context_engine import build_index, inspect_index

    build_index(Path(args.output))
    json.dump(inspect_index(Path(args.output)), sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


def cmd_index_inspect(args: argparse.Namespace) -> int:
    from .context_engine import inspect_index

    result = inspect_index(Path(args.index))
    if args.json:
        json.dump(result, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        for key, value in result.items():
            print(f"{key}: {value}")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    from .context_engine import search

    result = search(Path(args.index), args.query, limit=args.limit)
    if args.json:
        json.dump(result, sys.stdout, indent=2, ensure_ascii=False, sort_keys=True)
        sys.stdout.write("\n")
    else:
        for item in result:
            print(
                f"{item['score']:10.4f}  {item['plugin']}/{item['skill']}  {' > '.join(item['heading_path'])}"
            )
    return 0


def cmd_packet(args: argparse.Namespace) -> int:
    from .context_engine import compile_packet

    request = json.loads(Path(args.request).read_text(encoding="utf-8"))
    markdown, manifest = compile_packet(Path(args.index), request, budget=args.budget)
    Path(args.output).write_text(markdown, encoding="utf-8")
    Path(args.manifest).write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0 if manifest["status"] == "ok" else 2


def cmd_evaluate(args: argparse.Namespace) -> int:
    from .context_engine import evaluate

    result = evaluate(Path(args.index), Path(args.cases), top_k=args.top_k)
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False, sort_keys=True)
    sys.stdout.write("\n")
    return 0 if result["passed_mandatory_recall"] else 2


# --------------------------------------------------------------------------- parser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vibey-skills",
        description=(
            "Agent Skills for vibe engineering — browse and install the "
            "vibey-skills plugin marketplace."
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command")

    p_list = sub.add_parser("list", help="list plugins and their skills")
    p_list.add_argument("--plugin", help="show only this plugin, with trigger descriptions")
    p_list.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    p_list.set_defaults(func=cmd_list)

    p_install = sub.add_parser("install", help="install skills into ~/.claude/skills")
    p_install.add_argument("plugins", nargs="*", help="plugin name(s) to install")
    p_install.add_argument("--all", action="store_true", help="install every plugin's skills")
    p_install.add_argument(
        "--dest",
        default=str(DEFAULT_DEST),
        help=f"destination directory (default: {DEFAULT_DEST})",
    )
    p_install.add_argument(
        "--link",
        action="store_true",
        help="symlink each skill instead of copying it",
    )
    p_install.add_argument(
        "--force",
        action="store_true",
        help="overwrite skill directories that already exist",
    )
    p_install.add_argument(
        "--dry-run",
        action="store_true",
        help="print what would happen and write nothing",
    )
    p_install.set_defaults(func=cmd_install)

    p_path = sub.add_parser("path", help="print the packaged plugins root")
    p_path.set_defaults(func=cmd_path)

    p_market = sub.add_parser(
        "marketplace",
        help="print the packaged marketplace.json path, for /plugin marketplace add",
    )
    p_market.set_defaults(func=cmd_marketplace)

    p_index = sub.add_parser("index", help="build or inspect a local lexical index")
    index_sub = p_index.add_subparsers(dest="index_command")
    p_index_build = index_sub.add_parser("build", help="build a deterministic FTS5 index")
    p_index_build.add_argument("--output", default=str(DEFAULT_INDEX))
    p_index_build.set_defaults(func=cmd_index_build)
    p_index_inspect = index_sub.add_parser("inspect", help="inspect an index")
    p_index_inspect.add_argument("index")
    p_index_inspect.add_argument("--json", action="store_true")
    p_index_inspect.set_defaults(func=cmd_index_inspect)

    p_search = sub.add_parser("search", help="search indexed skill sections")
    p_search.add_argument("query")
    p_search.add_argument("--index", default=str(DEFAULT_INDEX))
    p_search.add_argument("--limit", type=int, default=20)
    p_search.add_argument("--json", action="store_true")
    p_search.set_defaults(func=cmd_search)

    p_packet = sub.add_parser("packet", help="compile a bounded context packet")
    p_packet.add_argument("--request", required=True)
    p_packet.add_argument("--index", default=str(DEFAULT_INDEX))
    p_packet.add_argument("--budget", type=int)
    p_packet.add_argument("--output", required=True)
    p_packet.add_argument("--manifest", required=True)
    p_packet.set_defaults(func=cmd_packet)

    p_evaluate = sub.add_parser("evaluate", help="evaluate retrieval against a gold case set")
    p_evaluate.add_argument("--cases", required=True)
    p_evaluate.add_argument("--index", default=str(DEFAULT_INDEX))
    p_evaluate.add_argument("--top-k", type=int, default=10)
    p_evaluate.set_defaults(func=cmd_evaluate)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 1
    try:
        return args.func(args)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"vibey-skills: {exc}", file=sys.stderr)
        return 1
    except BrokenPipeError:
        # `vibey-skills list | head` should exit quietly rather than dumping a traceback.
        return 0


DEPRECATED_ALIAS_WARNING = (
    "vibe-skills: this command name is deprecated and will be removed in a future release; "
    "use `vibey-skills` (the package is now `vibey-skills` on PyPI)."
)


def deprecated_alias_main(argv: list[str] | None = None) -> int:
    """Entry point for the legacy ``vibe-skills`` console script.

    Prints a single deprecation line to stderr, then behaves exactly like :func:`main`.
    Kept so that existing shell history, scripts, and docs keep working across the
    ``vibe-engineering-skills`` → ``vibey-skills`` rename.
    """
    print(DEPRECATED_ALIAS_WARNING, file=sys.stderr)
    return main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
