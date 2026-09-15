# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for the vibey-gh automation.

The readiness gate and the version decision are the parts most worth testing: both were
originally shell, where every case had to be exercised by hand and one of them was wrong
for a week. Here they are ordinary functions with an ordinary table of cases.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from vibey_gh import fingerprints, install, merge_train, realign, versioning
from vibey_gh.cli import main as cli_main
from vibey_gh.config import GhConfig, PrAutomationConfig, load_config, normalise_actor

# --------------------------------------------------------------------------- helpers


def git(cwd: Path, *args: str) -> str:
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)
    assert r.returncode == 0, r.stderr
    return r.stdout


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q", ".")
    git(tmp_path, "config", "user.email", "t@example.com")
    git(tmp_path, "config", "user.name", "t")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "__init__.py").write_text('__version__ = "1.2.3"\n')
    (tmp_path / "manifest.json").write_text(json.dumps({"metadata": {"version": "1.2.3"}}) + "\n")
    (tmp_path / "content").mkdir()
    (tmp_path / "content" / "thing.md").write_text("hello\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-qm", "base")
    return tmp_path


def cfg_for(root: Path, **kw) -> GhConfig:
    base = dict(
        root=root,
        sources=("src/*.py",),
        version_files=("src/__init__.py", "manifest.json"),
        content_paths=("content/",),
        code_paths=("src/",),
    )
    base.update(kw)
    return GhConfig(**base)


def test_sources_deduplicate_overlapping_patterns(tmp_path):
    source = tmp_path / "module.py"
    source.write_text("pass\n")
    cfg = cfg_for(tmp_path, sources=("*.py", "module.py"))
    assert fingerprints.sources(cfg) == [source]


# --------------------------------------------------------------------------- config


def test_defaults_apply_without_a_config_file(tmp_path):
    cfg = load_config(tmp_path)
    assert cfg.header.startswith("# Made with ❤️ by [Vibey]")
    assert cfg.trailer_key == "Made-With"


def test_config_file_overrides_defaults(tmp_path):
    (tmp_path / ".vibey-gh.toml").write_text(
        '[fingerprint]\ntext = "X"\ntrailer = "By: X"\nsources = ["a/*.py"]\n'
        '[branches]\nintegration = "trunk"\n'
    )
    cfg = load_config(tmp_path)
    assert cfg.header == "# X"
    assert cfg.trailer_key == "By"
    assert cfg.sources == ("a/*.py",)
    assert cfg.integration_branch == "trunk"


@pytest.mark.parametrize(
    "given,expected",
    [
        ("app/claude", "claude"),
        ("claude[bot]", "claude"),
        ("app/github-actions", "github-actions"),
        ("adammatthewsteinberger", "adammatthewsteinberger"),
    ],
)
def test_bot_logins_normalise_to_one_spelling(given, expected):
    """gh writes `app/claude`; the rest of GitHub writes `claude[bot]`."""
    assert normalise_actor(given) == expected


# ---------------------------------------------------------------------- fingerprints


def test_header_is_detected_and_inserted(repo):
    cfg = cfg_for(repo)
    report = fingerprints.check(cfg)
    assert [p.name for p in report.missing_header] == ["__init__.py"]

    fingerprints.check(cfg, apply=True)
    assert fingerprints.check(cfg).ok


def test_duplicate_header_is_detected_and_deduped(repo):
    cfg = cfg_for(repo)
    target = repo / "src" / "__init__.py"
    target.write_text(f"{cfg.header}\n{cfg.header}\n" + target.read_text())

    report = fingerprints.check(cfg)
    assert [p.name for p in report.duplicate_header] == ["__init__.py"]
    assert not report.ok

    fingerprints.check(cfg, apply=True)
    lines = target.read_text().splitlines()
    assert lines.count(cfg.header) == 1
    assert fingerprints.check(cfg).ok


