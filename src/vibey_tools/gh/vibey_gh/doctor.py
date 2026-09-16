# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""`vibey-gh doctor`: will this repository's automation actually work?

`check` answers "is the provenance intact?". Nothing answered the question every adoption
failure this family suffered was an instance of — "will the machinery function?" — and
each of the checks below encodes one failure that cost real debugging time on a live
repository before it was understood:

- a configuration key in the wrong section is silently ignored, so the feature it
  configures silently stays at defaults while every render looks green;
- `pr_automation.enabled` defaults true, so a repository without pr-automation.yml has a
  merge train that refuses every pull request with "gate has not passed" — green,
  mergeable, and stuck forever;
- ruff configured to select E cannot coexist with the 230-character provenance header,
  so CI fails on every stamped file;
- two workflows both deploying GitHub Pages silently contend for the same site;
- a header carrying a superseded fingerprint text sits invisible under the current one.

Everything here reads files already on disk. No network, no credentials, no execution.
"""

from __future__ import annotations

import dataclasses
import tomllib
from dataclasses import dataclass
from pathlib import Path

from vibey_gh import fingerprints
from vibey_gh.config import (
    CONFIG_NAME,
    AiConfig,
    BranchSyncConfig,
    ConversationConfig,
    DocumentationConfig,
    GhConfig,
    GithubReleaseConfig,
    IssueAutomationConfig,
    MarketplaceConfig,
    PrAutomationConfig,
    PrAutomationFallbackConfig,
    PrAutomationObservabilityConfig,
    RealignConfig,
    RepositoryProfileConfig,
    YankConfig,
)


@dataclass
class Finding:
    severity: str  # "error" | "warning"
    message: str


def _fields(cls: type) -> set[str]:
    return {f.name for f in dataclasses.fields(cls)}


# What each toml section may contain. Nested dataclasses are derived with
# dataclasses.fields so a new config field is recognised here automatically; the composite
# sections (whose keys load onto GhConfig itself) are spelled out to match the loader.
_SECTION_KEYS: dict[str, set[str] | None] = {
    "fingerprint": {"sources", "text", "superseded_texts", "trailer"},
    "version": {"files", "content_paths", "code_paths"},
    "branches": {"integration", "release"},
    "merge_train": {"owner", "trusted_authors"},
    "install": {"workflows", "pin_version", "union_merge_paths"},
    "pr_automation": _fields(PrAutomationConfig) | {"observability", "fallback"},
    "issue_automation": _fields(IssueAutomationConfig),
    "documentation": _fields(DocumentationConfig),
    "marketplace": _fields(MarketplaceConfig),
    "yank": _fields(YankConfig),
    "ai": _fields(AiConfig),
    "conversation": _fields(ConversationConfig),
    "branch_sync": _fields(BranchSyncConfig),
    "realign": _fields(RealignConfig),
    "github_release": _fields(GithubReleaseConfig),
    "repository_profile": _fields(RepositoryProfileConfig),
    # free-form: per-branch tables validated by their own machinery
    "rulesets": None,
}
_NESTED_KEYS: dict[str, set[str]] = {
    "pr_automation.observability": _fields(PrAutomationObservabilityConfig),
    "pr_automation.fallback": _fields(PrAutomationFallbackConfig),
}


def _check_unknown_keys(root: Path) -> list[Finding]:
    """A key in the wrong section is silently ignored — observed as a Google Analytics id
    that landed inside a comment-matched section and left GA_ID empty while every check
    stayed green. Naming the stray is the whole fix."""
    path = root / CONFIG_NAME
    if not path.is_file():
        return []
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    findings: list[Finding] = []
    for section, value in data.items():
        if section not in _SECTION_KEYS:
            findings.append(
                Finding(
                    "error", f"[{section}] is not a section vibey-gh reads; its keys do nothing"
                )
            )
            continue
        allowed = _SECTION_KEYS[section]
        if allowed is None or not isinstance(value, dict):
            continue
        for key, sub in value.items():
            dotted = f"{section}.{key}"
            if dotted in _NESTED_KEYS:
                for nested in sub:
                    if nested not in _NESTED_KEYS[dotted]:
                        findings.append(
                            Finding(
                                "error",
                                f"[{dotted}] {nested} is not a key vibey-gh reads; it is silently ignored",
                            )
                        )
                continue
            if key not in allowed:
                findings.append(
                    Finding(
                        "error",
                        f"[{section}] {key} is not a key vibey-gh reads; it is silently ignored",
                    )
                )
    return findings


def _check_gate_installed(cfg: GhConfig) -> list[Finding]:
    if not cfg.pr_automation.enabled:
        return []
    if (cfg.root / ".github" / "workflows" / "pr-automation.yml").is_file():
        return []
    return [
        Finding(
            "error",
            "pr_automation.enabled is true but .github/workflows/pr-automation.yml is not "
            "installed — the merge train will refuse every pull request with 'PR automation "
            'gate has not passed\'. Add "pr-automation.yml" to [install] workflows and run '
            "`vibey-gh install`, or set [pr_automation] enabled = false.",
        )
    ]


def _check_ruff_e501(cfg: GhConfig) -> list[Finding]:
    """ruff selecting E cannot coexist with the exact 230-character header `check`
    enforces byte-for-byte: every stamped file fails E501. Observed as a red CI on every
    source file the moment a repository was stamped."""
    path = cfg.root / "pyproject.toml"
    if not path.is_file():
        return []
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    lint = (data.get("tool", {}).get("ruff", {}) or {}).get("lint", {}) or {}
    select = lint.get("select", [])
    ignore = set(lint.get("ignore", []))
    selects_e = any(entry in ("E", "E5", "E501") for entry in select)
    if not selects_e or "E501" in ignore or "E" in ignore:
        return []
    limit = (data.get("tool", {}).get("ruff", {}) or {}).get("line-length", 88)
    if len(cfg.header) <= int(limit):
        return []
    return [
        Finding(
            "error",
            f"ruff selects E with line-length {limit}, and the provenance header is "
            f'{len(cfg.header)} characters — every stamped file fails E501. Add "E501" to '
            "[tool.ruff.lint] ignore; the formatter still enforces width on code.",
        )
    ]


def _check_pages_contention(cfg: GhConfig) -> list[Finding]:
    """Two workflows calling deploy-pages silently fight over one site; whichever runs
    last wins. Observed as a hand-authored docs.yml and release-surfaces.yml trading the
    front page."""
    workflows = cfg.root / ".github" / "workflows"
    if not workflows.is_dir():
        return []
    deployers = [
        p.name
        for p in sorted(workflows.glob("*.yml"))
        if "actions/deploy-pages" in p.read_text(encoding="utf-8")
    ]
    if len(deployers) <= 1:
        return []
    names = ", ".join(deployers)
    return [
        Finding(
            "error",
            f"{len(deployers)} workflows deploy GitHub Pages ({names}) — they contend for "
            "the same site and whichever runs last wins. Keep exactly one owner.",
        )
    ]


def _check_superseded_headers(cfg: GhConfig) -> list[Finding]:
    stale = [
        p
        for p in fingerprints.sources(cfg)
        if fingerprints.superseded_headers(p.read_text(encoding="utf-8"), cfg) > 0
    ]
    if not stale:
        return []
    return [
        Finding(
            "warning",
            f"{len(stale)} file(s) carry a superseded fingerprint header — "
            "`vibey-gh check --apply` replaces them in place.",
        )
    ]


def diagnose(cfg: GhConfig | None = None, root: Path | None = None) -> list[Finding]:
    from vibey_gh.config import load_config

    cfg = cfg or load_config(root)
    findings: list[Finding] = []
    findings += _check_unknown_keys(cfg.root)
    findings += _check_gate_installed(cfg)
    findings += _check_ruff_e501(cfg)
    findings += _check_pages_contention(cfg)
    findings += _check_superseded_headers(cfg)
    return findings
