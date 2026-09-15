# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Keeping dependabot out of managed workflows (#273)."""

from __future__ import annotations

from pathlib import Path

from vibey_gh import install
from vibey_gh.config import GhConfig
from vibey_gh.dependabot import (
    DEPENDABOT_PATH,
    desired_config,
    differs_only_in_action_pins,
    template_actions,
    unprotected_actions,
)

WORKFLOWS = Path(install.__file__).parent / "templates" / "workflows"


def test_the_ignore_list_is_derived_from_the_templates_not_hand_maintained():
    """A hand-kept list goes stale the first time a template adds an action, and the
    staleness is silent — the unlisted action is the one that breaks the next release."""
    actions = template_actions(sorted(WORKFLOWS.glob("*.yml")))
    assert "actions/checkout" in actions and "actions/setup-python" in actions
    assert "anthropics/claude-code-action" in actions
    assert actions == tuple(sorted(set(actions)))
    # `owner/repo` only: dependabot names dependencies that way, and a pinned subpath
    # (`github/codeql-action/init`) is the same dependency as its parent.
    assert all(name.count("/") == 1 for name in actions), actions


def test_only_real_action_dependencies_are_listed(tmp_path: Path):
    """Local and docker `uses:` are not github-actions dependencies; naming them would
    produce an ignore rule matching nothing, which reads as protection and is not."""
    wf = tmp_path / "w.yml"
    wf.write_text(
        "jobs:\n  a:\n    steps:\n"
        "      - uses: actions/checkout@11d5960\n"
        "      - uses: github/codeql-action/init@abc123\n"
        "      - uses: ./.github/actions/local\n"
        "      - uses: docker://alpine:3\n",
        encoding="utf-8",
    )
    assert template_actions([wf]) == ("actions/checkout", "github/codeql-action")


def test_an_unreadable_template_is_skipped_rather_than_fatal(tmp_path: Path):
    assert template_actions([tmp_path / "gone.yml"]) == ()


def test_the_written_config_names_every_managed_pin():
    actions = ("actions/checkout", "anthropics/claude-code-action")
    text = desired_config(actions)
    for name in actions:
        assert f"      - dependency-name: {name}" in text
    assert "package-ecosystem: github-actions" in text
    # The comment has to carry the *consequence*, because the person who meets this file
    # is usually the one wondering why their dependabot PR was a bad idea.
    assert "refuse every push" in text
    assert "Dependabot cannot ignore a FILE" in text


def test_no_dependabot_config_means_nothing_is_exposed(tmp_path: Path):
    """Nothing is scanning the repository, so there is nothing to protect against."""
    assert unprotected_actions(tmp_path, ("actions/checkout",)) == ()


def test_a_config_without_the_github_actions_ecosystem_is_not_exposed(tmp_path: Path):
    (tmp_path / ".github").mkdir()
    (tmp_path / DEPENDABOT_PATH).write_text(
        "version: 2\nupdates:\n  - package-ecosystem: pip\n    directory: /\n", encoding="utf-8"
    )
    assert unprotected_actions(tmp_path, ("actions/checkout",)) == ()


def test_a_scanning_config_reports_exactly_the_pins_it_leaves_open(tmp_path: Path):
    """The real shape observed across adopters: a github-actions ecosystem with no
    `ignore:` at all, or one covering some pins but not the ones a later template added."""
    (tmp_path / ".github").mkdir()
    config = tmp_path / DEPENDABOT_PATH
    wanted = ("actions/checkout", "actions/setup-python", "anthropics/claude-code-action")

    config.write_text(
        "version: 2\nupdates:\n  - package-ecosystem: github-actions\n    directory: /\n",
        encoding="utf-8",
    )
    assert unprotected_actions(tmp_path, wanted) == wanted

    config.write_text(
        "version: 2\nupdates:\n  - package-ecosystem: github-actions\n"
        "    ignore:\n"
        "      - dependency-name: actions/checkout\n"
        '      - dependency-name: "actions/setup-python"\n',
        encoding="utf-8",
    )
    assert unprotected_actions(tmp_path, wanted) == ("anthropics/claude-code-action",)