def test_has_header_reports_presence(repo):
    cfg = cfg_for(repo)
    target = repo / "src" / "__init__.py"
    assert not fingerprints.has_header(target.read_text(), cfg)

    fingerprints.check(cfg, apply=True)
    assert fingerprints.has_header(target.read_text(), cfg)


def test_header_goes_after_a_shebang(repo):
    cfg = cfg_for(repo)
    target = repo / "src" / "__init__.py"
    target.write_text('#!/usr/bin/env python3\n__version__ = "1.2.3"\n')
    fingerprints.check(cfg, apply=True)
    lines = target.read_text().splitlines()
    assert lines[0].startswith("#!")
    assert lines[1] == cfg.header


def test_missing_commit_trailer_is_reported(repo):
    cfg = cfg_for(repo)
    git(repo, "commit", "-q", "--allow-empty", "-m", "no trailer here")
    missing = fingerprints.commits_missing_trailer("HEAD~1..HEAD", cfg)
    assert len(missing) == 1 and "no trailer here" in missing[0]

    git(repo, "commit", "-q", "--allow-empty", "-m", f"has one\n\n{cfg.trailer}")
    assert fingerprints.commits_missing_trailer("HEAD~1..HEAD", cfg) == []


def test_conventional_commit_subject_validation_and_normalization():
    assert fingerprints.conventional_subject("feat(cli): add repair command")
    assert fingerprints.conventional_subject("fix!: reject unsafe branch deletion")
    assert not fingerprints.conventional_subject("Add repair command")
    message = "Add repair command\n\nDetails\n\nMade-With: Vibey\n"
    assert fingerprints.normalize_commit_message(message) == (
        "chore: Add repair command\n\nDetails\n\nMade-With: Vibey\n"
    )
    assert fingerprints.normalize_commit_message("") == ""
    crlf = "Bad subject\r\nBody\r\nMade-With: Vibey\r\n"
    assert fingerprints.normalize_commit_message(crlf) == (
        "chore: Bad subject\r\nBody\r\nMade-With: Vibey\r\n"
    )
    unicode_body = "Bad subject\nBody\u2028still body\n"
    assert fingerprints.normalize_commit_message(unicode_body) == (
        "chore: Bad subject\nBody\u2028still body\n"
    )


def test_nonconventional_commit_is_reported(repo):
    cfg = cfg_for(repo)
    git(repo, "commit", "-q", "--allow-empty", "-m", f"Not conventional\n\n{cfg.trailer}")
    invalid = fingerprints.commits_with_invalid_subject("HEAD~1..HEAD", cfg)
    assert len(invalid) == 1 and "Not conventional" in invalid[0]
    with pytest.raises(RuntimeError, match="cannot read"):
        fingerprints.commits_with_invalid_subject("missing-ref..HEAD", cfg)


