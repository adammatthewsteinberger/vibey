# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Install the git hooks that enforce the automation into a consuming repository.

Installing is deliberately additive. A repository that already has its own `pre-push` or
`commit-msg` keeps it: the existing hook is moved aside to `<name>.local` and the
installed hook chains to it. Adopting this should never silently discard checks somebody
else thought were important.
"""

from __future__ import annotations

import dataclasses
import json
import shlex
import shutil
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path

from vibey_gh import __version__, dependabot
from vibey_gh.config import GhConfig, load_config

TEMPLATES = Path(__file__).parent / "templates" / "githooks"
WORKFLOWS = Path(__file__).parent / "templates" / "workflows"
PACKAGED_RELEASE_ASSETS = Path(__file__).parent / "templates" / "release"
SOURCE_RELEASE_ASSETS = Path(__file__).parent.parent / "docs"
WORKFLOWS_DIR = ".github/workflows"
RELEASE_ASSETS_DIR = ".github/vibey-gh/release"
HOOKS = ("commit-msg", "pre-push")
HOOKS_DIR = ".githooks"
GITATTRIBUTES = ".gitattributes"
UNION_MARKER = "# vibey-gh: append-only files merge instead of conflicting"


@dataclass
class Action:
    hook: str
    outcome: str  # installed | updated | unchanged | chained


def _executable(path: Path) -> None:
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _managed_workflows(cfg: GhConfig) -> list[Path]:
    """The workflow templates this repository has asked to be responsible for.

    A repository that already has its own richer workflows sets `install.workflows = []`
    and takes only the hooks and the CLI. Without this, `check` would fail forever on
    workflows it never wanted — and a check that cannot pass is a check people route
    around.
    """
    every = sorted(WORKFLOWS.glob("*.yml"))
    if cfg.managed_workflows is None:
        return every
    wanted = set(cfg.managed_workflows)
    return [p for p in every if p.name in wanted]


def _release_assets(cfg: GhConfig) -> list[tuple[Path, str]]:
    """Theme files installed only with the release-surfaces workflow.

    Source checkouts use ``docs`` directly; wheels force-include the same bytes beside
    the workflow templates. This keeps one authored copy while making installed projects
    self-contained and independent of the vibey-gh repository.
    """
    if not any(path.name == "release-surfaces.yml" for path in _managed_workflows(cfg)):
        return []
    if PACKAGED_RELEASE_ASSETS.is_dir():
        return [
            (PACKAGED_RELEASE_ASSETS / "vibey.css", "vibey.css"),
            (PACKAGED_RELEASE_ASSETS / "channel.js", "channel.js"),
        ]
    return [
        (SOURCE_RELEASE_ASSETS / "stylesheets" / "vibey.css", "vibey.css"),
        (SOURCE_RELEASE_ASSETS / "javascripts" / "channel.js", "channel.js"),
    ]


def _favicon_links(spec: str) -> str:
    """Favicon <link> tags for a spec that is either emoji or a URL/path.

    One or two emoji become a crisp zero-asset SVG data URI (the same URI serves
    apple-touch-icon so pinned tabs and home screens match); anything that looks like a
    URL or a file path is used verbatim. Computed once at render time so static pages —
    the channel index — carry it without any runtime step.
    """
    import html as _html
    import urllib.parse as _up

    spec = spec.strip()
    if not spec:
        return ""
    if spec.startswith(("http://", "https://", "/")) or "." in spec.split("/")[-1]:
        return f'<link rel="icon" href="{_html.escape(spec, quote=True)}">'
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        f'<text y="0.9em" font-size="90">{_html.escape(spec)}</text></svg>'
    )
    uri = "data:image/svg+xml," + _up.quote(svg)
    return f'<link rel="icon" href="{uri}"><link rel="apple-touch-icon" href="{uri}">'


def _strip_trailing_space(text: str) -> str:
    """Remove trailing whitespace from every rendered line.

    Substitution creates it even though no template contains any. A placeholder that
    renders empty mid-line -- `__VIBEY_GH_DOC_SITE_REQUIREMENTS__` with the default empty
    `site_requirements`, for instance -- leaves the space that separated it from the
    previous argument dangling at end of line.

    That is not cosmetic. `installed()` compares managed files against the template
    byte-for-byte, and the near-universal `trailing-whitespace` pre-commit hook strips the
    space on the adopting repository's next commit. The file then reads as out of date,
    `check` fails, and the pre-push hook refuses the push -- a formatting hook silently
    breaking provenance, surfacing at `git push` with no visible connection to its cause.
    Hit on five repositories adopting 1.38.0.

    Done here rather than per placeholder so no future one can reintroduce it.
    """
    return "\n".join(line.rstrip() for line in text.split("\n"))


def render_workflow(source: Path, cfg: GhConfig) -> str:
    wanted = source.read_text(encoding="utf-8")
    wanted = wanted.replace("__VIBEY_GH_INTEGRATION_BRANCH__", cfg.integration_branch)
    wanted = wanted.replace("__VIBEY_GH_RELEASE_BRANCH__", cfg.release_branch)
    wanted = wanted.replace("__VIBEY_GH_MODEL__", cfg.pr_automation.model)
    # Every workflow name the chain depends on, from one source: a template's own
    # `name:` and the `workflow_run` triggers that watch it render from the same
    # field, so a rename can never leave a trigger pointing at a workflow that no
    # longer answers to that name.
    for field in dataclasses.fields(cfg.workflow_names):
        wanted = wanted.replace(
            f"__VIBEY_GH_WF_{field.name.upper()}__",
            getattr(cfg.workflow_names, field.name),
        )
    # The secret's NAME, rendered inside `${{ secrets.… }}`. `AiConfig` has already refused
    # anything that is not a bare secret identifier, so this cannot close the expression.
    wanted = wanted.replace("__VIBEY_GH_AI_AUTH_SECRET__", cfg.ai.auth_secret)
    # An endpoint override is emitted as a whole `env:` block or not at all: an empty
    # `ANTHROPIC_BASE_URL` is not the same as an absent one, and would point Claude Code at
    # nothing rather than at its default. Both header conventions are filled from the one
    # secret, since Claude Code sends `x-api-key` while some gateways read `Authorization`.
    wanted = wanted.replace(
        "        # __VIBEY_GH_AI_ENV__",
        (
            "        env:\n"
            f"          ANTHROPIC_BASE_URL: {json.dumps(cfg.ai.base_url)}\n"
            "          ANTHROPIC_AUTH_TOKEN: ${{ secrets." + cfg.ai.auth_secret + " }}"
            if cfg.ai.base_url
            else "        # ai: the default Anthropic endpoint"
        ),
    )
    # The local review fallback. `enabled` renders as a literal `true`/`false` into the
    # job's `if:`, so a repository that has not opted in emits a job GitHub always skips
    # rather than one that fails looking for a runner label nobody registered.
    fallback = cfg.pr_automation.fallback
    wanted = wanted.replace(
        "__VIBEY_GH_FALLBACK_ENABLED__", "true" if fallback.enabled else "false"
    )
    wanted = wanted.replace(
        "__VIBEY_GH_ISSUE_FALLBACK_ENABLED__",
        "true" if cfg.issue_automation.fallback_enabled else "false",
    )
    wanted = wanted.replace(
        "__VIBEY_GH_FALLBACK_TRUSTED_ONLY__", "true" if fallback.trusted_only else "false"
    )
    wanted = wanted.replace("__VIBEY_GH_FALLBACK_RUNNER_LABEL__", fallback.runner_label)
    wanted = wanted.replace("__VIBEY_GH_FALLBACK_MODEL__", fallback.model)
    wanted = wanted.replace("__VIBEY_GH_FALLBACK_BASE_URL__", fallback.base_url)
    wanted = wanted.replace("__VIBEY_GH_FALLBACK_MAX_DIFF_CHARS__", str(fallback.max_diff_chars))
    wanted = wanted.replace("__VIBEY_GH_FALLBACK_TIMEOUT_SECONDS__", str(fallback.timeout_seconds))
    wanted = wanted.replace(
        "__VIBEY_GH_SANITIZED_PROGRESS__",
        "true" if cfg.pr_automation.observability.sanitized_progress else "false",
    )
    wanted = wanted.replace(
        "__VIBEY_GH_ARCHIVE_EXECUTION_FILE__",
        "true" if cfg.pr_automation.observability.archive_execution_file else "false",
    )
    wanted = wanted.replace(
        "__VIBEY_GH_ALLOW_PRIVATE_FULL_OUTPUT__",
        "true" if cfg.pr_automation.observability.allow_private_full_output else "false",
    )
    wanted = wanted.replace(
        "__VIBEY_GH_SYNC_ENABLED__", "true" if cfg.branch_sync.enabled else "false"
    )
    talk = cfg.conversation
    wanted = wanted.replace(
        "__VIBEY_GH_CONVERSATION_ENABLED__", "true" if talk.enabled else "false"
    )
    wanted = wanted.replace("__VIBEY_GH_CONVERSATION_TRIGGER__", talk.trigger)
    wanted = wanted.replace("__VIBEY_GH_CONVERSATION_MODEL__", talk.model)
    issues = cfg.issue_automation
    wanted = wanted.replace("__VIBEY_GH_ISSUE_ENABLED__", "true" if issues.enabled else "false")
    wanted = wanted.replace("__VIBEY_GH_ISSUE_MODEL__", issues.model)
    wanted = wanted.replace("__VIBEY_GH_ISSUE_MAX_TURNS__", str(issues.max_turns))
    wanted = wanted.replace("__VIBEY_GH_ISSUE_BRANCH_PREFIX__", issues.branch_prefix)
    wanted = wanted.replace("__VIBEY_GH_ISSUE_LABEL__", issues.required_label)
    wanted = wanted.replace(
        "__VIBEY_GH_ISSUE_OPEN_PR__", "true" if issues.open_pull_request else "false"
    )
    wanted = wanted.replace(
        "__VIBEY_GH_ISSUE_DRAFT_PR__", "true" if issues.draft_pull_request else "false"
    )
    wanted = wanted.replace(
        "  # __VIBEY_GH_ISSUE_SCHEDULE__",
        (
            '  schedule:\n    - cron: "19 */12 * * *"'
            if issues.retain_schedule_backstop
            else "  # schedule backstop disabled by .vibey-gh.toml"
        ),
    )
    wanted = wanted.replace(
        "__VIBEY_GH_PROFILE_ENABLED__",
        "true" if cfg.repository_profile.enabled else "false",
    )
    wanted = wanted.replace(
        "__VIBEY_GH_RULESETS_ENABLED__",
        "true" if cfg.rulesets.enabled else "false",
    )
    wanted = wanted.replace(
        "__VIBEY_GH_PROFILE_DESCRIPTION__",
        json.dumps(cfg.repository_profile.description),
    )
    wanted = wanted.replace(
        "__VIBEY_GH_PROFILE_TOPICS__",
        json.dumps({"names": list(cfg.repository_profile.topics)}, separators=(",", ":")),
    )
    profile_settings = {
        name: getattr(cfg.repository_profile, name)
        for name in (
            "has_issues",
            "has_projects",
            "has_wiki",
            "has_discussions",
            "allow_squash_merge",
            "allow_merge_commit",
            "allow_rebase_merge",
            "allow_auto_merge",
            "delete_branch_on_merge",
            "web_commit_signoff_required",
            "vulnerability_alerts",
            "automated_security_fixes",
        )
    }
    wanted = wanted.replace(
        "__VIBEY_GH_PROFILE_SETTINGS__",
        json.dumps(profile_settings, separators=(",", ":")),
    )
    wanted = wanted.replace(
        "__VIBEY_GH_DOCUMENTATION_AI__",
        "true" if cfg.documentation.ai_maintenance else "false",
    )
    wanted = wanted.replace("__VIBEY_GH_DOCUMENTATION_MODEL__", cfg.documentation.model)
    wanted = wanted.replace("__VIBEY_GH_DOC_PRODUCTION_LABEL__", cfg.documentation.production_label)
    wanted = wanted.replace("__VIBEY_GH_DOC_PREVIEW_LABEL__", cfg.documentation.preview_label)
    wanted = wanted.replace(
        "__VIBEY_GH_DOC_GOOGLE_ANALYTICS_ID__", cfg.documentation.google_analytics_id
    )
    # Shell-quoted because these land verbatim in a `pip install` line. A requirement may
    # legitimately carry spaces and brackets (`mkdocs-material[imaging] >= 9.5`), which
    # would otherwise split into several arguments or be read as a glob.
    wanted = wanted.replace(
        "__VIBEY_GH_DOC_SITE_REQUIREMENTS__",
        " ".join(shlex.quote(value) for value in cfg.documentation.site_requirements),
    )
    wanted = wanted.replace(
        "__VIBEY_GH_DOC_REQUIREMENTS_FILE__", cfg.documentation.site_requirements_file
    )
    wanted = wanted.replace("__VIBEY_GH_PROPERDOCS_VERSION__", cfg.documentation.properdocs_version)
    docs = cfg.documentation
    wanted = wanted.replace("__VIBEY_GH_DOC_FAVICON__", docs.favicon)
    wanted = wanted.replace("__VIBEY_GH_DOC_FAVICON_LINKS__", _favicon_links(docs.favicon))
    wanted = wanted.replace("__VIBEY_GH_DOC_OG_IMAGE__", docs.og_image)
    wanted = wanted.replace("__VIBEY_GH_DOC_TWITTER_SITE__", docs.twitter_site)
    wanted = wanted.replace("__VIBEY_GH_DOC_TWITTER_CREATOR__", docs.twitter_creator)
    wanted = wanted.replace("__VIBEY_GH_DOC_KEYWORDS__", ",".join(docs.keywords))
    wanted = wanted.replace("__VIBEY_GH_DOC_AUTHOR__", docs.author)
    wanted = wanted.replace("__VIBEY_GH_DOC_FUNDING_BITCOIN__", docs.funding_bitcoin)
    wanted = wanted.replace("__VIBEY_GH_DOC_FUNDING_MONERO__", docs.funding_monero)
    wanted = wanted.replace("__VIBEY_GH_DOC_FUNDING_ETHEREUM__", docs.funding_ethereum)
    wanted = wanted.replace("__VIBEY_GH_DOC_FUNDING_LABEL__", docs.funding_label)
    wanted = wanted.replace("__VIBEY_GH_DOC_THEME_COLOR__", docs.theme_color)
    wanted = wanted.replace("__VIBEY_GH_DOC_LOCALE__", docs.locale)
    wanted = wanted.replace("__VIBEY_GH_DOC_SITE_VERIFICATION__", docs.google_site_verification)
    wanted = wanted.replace(
        "__VIBEY_GH_DOC_SITE_VERIFICATION_TAG__",
        (
            (f'<meta name="google-site-verification" content="{docs.google_site_verification}">')
            if docs.google_site_verification
            else ""
        ),
    )
    wanted = wanted.replace(
        "__VIBEY_GH_DOCUMENTATION_FILES__",
        json.dumps(list(cfg.documentation.required_files)),
    )
    for marker, enabled in (
        ("__VIBEY_GH_DOC_ROBOTS__", cfg.documentation.generate_robots),
        ("__VIBEY_GH_DOC_SITEMAP_INDEX__", cfg.documentation.generate_sitemap_index),
        ("__VIBEY_GH_DOC_LLMS__", cfg.documentation.generate_llms_txt),
        ("__VIBEY_GH_DOC_LLMS_FULL__", cfg.documentation.generate_llms_full_txt),
        ("__VIBEY_GH_DOC_JSON_LD__", cfg.documentation.generate_json_ld),
        ("__VIBEY_GH_DOC_BOOK__", cfg.documentation.generate_book),
        ("__VIBEY_GH_DOC_PAPER__", cfg.documentation.generate_paper),
        ("__VIBEY_GH_DOC_BOTTOM_NAV__", cfg.documentation.bottom_nav),
        ("__VIBEY_GH_DOC_PRODUCTION_INDEX__", cfg.documentation.production_indexing),
        ("__VIBEY_GH_DOC_PREVIEW_INDEX__", cfg.documentation.preview_indexing),
        ("__VIBEY_GH_SOCIAL_SIGNALS__", cfg.social_signals.enabled),
        ("__VIBEY_GH_GITHUB_RELEASE_ENABLED__", cfg.github_release.enabled),
    ):
        wanted = wanted.replace(marker, "true" if enabled else "false")
    wanted = wanted.replace("__VIBEY_GH_RELEASE_TAG_PREFIX__", cfg.github_release.tag_prefix)
    wanted = wanted.replace("__VIBEY_GH_SELF_SOURCE__", cfg.self_source)
    if cfg.pin_version:
        # Only the floating fallback install is pinned. The self-hosting branch just
        # above it (`pip install --quiet -e .`) must keep installing from source: this
        # repository cannot pin itself to a published release that may not exist yet.
        wanted = wanted.replace(
            "python -m pip install --quiet vibey-gh\n",
            f'python -m pip install --quiet "vibey-gh=={__version__}"\n',
        )
    if source.name != "pr-automation.yml":
        return _strip_trailing_space(wanted)
    # One marketplace or plugin per line of the action's newline-separated input. A
    # repository-relative marketplace resolves inside the trusted default-branch checkout
    # every plugin-loading job makes at `automation/`, as an absolute path, which is the
    # form the action passes to Claude Code as a local marketplace.
    indent = "\n            "
    marketplaces = [
        entry if entry.startswith("https://") else "${{ github.workspace }}/automation/" + entry
        for entry in cfg.pr_automation.plugin_marketplaces
    ]
    wanted = wanted.replace("__VIBEY_GH_PLUGIN_MARKETPLACES__", indent.join(marketplaces))
    wanted = wanted.replace("__VIBEY_GH_PLUGINS__", indent.join(cfg.pr_automation.plugins))
    workflows = json.dumps(list(cfg.pr_automation.scan_workflows))
    schedule = (
        '  schedule:\n    - cron: "37 */2 * * *"'
        if cfg.pr_automation.retain_schedule_backstop
        else "  # schedule backstop disabled by .vibey-gh.toml"
    )
    return _strip_trailing_space(
        wanted.replace("__VIBEY_GH_SCAN_WORKFLOWS__", workflows).replace(
            "  # __VIBEY_GH_SCHEDULE__", schedule
        )
    )


def installation_notices() -> tuple[str, ...]:
    """Best-effort secret inventory plus settings the GitHub API cannot infer safely."""
    notices = [
        "enable Actions read/write permissions and allow Actions to create pull requests",
    ]
    run = subprocess.run(
        ["gh", "secret", "list", "--json", "name"], capture_output=True, text=True, check=False
    )
    if run.returncode == 0:
        try:
            present = {str(item["name"]) for item in json.loads(run.stdout)}
        except (json.JSONDecodeError, KeyError, TypeError):
            present = set()
        for name in ("ANTHROPIC_API_KEY", "AUTOMERGE_TOKEN"):
            if name not in present:
                notices.append(f"configure repository secret {name}")
    return tuple(notices)


def union_merge_lines(cfg: GhConfig) -> list[str]:
    return [f"{path} merge=union" for path in cfg.union_merge_paths]


def missing_union_merge_lines(cfg: GhConfig) -> list[str]:
    """Which `merge=union` declarations `.gitattributes` does not already carry."""
    path = cfg.root / GITATTRIBUTES
    existing = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    present = {line.strip() for line in existing}
    return [line for line in union_merge_lines(cfg) if line not in present]


def apply_union_merge(cfg: GhConfig) -> str | None:
    """Append the missing declarations, never rewriting what is already there.

    Every branch appends to the changelog, so two branches almost always touch the same
    lines and every merge strands the others — a conflict that carries no information and
    has to be resolved by hand each time. Git's `union` driver keeps both sides instead.

    It only works from the branch being merged *into*, so this file has to be committed on
    the integration branch to have any effect on the topic branches that follow.

    A repository's own `.gitattributes` is its own: this appends and never rewrites, so an
    adopter's existing rules survive adoption untouched.
    """
    missing = missing_union_merge_lines(cfg)
    if not missing:
        return None
    path = cfg.root / GITATTRIBUTES
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    outcome = "updated" if existing else "installed"
    block = "\n".join([UNION_MARKER, *missing])
    if existing and not existing.endswith("\n"):
        existing += "\n"
    prefix = f"{existing}\n" if existing else ""
    path.write_text(f"{prefix}{block}\n", encoding="utf-8")
    return outcome


def install(cfg: GhConfig | None = None, hooks_path: bool = True) -> list[Action]:
    cfg = cfg or load_config()
    target = cfg.root / HOOKS_DIR
    target.mkdir(parents=True, exist_ok=True)
    actions: list[Action] = []

    for hook in HOOKS:
        source = TEMPLATES / hook
        dest = target / hook
        wanted = source.read_text(encoding="utf-8")

        if dest.exists():
            existing = dest.read_text(encoding="utf-8")
            if existing == wanted:
                actions.append(Action(hook, "unchanged"))
                continue
            # Someone else's hook: preserve it and chain rather than overwrite.
            if "vibey-gh" not in existing:
                local = target / f"{hook}.local"
                if not local.exists():
                    shutil.move(str(dest), str(local))
                    _executable(local)
                    actions.append(Action(hook, "chained"))
                dest.write_text(wanted, encoding="utf-8")
                _executable(dest)
                continue
            dest.write_text(wanted, encoding="utf-8")
            _executable(dest)
            actions.append(Action(hook, "updated"))
            continue

        dest.write_text(wanted, encoding="utf-8")
        _executable(dest)
        actions.append(Action(hook, "installed"))

    # Workflows are copied, not chained: a workflow file is standalone and a stale copy
    # is worse than none, so an out-of-date one is replaced outright.
    wf_target = cfg.root / WORKFLOWS_DIR
    wf_target.mkdir(parents=True, exist_ok=True)
    for source in _managed_workflows(cfg):
        dest = wf_target / source.name
        wanted = render_workflow(source, cfg)
        if dest.exists() and dest.read_text(encoding="utf-8") == wanted:
            actions.append(Action(f"{WORKFLOWS_DIR}/{source.name}", "unchanged"))
            continue
        outcome = "updated" if dest.exists() else "installed"
        dest.write_text(wanted, encoding="utf-8")
        actions.append(Action(f"{WORKFLOWS_DIR}/{source.name}", outcome))

    asset_target = cfg.root / RELEASE_ASSETS_DIR
    for source, name in _release_assets(cfg):
        asset_target.mkdir(parents=True, exist_ok=True)
        dest = asset_target / name
        wanted = source.read_text(encoding="utf-8")
        if dest.exists() and dest.read_text(encoding="utf-8") == wanted:
            actions.append(Action(f"{RELEASE_ASSETS_DIR}/{name}", "unchanged"))
            continue
        outcome = "updated" if dest.exists() else "installed"
        dest.write_text(wanted, encoding="utf-8")
        actions.append(Action(f"{RELEASE_ASSETS_DIR}/{name}", outcome))

    # Written only when absent (#273). An existing config belongs to the adopter, and
    # rewriting it here — with string surgery, in a package carrying no YAML dependency —
    # risks turning a lint into an outage. `installed()` reports that case instead, with
    # the exact lines to add.
    config = cfg.root / dependabot.DEPENDABOT_PATH
    pins = dependabot.template_actions(_managed_workflows(cfg))
    if pins:  # a repository that took no workflows has no managed pins to protect
        if config.exists():
            actions.append(Action(dependabot.DEPENDABOT_PATH, "unchanged"))
        else:
            config.parent.mkdir(parents=True, exist_ok=True)
            config.write_text(dependabot.desired_config(pins), encoding="utf-8")
            actions.append(Action(dependabot.DEPENDABOT_PATH, "installed"))

    attributes = apply_union_merge(cfg)
    actions.append(Action(GITATTRIBUTES, attributes or "unchanged"))

    if hooks_path:
        subprocess.run(
            ["git", "config", "core.hooksPath", HOOKS_DIR],
            cwd=cfg.root,
            check=False,
            capture_output=True,
        )
    return actions


def installed(cfg: GhConfig | None = None, local: bool = True) -> tuple[bool, list[str]]:
    """Whether the hooks are present, current, and — when `local` — actually wired up.

    The two halves are deliberately separable. Whether the hook FILES are committed and
    current is repository state, and CI can and should check it. Whether `core.hooksPath`
    points at them is per-clone local git config that no CI checkout will ever have, so
    asserting it on a runner would fail every build for a condition that cannot hold there.
    """
    cfg = cfg or load_config()
    problems: list[str] = []
    target = cfg.root / HOOKS_DIR

    for hook in HOOKS:
        dest = target / hook
        if not dest.exists():
            problems.append(f"{HOOKS_DIR}/{hook} is missing")
        elif dest.read_text(encoding="utf-8") != (TEMPLATES / hook).read_text(encoding="utf-8"):
            problems.append(f"{HOOKS_DIR}/{hook} is out of date")

    for source in _managed_workflows(cfg):
        dest = cfg.root / WORKFLOWS_DIR / source.name
        if not dest.exists():
            problems.append(f"{WORKFLOWS_DIR}/{source.name} is missing")
        else:
            existing, wanted = dest.read_text(encoding="utf-8"), render_workflow(source, cfg)
            if existing != wanted:
                problem = f"{WORKFLOWS_DIR}/{source.name} is out of date"
                # Name the likeliest cause when the drift has its signature (#273). "Out
                # of date" alone sent one diagnosis through three wrong hypotheses before
                # a dependabot merge timestamp gave it away.
                if dependabot.differs_only_in_action_pins(existing, wanted):
                    problem += (
                        " — it differs ONLY in action pins, which is the signature of a bot"
                        " edit. This file is managed: its pins come from the vibey-gh"
                        " template and arrive with a vibey-gh upgrade. Re-render with"
                        " `vibey-gh install`, then ignore these actions in"
                        f" {dependabot.DEPENDABOT_PATH} so it cannot recur"
                    )
                problems.append(problem)

    for source, name in _release_assets(cfg):
        dest = cfg.root / RELEASE_ASSETS_DIR / name
        if not dest.exists():
            problems.append(f"{RELEASE_ASSETS_DIR}/{name} is missing")
        elif dest.read_text(encoding="utf-8") != source.read_text(encoding="utf-8"):
            problems.append(f"{RELEASE_ASSETS_DIR}/{name} is out of date")

    # A present-but-unprotected dependabot config is the state that breaks managed
    # workflows on the next action release. Reported rather than rewritten: the file is
    # the adopter's, and the fix is three lines they can read.
    exposed = dependabot.unprotected_actions(
        cfg.root, dependabot.template_actions(_managed_workflows(cfg))
    )
    if exposed:
        problems.append(
            f"{dependabot.DEPENDABOT_PATH} lets dependabot bump actions the managed"
            " workflows pin, which makes them stop matching their templates and refuses"
            " every push from the branch. Add under the github-actions ecosystem's"
            " `ignore:` — " + ", ".join(f"`dependency-name: {name}`" for name in exposed)
        )

    for line in missing_union_merge_lines(cfg):
        problems.append(f"{GITATTRIBUTES} is missing `{line}`")

    if local:
        import subprocess

        result = subprocess.run(
            ["git", "config", "--get", "core.hooksPath"],
            cwd=cfg.root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.stdout.strip() != HOOKS_DIR:
            problems.append(f"core.hooksPath is not {HOOKS_DIR} — run `vibey-gh install`")

    return (not problems), problems
