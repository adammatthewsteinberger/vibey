# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""One Claude Code marketplace at the repository root, rendered from the workspace members.

`/plugin marketplace add owner/repo` reads exactly one file: `<repo>/.claude-plugin/
marketplace.json`. A monorepo that absorbed its plugin marketplaces as workspace members
(vibey ADR-0021) keeps each member's manifest where that member's own package expects it,
which leaves the root with nothing for the shorthand to read. This module renders the root
manifest FROM the members' manifests — built at reconcile time, never hand-maintained,
never a second source of truth (the corpus-index pattern) — and `check` reports drift, so
the shorthand keeps working as members grow.

Three properties are load-bearing:

- **deterministic**: the same members always produce the same bytes;
- **contained**: every rewritten plugin source is a `./`-relative path inside the root,
  which is all Claude Code resolves — no `../`, no absolute paths, no backslashes;
- **a name of its own**: Claude Code registers one marketplace per name per user, and each
  member's package still ships its own manifest under its own name, so the root carries
  `[marketplace] name` rather than borrowing a member's.
"""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
from typing import Any

from vibey_gh.config import GhConfig

__all__ = ["MANIFEST_PATH", "SCHEMA_URL", "MarketplaceError", "MarketplaceRenderer"]

# Where Claude Code looks, and the only place it looks. Fixed by the consumer, so it is a
# constant here and not a configuration key.
MANIFEST_PATH = ".claude-plugin/marketplace.json"
SCHEMA_URL = "https://json.schemastore.org/claude-code-marketplace.json"


class MarketplaceError(ValueError):
    """A member the root marketplace cannot be rendered from."""


class MarketplaceRenderer:
    """Implements `MarketplaceRendererInterface` against the members on disk."""

    def build(self, cfg: GhConfig) -> dict[str, Any]:
        members = cfg.marketplace.members
        if not members:
            raise MarketplaceError("[marketplace] members is empty — nothing to render")
        plugins: list[dict[str, Any]] = []
        declared_by: dict[str, str] = {}
        recorded: list[dict[str, str]] = []
        owner: dict[str, Any] = {}
        for member in members:
            manifest = self._member(cfg, member)
            if not owner:
                owner = manifest["owner"]
            # The schema keeps a marketplace's version under `metadata`; older manifests
            # wrote it at the top level. Record whichever the member has, else nothing.
            version = manifest.get("metadata", {}).get("version") or manifest.get("version", "")
            recorded.append({"path": member, "name": manifest["name"], "version": str(version)})
            for entry in manifest["plugins"]:
                plugin = self._plugin(cfg, member, entry)
                name = plugin["name"]
                if name in declared_by:
                    raise MarketplaceError(
                        f"plugin {name!r} is declared by both {declared_by[name]} and {member}"
                    )
                declared_by[name] = member
                plugins.append(plugin)
        description = cfg.marketplace.description or (
            f"Every Claude Code plugin in this repository: {len(plugins)} plugin(s)"
            f" from {', '.join(members)}."
        )
        return {
            "$schema": SCHEMA_URL,
            "name": cfg.marketplace.name,
            "owner": owner,
            "metadata": {"description": description, "members": recorded},
            "plugins": plugins,
        }

    def render(self, cfg: GhConfig) -> str:
        return self._dumps(self.build(cfg))

    def write(self, cfg: GhConfig) -> Path:
        target = cfg.root / MANIFEST_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.render(cfg), encoding="utf-8")
        return target

    def check(self, cfg: GhConfig) -> tuple[bool, str]:
        try:
            manifest = self.build(cfg)
        except MarketplaceError as exc:
            return False, str(exc)
        target = cfg.root / MANIFEST_PATH
        if not target.is_file():
            return False, f"{MANIFEST_PATH} is missing — run `vibey-gh marketplace`"
        if target.read_text(encoding="utf-8") != self._dumps(manifest):
            return False, (
                f"{MANIFEST_PATH} is out of date with its members — run `vibey-gh marketplace`"
            )
        return True, (
            f"{MANIFEST_PATH} matches its {len(cfg.marketplace.members)} member(s):"
            f" {len(manifest['plugins'])} plugin(s) as {manifest['name']!r}"
        )

    @staticmethod
    def _dumps(manifest: dict[str, Any]) -> str:
        return json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"

    @staticmethod
    def _member(cfg: GhConfig, member: str) -> dict[str, Any]:
        """A member's own manifest, validated to the shape the root can be built from."""
        path = cfg.root / member / MANIFEST_PATH
        where = f"{member}/{MANIFEST_PATH}"
        if not path.is_file():
            raise MarketplaceError(f"{where} is missing")
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise MarketplaceError(f"{where} is invalid JSON: {exc}") from exc
        if not isinstance(manifest, dict) or not isinstance(manifest.get("name"), str):
            raise MarketplaceError(f"{where} has no name")
        owner = manifest.get("owner")
        if not isinstance(owner, dict) or not owner.get("name"):
            raise MarketplaceError(f"{where} declares no owner")
        plugins = manifest.get("plugins")
        if not isinstance(plugins, list) or not plugins:
            raise MarketplaceError(f"{where} has no plugins")
        return manifest

    @staticmethod
    def _plugin(cfg: GhConfig, member: str, entry: Any) -> dict[str, Any]:
        """One plugin entry, its `./` source re-rooted from the member to the repository.

        A source that is not a string is a remote one (a `github`/`url` object); it is not
        relative to the member and passes through untouched.
        """
        if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
            raise MarketplaceError(f"{member}: a plugin entry has no name")
        name = entry["name"]
        if "source" not in entry:
            raise MarketplaceError(f"{member}: plugin {name!r} has no source")
        source = entry["source"]
        if not isinstance(source, str):
            return dict(entry)
        if not source.startswith("./") or "\\" in source or ".." in PurePosixPath(source).parts:
            raise MarketplaceError(
                f"{member}: plugin {name!r} source must be a ./-relative path inside the"
                f" member: {source!r}"
            )
        relative = PurePosixPath(member) / source[2:]
        rewritten = f"./{relative.as_posix()}"
        if not (cfg.root / relative / ".claude-plugin/plugin.json").is_file():
            raise MarketplaceError(
                f"{member}: plugin {name!r} has no .claude-plugin/plugin.json at {rewritten}"
            )
        return {**entry, "source": rewritten}