def test_an_imported_history_is_not_this_branch_s_to_answer_for(repo):
    """Both commit gates walk the first-parent line only.

    A `git subtree add` without `--squash` attaches another repository's whole history as
    the merge's second parent. Those commits are admitted history, not authored work, and
    the only way to make them satisfy this repository's rules is to rewrite them — which
    changes the SHA the merge's `git-subtree-split` trailer records.
    """
    base = git(repo, "rev-parse", "HEAD").strip()

    # An unrelated history, exactly as an upstream repository would arrive: no trailer,
    # no Conventional Commits.
    git(repo, "checkout", "-q", "--orphan", "upstream")
    git(repo, "rm", "-rq", "--cached", ".")
    (repo / "vendored.txt").write_text("from somewhere else\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "Initial import of somebody else's code")
    upstream = git(repo, "rev-parse", "HEAD").strip()

    git(repo, "checkout", "-q", base)
    git(repo, "checkout", "-qb", "trunk")
    git(repo, "merge", "-q", "--no-ff", "--allow-unrelated-histories", upstream, "-m", "merged")
    git(repo, "commit", "-q", "--allow-empty", "-m", f"feat: ours\n\n{cfg_for(repo).trailer}")

    cfg = cfg_for(repo)
    rev_range = f"{base}..HEAD"
    assert fingerprints.commits_missing_trailer(rev_range, cfg) == []
    assert fingerprints.commits_with_invalid_subject(rev_range, cfg) == []

    # And the gate still sees what this branch actually authored.
    git(repo, "commit", "-q", "--allow-empty", "-m", "Ours, and wrong")
    assert len(fingerprints.commits_missing_trailer(rev_range, cfg)) == 1
    assert len(fingerprints.commits_with_invalid_subject(rev_range, cfg)) == 1


# ------------------------------------------------------------------------ versioning


@pytest.mark.parametrize(
    "version,level,expected",
    [
        ("1.2.3", "minor", "1.3.0"),
        ("1.2.3", "patch", "1.2.4"),
        ("2.17.0", "minor", "2.18.0"),
    ],
)
def test_bump(version, level, expected):
    assert versioning.bump(version, level) == expected


def test_read_version_from_python_and_json(repo):
    cfg = cfg_for(repo)
    assert versioning.read_version(cfg) == "1.2.3"
    cfg_json = cfg_for(repo, version_files=("manifest.json",))
    assert versioning.read_version(cfg_json) == "1.2.3"


def test_apply_version_writes_every_configured_file(repo):
    cfg = cfg_for(repo)
    versioning.apply_version(cfg, "9.9.9")
    assert '__version__ = "9.9.9"' in (repo / "src" / "__init__.py").read_text()
    assert json.loads((repo / "manifest.json").read_text())["metadata"]["version"] == "9.9.9"


@pytest.mark.parametrize(
    "change,expected,note",
    [
        ("content", "1.3.0", "packaged content changed -> minor"),
        ("code", "1.2.4", "only internal code -> patch"),
        ("docs", None, "nothing an installed user receives -> none"),
        (None, None, "no changes at all -> none"),
    ],
)
def test_version_decision_table(repo, change, expected, note):
    cfg = cfg_for(repo)
    git(repo, "branch", "-q", "base")
    if change == "content":
        (repo / "content" / "thing.md").write_text("changed\n")
    elif change == "code":
        (repo / "src" / "other.py").write_text("x = 1\n")
    elif change == "docs":
        (repo / "README.md").write_text("docs\n")
    if change:
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", change)

    new, why = versioning.decide(cfg, "base")
    assert new == expected, f"{note}: got {new} ({why})"


def test_stamping_the_fingerprint_is_not_a_release(repo):
    """Observed on a live adoption: 181 files gained the header and nothing else, and the
    repository was bumped 0.4.1 -> 0.5.0 for a diff made entirely of comments. The header
    is the one change this tool can prove is inert -- it writes it, knows its exact text,
    and enforces it byte-for-byte -- so it must never manufacture a release by itself."""
    from vibey_gh.config import DEFAULT_TEXT

    cfg = cfg_for(repo)
    git(repo, "branch", "-q", "base")
    for path in (repo / "content" / "thing.md", repo / "src" / "__init__.py"):
        path.write_text(f"# {DEFAULT_TEXT}\n" + path.read_text())
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "stamp")
    new, why = versioning.decide(cfg, "base")
    assert new is None
    assert "provenance" in why and "2 file(s)" in why