def test_a_prefix_match_is_not_protection(tmp_path: Path):
    """`actions/checkout` must not be considered covered by `actions/checkout-extra`."""
    (tmp_path / ".github").mkdir()
    (tmp_path / DEPENDABOT_PATH).write_text(
        "version: 2\nupdates:\n  - package-ecosystem: github-actions\n"
        "    ignore:\n      - dependency-name: actions/checkout-extra\n",
        encoding="utf-8",
    )
    assert unprotected_actions(tmp_path, ("actions/checkout",)) == ("actions/checkout",)


def test_pin_only_drift_is_recognised_and_nothing_else_is():
    """The signature of a bot edit: same shape, same length, only `uses:` refs moved."""
    base = "name: CI\njobs:\n  a:\n    steps:\n      - uses: actions/checkout@aaa # v4\n"
    bumped = base.replace("@aaa # v4", "@bbb # v7")
    assert differs_only_in_action_pins(bumped, base)
    # An identical file is not drift.
    assert not differs_only_in_action_pins(base, base)
    # A real content change is not a pin bump, even alongside one.
    assert not differs_only_in_action_pins(bumped.replace("name: CI", "name: Build"), base)
    # Different line counts cannot be a pin bump.
    assert not differs_only_in_action_pins(base + "      - run: echo\n", base)


def test_install_writes_the_config_when_absent_and_never_touches_an_existing_one(
    tmp_path: Path,
):
    """It is written only when absent. Rewriting an adopter's configuration with string
    surgery, from a package that carries no YAML parser, risks turning a lint into an
    outage — so the present-but-unprotected case is reported by `installed()` instead."""
    cfg = GhConfig(root=tmp_path)
    install.install(cfg, hooks_path=False)
    written = (tmp_path / DEPENDABOT_PATH).read_text(encoding="utf-8")
    assert "dependency-name: actions/checkout" in written

    mine = "version: 2\n# hand written, do not clobber\n"
    (tmp_path / DEPENDABOT_PATH).write_text(mine, encoding="utf-8")
    actions = install.install(cfg, hooks_path=False)
    assert (tmp_path / DEPENDABOT_PATH).read_text(encoding="utf-8") == mine
    assert any(a.hook == DEPENDABOT_PATH and a.outcome == "unchanged" for a in actions)


def test_a_repository_that_took_no_workflows_gets_no_dependabot_opinion(tmp_path: Path):
    cfg = GhConfig(root=tmp_path, managed_workflows=())
    actions = install.install(cfg, hooks_path=False)
    assert not (tmp_path / DEPENDABOT_PATH).exists()
    assert not any(a.hook == DEPENDABOT_PATH for a in actions)


def test_check_names_the_bot_as_the_likely_cause_of_pin_only_drift(tmp_path: Path):
    """ "Out of date" alone sent one diagnosis through three wrong hypotheses before a
    dependabot merge timestamp gave it away. The message now carries the cause."""
    cfg = GhConfig(root=tmp_path)
    install.install(cfg, hooks_path=False)
    target = tmp_path / install.WORKFLOWS_DIR / "provenance.yml"
    text = target.read_text(encoding="utf-8")
    bumped, count = __import__("re").subn(
        r"(uses: actions/checkout@)\w+", r"\g<1>deadbeef", text, count=1
    )
    assert count == 1, "expected a pinned checkout to bump"
    target.write_text(bumped, encoding="utf-8")

    _, problems = install.installed(cfg, local=False)
    drift = [p for p in problems if "provenance.yml" in p]
    assert drift and "differs ONLY in action pins" in drift[0]
    assert "signature of a bot edit" in drift[0] and "vibey-gh install" in drift[0]


def test_check_reports_a_scanning_config_that_leaves_the_managed_pins_open(tmp_path: Path):
    cfg = GhConfig(root=tmp_path)
    install.install(cfg, hooks_path=False)
    (tmp_path / DEPENDABOT_PATH).write_text(
        "version: 2\nupdates:\n  - package-ecosystem: github-actions\n    directory: /\n",
        encoding="utf-8",
    )
    ok, problems = install.installed(cfg, local=False)
    exposed = [p for p in problems if DEPENDABOT_PATH in p]
    assert not ok and exposed
    assert "refuses every push" in exposed[0]
    assert "`dependency-name: actions/checkout`" in exposed[0]