def test_a_real_change_beside_the_header_still_counts(repo):
    """The discount is per file and only for files whose ENTIRE diff is the header. A file
    that gained the header and a real line contains a real change; and a header-only file
    must not shield a genuine change elsewhere from classification."""
    from vibey_gh.config import DEFAULT_TEXT

    cfg = cfg_for(repo)
    git(repo, "branch", "-q", "base")
    stamped = repo / "content" / "thing.md"
    stamped.write_text(f"# {DEFAULT_TEXT}\n" + stamped.read_text())
    (repo / "src" / "other.py").write_text("x = 1\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "stamp plus code")
    new, why = versioning.decide(cfg, "base")
    # The content file is discounted (header only); the code file is real -> patch, not
    # the minor that counting the stamped content file would have produced.
    assert new == "1.2.4", why


def test_header_plus_content_in_one_file_is_still_content(repo):
    from vibey_gh.config import DEFAULT_TEXT

    cfg = cfg_for(repo)
    git(repo, "branch", "-q", "base")
    f = repo / "content" / "thing.md"
    f.write_text(f"# {DEFAULT_TEXT}\nreal new words\n" + f.read_text())
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "stamp and change")
    new, why = versioning.decide(cfg, "base")
    assert new == "1.3.0", why


def test_a_deliberate_bump_is_never_doubled(repo):
    """Someone bumped by hand in a pull request; the automation must leave it alone."""
    cfg = cfg_for(repo)
    git(repo, "branch", "-q", "base")
    (repo / "content" / "thing.md").write_text("changed\n")
    versioning.apply_version(cfg, "5.0.0")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "manual bump")
    new, why = versioning.decide(cfg, "base")
    assert new is None and "deliberate bump" in why


def test_dev_version_is_pep440_and_ordered(repo):
    cfg = cfg_for(repo)
    assert versioning.dev_version(cfg, "42") == "1.2.3.dev42"
    assert versioning.dev_version(cfg, "build-7") == "1.2.3.dev7"


# ----------------------------------------------------------------------- merge train


def _pr(**kw):
    pr = dict(
        number=1,
        title="t",
        isDraft=False,
        mergeable="MERGEABLE",
        reviewDecision=None,
        statusCheckRollup=[{"status": "COMPLETED", "conclusion": "SUCCESS"}],
        author={"login": "owner"},
    )
    pr.update(kw)
    return pr


@pytest.mark.parametrize(
    "pr,ready,fragment",
    [
        (_pr(), True, None),
        (_pr(author={"login": "app/claude"}), True, None),
        (_pr(author={"login": "claude[bot]"}), True, None),
        (_pr(isDraft=True), False, "draft"),
        (_pr(mergeable="CONFLICTING"), False, "conflicts"),
        (_pr(reviewDecision="CHANGES_REQUESTED"), False, "changes requested"),
        (
            _pr(statusCheckRollup=[{"status": "IN_PROGRESS", "conclusion": None}]),
            False,
            "still running",
        ),
        (
            _pr(statusCheckRollup=[{"status": "COMPLETED", "conclusion": "FAILURE"}]),
            False,
            "failing",
        ),
        (_pr(statusCheckRollup=[]), True, None),
        (_pr(author={"login": "outsider"}), False, "not approved"),
        (_pr(author={"login": "outsider"}, reviewDecision="APPROVED"), True, None),
    ],
)
def test_readiness_gate(tmp_path, pr, ready, fragment):
    cfg = cfg_for(
        tmp_path,
        owner="owner",
        trusted_authors=("owner", "claude[bot]", "github-actions[bot]"),
        pr_automation=PrAutomationConfig(enabled=False),
    )
    verdict = merge_train.judge(pr, cfg)
    assert verdict.ready is ready
    if fragment:
        assert fragment in verdict.reason


def test_merge_train_ignores_internal_draft_gate_after_public_gate_passes(tmp_path):
    cfg = cfg_for(
        tmp_path,
        owner="owner",
        trusted_authors=("owner",),
        pr_automation=PrAutomationConfig(enabled=True),
    )
    pr = _pr(
        statusCheckRollup=[
            {"name": "gate", "status": "COMPLETED", "conclusion": "FAILURE"},
            {
                "name": "PR automation / gate",
                "status": "COMPLETED",
                "conclusion": "FAILURE",
            },
            {
                "name": "PR automation / gate",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
            },
            {"name": "CI", "status": "COMPLETED", "conclusion": "SUCCESS"},
        ]
    )
    assert merge_train.judge(pr, cfg).ready


def test_pull_request_recovers_fresh_exact_head_gate(monkeypatch):
    calls = []

    def fake(*args):
        calls.append(args)
        if args[:2] == ("pr", "view"):
            return _pr(headRefOid="abc", statusCheckRollup=[])
        if args[:2] == ("repo", "view"):
            return {"nameWithOwner": "owner/repo"}
        return {
            "check_runs": [
                {"name": "PR automation / gate", "status": "completed", "conclusion": "success"}
            ]
        }

    monkeypatch.setattr(merge_train, "_gh_json", fake)
    pr = merge_train.pull_request(1)
    assert pr["statusCheckRollup"][-1]["conclusion"] == "SUCCESS"
    assert any(args[0] == "api" for args in calls)


def test_exact_head_gate_lookup_skips_existing_missing_sha_and_nonpassing(monkeypatch):
    called = []
    monkeypatch.setattr(
        merge_train,
        "_gh_json",
        lambda *args: (
            called.append(args) or {"nameWithOwner": "owner/repo"}
            if args[0] == "repo"
            else {
                "check_runs": [
                    {"name": "PR automation / gate", "status": "completed", "conclusion": "failure"}
                ]
            }
        ),
    )
    existing = {"statusCheckRollup": [{"name": "PR automation / gate"}], "headRefOid": "x"}
    merge_train._include_exact_head_gate(existing)
    merge_train._include_exact_head_gate({"statusCheckRollup": []})
    failing = {"statusCheckRollup": [], "headRefOid": "x"}
    merge_train._include_exact_head_gate(failing)
    assert failing["statusCheckRollup"] == []


def test_open_pull_requests_reuses_exact_head_lookup(monkeypatch, tmp_path):
    monkeypatch.setattr(merge_train, "_gh_json", lambda *args: [{"number": 2}])
    monkeypatch.setattr(merge_train, "pull_request", lambda number: {"number": number})
    assert merge_train.open_pull_requests(cfg_for(tmp_path)) == [{"number": 2}]


# -------------------------------------------------------------------------- install


def test_install_places_hooks_and_reports_missing(repo):
    cfg = cfg_for(repo)
    ok, problems = install.installed(cfg, local=False)
    assert not ok and any("commit-msg" in p for p in problems)

    install.install(cfg, hooks_path=False)
    ok, problems = install.installed(cfg, local=False)
    assert ok, problems
    assert (repo / ".githooks" / "pre-push").exists()


def test_install_chains_an_existing_hook_instead_of_discarding_it(repo):
    cfg = cfg_for(repo)
    hooks = repo / ".githooks"
    hooks.mkdir()
    (hooks / "pre-push").write_text("#!/bin/sh\necho someone elses check\n")

    actions = install.install(cfg, hooks_path=False)
    assert any(a.hook == "pre-push" and a.outcome == "chained" for a in actions)
    assert "someone elses check" in (hooks / "pre-push.local").read_text()
    assert "vibey-gh" in (hooks / "pre-push").read_text()


def test_ci_mode_ignores_local_hooks_path(repo):
    """core.hooksPath is per-clone config no runner can satisfy; the FILES still count."""
    cfg = cfg_for(repo)
    install.install(cfg, hooks_path=False)
    assert install.installed(cfg, local=False)[0] is True
    assert install.installed(cfg, local=True)[0] is False


# --------------------------------------------------------------------------- realign


def test_realign_refuses_when_the_branches_differ(repo, monkeypatch):
    cfg = cfg_for(repo, integration_branch="develop", release_branch="main")
    monkeypatch.setattr(
        realign,
        "_git",
        lambda c, *a: subprocess.CompletedProcess(a, 1 if a[0] == "diff" else 0, "", ""),
    )
    changed, message = realign.realign(cfg)
    assert changed is False and "left untouched" in message


# ------------------------------------------------------------------------------ cli


def test_cli_check_reports_failure_then_success(repo, monkeypatch, capsys):
    (repo / ".vibey-gh.toml").write_text(
        '[fingerprint]\nsources = ["src/*.py"]\n[documentation]\nenabled=false\n'
    )
    monkeypatch.chdir(repo)
    assert cli_main(["check", "--ci"]) == 1
    install.install(load_config(repo), hooks_path=False)
    assert cli_main(["check", "--ci", "--apply"]) == 0


def test_one_repository_can_derive_a_second_distributions_version(repo, monkeypatch, capsys):
    """A monorepo publishes several distributions; one .vibey-gh.toml holds one version
    line. `--config` supplies a second, without moving the root.

    The paths stay repository-root-relative on purpose: the deriver asks git for them with
    `git show <rev>:<path>`, which resolves only from the top of the tree. A config whose
    paths were relative to the subtree would silently read the wrong pyproject.
    """
    (repo / ".vibey-gh.toml").write_text(
        '[version]\nfiles = ["src/__init__.py"]\ncontent_paths = ["content/"]\n'
    )
    (repo / "tool").mkdir()
    (repo / "tool" / "__init__.py").write_text('__version__ = "9.9.9"\n')
    (repo / ".vibey-gh.d").mkdir()
    (repo / ".vibey-gh.d" / "tool.toml").write_text(
        '[version]\nfiles = ["tool/__init__.py"]\ncontent_paths = ["tool/"]\n'
    )
    monkeypatch.chdir(repo)

    primary = load_config()
    alternate = load_config(config=Path(".vibey-gh.d/tool.toml"))
    assert primary.version_files == ("src/__init__.py",)
    assert alternate.version_files == ("tool/__init__.py",)
    # The root did NOT move. That is the whole distinction.
    assert alternate.root == primary.root == repo

    assert cli_main(["version", "--config", ".vibey-gh.d/tool.toml", "--since", "HEAD"]) == 0

    with pytest.raises(FileNotFoundError, match="no such configuration"):
        load_config(config=Path(".vibey-gh.d/absent.toml"))


def test_cli_prints_the_trailer(repo, monkeypatch, capsys):
    monkeypatch.chdir(repo)
    cli_main(["trailer-key"])
    assert capsys.readouterr().out.strip() == "Made-With"


def test_the_train_ignores_pr_automations_own_superseded_jobs():
    """A superseded PR-automation run leaves CANCELLED check runs for every job it did not
    finish. Those are this automation's own bookkeeping, not evidence about the change, and
    the gate already excludes them — the train excluding only `gate` meant it counted them
    as failures and skipped a pull request the gate had certified green.
    """
    from vibey_gh import merge_train
    from vibey_gh.config import GhConfig

    cfg = GhConfig(root=Path("."), owner="owner", trusted_authors=("owner",))
    leftovers = [
        {"name": name, "status": "COMPLETED", "conclusion": "CANCELLED"}
        for name in (
            "Resolve merge conflicts",
            "Mirror fork for safe repair",
            "Repair failed scans or review findings",
            "Escalate exhausted repair lineage",
            "Local review fallback",
            "Exact-head code and documentation review",
            "Evaluate current head",
        )
    ]
    gate = {
        "name": "PR automation / gate",
        "status": "COMPLETED",
        "conclusion": "SUCCESS",
    }
    real = {"name": "CI", "status": "COMPLETED", "conclusion": "SUCCESS"}

    verdict = merge_train.judge(_pr(statusCheckRollup=[*leftovers, gate, real]), cfg)
    assert verdict.ready, verdict.reason


def test_the_train_still_requires_the_gate_it_excludes_from_the_policy_set():
    """Excluding `PR automation / gate` from the failure count must not stop it being
    REQUIRED: the readiness check reads the unfiltered rollup for exactly that reason. A
    change that loses this distinction would merge pull requests the gate never certified.
    """
    from vibey_gh import merge_train
    from vibey_gh.config import GhConfig

    cfg = GhConfig(root=Path("."), owner="owner", trusted_authors=("owner",))
    real = {"name": "CI", "status": "COMPLETED", "conclusion": "SUCCESS"}

    verdict = merge_train.judge(_pr(statusCheckRollup=[real]), cfg)
    assert not verdict.ready
    assert "gate has not passed" in (verdict.reason or "")


def test_a_superseded_header_is_replaced_not_stacked(repo):
    """The 770-file incident, encoded. `--apply` used to only insert the current header,
    so a fingerprint-text change left the old line behind underneath the new one and
    `check` reported ok. Now the old line is recognised and REPLACED in place."""
    from vibey_gh import fingerprints
    from vibey_gh.config import DEFAULT_SUPERSEDED_TEXTS

    cfg = cfg_for(repo)
    src = repo / "src" / "stamped.py"
    src.write_text(f"# {DEFAULT_SUPERSEDED_TEXTS[0]}\nx = 1\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "old stamp")

    report = fingerprints.check(cfg)
    assert src in report.superseded_header and not report.ok

    fingerprints.check(cfg, apply=True)
    text = src.read_text()
    assert text.startswith(cfg.header + "\n")
    assert DEFAULT_SUPERSEDED_TEXTS[0] not in text
    assert text.count("Made with") == 1
    assert fingerprints.check(cfg).ok


def test_an_already_stacked_pair_collapses_to_one(repo):
    """A file that already suffered the stacking bug — current header above a superseded
    one — comes out of `--apply` with exactly the current header."""
    from vibey_gh import fingerprints
    from vibey_gh.config import DEFAULT_SUPERSEDED_TEXTS

    cfg = cfg_for(repo)
    src = repo / "src" / "stacked.py"
    src.write_text(f"{cfg.header}\n# {DEFAULT_SUPERSEDED_TEXTS[1]}\nx = 1\n")
    fingerprints.check(cfg, apply=True)
    text = src.read_text()
    assert text == f"{cfg.header}\nx = 1\n"


def test_a_text_migration_is_not_a_release(repo):
    """Replacing the old header with the new one — the whole-family migration — must be
    discounted exactly like a fresh stamp: minus-old plus-new, both provenance lines."""
    from vibey_gh.config import DEFAULT_SUPERSEDED_TEXTS, DEFAULT_TEXT

    cfg = cfg_for(repo)
    f = repo / "content" / "thing.md"
    f.write_text(f"# {DEFAULT_SUPERSEDED_TEXTS[0]}\nhello\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "old stamp")
    git(repo, "branch", "-q", "base")
    f.write_text(f"# {DEFAULT_TEXT}\nhello\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "migrate stamp")
    new, why = versioning.decide(cfg, "base")
    assert new is None
    assert "provenance" in why


def test_seo_configuration_survives_the_loader(tmp_path):
    """The dataclass gaining fields is not the same as the loader reading them — this
    exact gap shipped a green render with every SEO value silently defaulted."""
    from vibey_gh.config import load_config

    (tmp_path / ".vibey-gh.toml").write_text(
        '[documentation]\nfavicon = "🔧"\nauthor = "A"\nkeywords = ["k1", "k2"]\n'
        'og_image = "https://x/i.png"\ntwitter_site = "@t"\ntwitter_creator = "@c"\n'
        'theme_color = "#fff"\nlocale = "fr_FR"\n'
    )
    d = load_config(tmp_path).documentation
    assert (d.favicon, d.author, d.keywords) == ("🔧", "A", ("k1", "k2"))
    assert (d.og_image, d.twitter_site, d.twitter_creator) == ("https://x/i.png", "@t", "@c")
    assert (d.theme_color, d.locale) == ("#fff", "fr_FR")
