# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The paths the happy-path tests do not reach: refusals, re-runs, and drift.

Where the module shells out, these tests give it a real thing to shell out to — a fake
`gh` on PATH, a real bare repository over file:// — rather than a mocked `subprocess.run`.
A mock cannot tell you that the argument order is wrong.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path

import pytest

import vibey_gh.pr_automation as pa
from vibey_gh import fingerprints, install, merge_train, realign, versioning
from vibey_gh.config import GhConfig, PrAutomationConfig


def git(cwd: Path, *a: str) -> str:
    r = subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True, check=True)
    return r.stdout


def init(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-q", "-b", "main", ".")
    git(path, "config", "user.email", "t@example.com")
    git(path, "config", "user.name", "t")


# ---------------------------------------------------------------- install


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    init(tmp_path)
    return tmp_path


def outcomes(actions) -> dict[str, str]:
    return {a.hook: a.outcome for a in actions}


def test_installing_twice_reports_everything_unchanged(repo):
    cfg = GhConfig(root=repo)
    install.install(cfg)
    second = outcomes(install.install(cfg))
    assert set(second.values()) == {"unchanged"}
    assert install.installed(cfg) == (True, [])


def test_an_outdated_vibey_hook_is_replaced_not_chained(repo):
    cfg = GhConfig(root=repo)
    install.install(cfg)
    hook = repo / install.HOOKS_DIR / "pre-push"
    hook.write_text(hook.read_text() + "\n# stale vibey-gh copy\n")
    (repo / install.WORKFLOWS_DIR / "provenance.yml").write_text("stale\n")
    release_asset = repo / install.RELEASE_ASSETS_DIR / "vibey.css"
    release_asset.write_text("stale\n")

    ok, problems = install.installed(cfg)
    assert not ok
    assert any("pre-push is out of date" in p for p in problems)
    assert any("provenance.yml is out of date" in p for p in problems)
    assert any("vibey.css is out of date" in p for p in problems)

    assert outcomes(install.install(cfg))["pre-push"] == "updated"
    assert not (repo / install.HOOKS_DIR / "pre-push.local").exists()
    assert install.installed(cfg) == (True, [])


def test_a_foreign_hook_is_preserved_and_chained(repo):
    cfg = GhConfig(root=repo)
    hooks = repo / install.HOOKS_DIR
    hooks.mkdir()
    (hooks / "pre-push").write_text("#!/bin/sh\necho someone elses check\n")

    assert outcomes(install.install(cfg))["pre-push"] == "chained"
    local = hooks / "pre-push.local"
    assert "someone elses check" in local.read_text()
    assert local.stat().st_mode & stat.S_IXUSR


def test_a_foreign_hook_with_an_existing_local_chain_is_replaced(repo):
    hooks = repo / install.HOOKS_DIR
    hooks.mkdir()
    (hooks / "pre-push").write_text("#!/bin/sh\necho foreign\n")
    local = hooks / "pre-push.local"
    local.write_text("#!/bin/sh\necho preserved\n")

    install.install(GhConfig(root=repo))

    assert "vibey-gh" in (hooks / "pre-push").read_text()
    assert "preserved" in local.read_text()


def test_missing_hooks_and_workflows_are_both_reported(repo):
    ok, problems = install.installed(GhConfig(root=repo), local=True)
    assert not ok
    assert any("commit-msg is missing" in p for p in problems)
    assert any("provenance.yml is missing" in p for p in problems)
    assert any("core.hooksPath" in p for p in problems)


def test_install_can_leave_core_hookspath_alone(repo):
    install.install(GhConfig(root=repo), hooks_path=False)
    got = subprocess.run(
        ["git", "config", "--get", "core.hooksPath"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    assert got.stdout.strip() == ""


def test_release_assets_are_found_inside_an_installed_wheel(repo, tmp_path, monkeypatch):
    packaged = tmp_path / "installed-package" / "templates" / "release"
    packaged.mkdir(parents=True)
    (packaged / "vibey.css").write_text("theme")
    (packaged / "channel.js").write_text("provenance")
    monkeypatch.setattr(install, "PACKAGED_RELEASE_ASSETS", packaged)

    assert install._release_assets(GhConfig(root=repo)) == [
        (packaged / "vibey.css", "vibey.css"),
        (packaged / "channel.js", "channel.js"),
    ]


# ---------------------------------------------------------------- fingerprints


def test_an_unreadable_rev_range_is_an_error_not_a_silent_pass(repo):
    with pytest.raises(RuntimeError, match="cannot read no-such-ref"):
        fingerprints.commits_missing_trailer("no-such-ref..HEAD", GhConfig(root=repo))


# ---------------------------------------------------------------- versioning


def cfg_with_versions(root: Path, *files: str) -> GhConfig:
    return GhConfig(
        root=root, version_files=files, content_paths=("content/",), code_paths=("src/",)
    )


def test_read_version_skips_absent_files_and_reads_json_metadata(tmp_path):
    (tmp_path / "m.json").write_text(json.dumps({"metadata": {"version": "3.4.5"}}))
    cfg = cfg_with_versions(tmp_path, "gone.py", "m.json")
    assert versioning.read_version(cfg) == "3.4.5"


def test_read_version_accepts_a_flat_json_version(tmp_path):
    (tmp_path / "m.json").write_text(json.dumps({"version": "9.0.1"}))
    assert versioning.read_version(cfg_with_versions(tmp_path, "m.json")) == "9.0.1"


def test_json_without_version_falls_through_to_next_file(tmp_path):
    (tmp_path / "empty.json").write_text("{}")
    (tmp_path / "v.py").write_text('__version__ = "4.5.6"\n')
    assert versioning.read_version(cfg_with_versions(tmp_path, "empty.json", "v.py")) == "4.5.6"


def test_read_version_raises_when_no_file_carries_one(tmp_path):
    (tmp_path / "v.py").write_text("# nothing here\n")
    with pytest.raises(RuntimeError, match="no version found"):
        versioning.read_version(cfg_with_versions(tmp_path, "v.py", "absent.json"))


def test_git_failures_surface_as_runtime_errors(repo):
    with pytest.raises(RuntimeError, match="git diff"):
        versioning._git(GhConfig(root=repo), "diff", "--name-only", "nope", "HEAD")


def test_decide_refuses_to_guess_when_the_ref_has_no_version(repo):
    (repo / "v.py").write_text('__version__ = "1.0.0"\n')
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "no version file tracked yet")
    cfg = cfg_with_versions(repo, "absent.py")
    new, why = versioning.decide(cfg, "HEAD")
    assert new is None and "refusing to guess" in why


def test_read_version_at_walks_past_junk_to_the_file_that_has_one(repo):
    (repo / "broken.json").write_text("{not json")
    (repo / "empty.py").write_text("x = 1\n")
    (repo / "m.json").write_text(json.dumps({"metadata": {"version": "2.0.0"}}))
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "base")

    cfg = cfg_with_versions(repo, "absent.json", "broken.json", "empty.py", "m.json")
    assert versioning.read_version_at(cfg, "HEAD") == "2.0.0"
    assert versioning.read_version_at(cfg_with_versions(repo, "empty.py"), "HEAD") is None


def test_read_version_at_walks_past_json_without_version(repo):
    (repo / "empty.json").write_text("{}")
    (repo / "v.py").write_text('__version__ = "5.6.7"\n')
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "base")
    assert (
        versioning.read_version_at(cfg_with_versions(repo, "empty.json", "v.py"), "HEAD") == "5.6.7"
    )


def test_apply_version_skips_absent_files_and_rejects_a_file_without_a_version(tmp_path):
    (tmp_path / "m.json").write_text(json.dumps({"version": "1.0.0"}))
    assert versioning.apply_version(cfg_with_versions(tmp_path, "gone.py", "m.json"), "1.1.0") == [
        "m.json"
    ]
    assert json.loads((tmp_path / "m.json").read_text())["version"] == "1.1.0"

    (tmp_path / "v.py").write_text("# no version line\n")
    with pytest.raises(RuntimeError, match="expected one __version__ line"):
        versioning.apply_version(cfg_with_versions(tmp_path, "v.py"), "1.1.0")


def test_dev_version_strips_non_digits_and_survives_a_digitless_build(tmp_path):
    (tmp_path / "v.py").write_text('__version__ = "1.2.3"\n')
    cfg = cfg_with_versions(tmp_path, "v.py")
    assert versioning.dev_version(cfg, "run-42") == "1.2.3.dev42"
    assert versioning.dev_version(cfg, "none") == "1.2.3.dev0"


# ---------------------------------------------------------------- merge train


@pytest.fixture
def fake_gh(tmp_path: Path, monkeypatch) -> Path:
    """A `gh` on PATH that replays scripted answers and records what it was asked.

    Answers live in `answers.json`, keyed by the joined argv; `calls.txt` records every
    invocation, so a test can assert on the command line the module actually built.
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    gh = bin_dir / "gh"
    gh.write_text(f"""#!/usr/bin/env python3
import json, pathlib, sys
here = pathlib.Path({str(bin_dir)!r})
with (here / "calls.txt").open("a") as fh:
    fh.write(" ".join(sys.argv[1:]) + "\\n")
answers = json.loads((here / "answers.json").read_text())
entry = answers.get(" ".join(sys.argv[1:]))
if entry is None:
    sys.stderr.write("no scripted answer\\n")
    raise SystemExit(3)
sys.stdout.write(entry.get("out", ""))
sys.stderr.write(entry.get("err", ""))
raise SystemExit(entry.get("code", 0))
""")
    gh.chmod(0o755)
    (bin_dir / "answers.json").write_text("{}")
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    return bin_dir


def script(bin_dir: Path, answers: dict) -> None:
    (bin_dir / "answers.json").write_text(json.dumps(answers))


def calls(bin_dir: Path) -> list[str]:
    path = bin_dir / "calls.txt"
    return path.read_text().splitlines() if path.exists() else []


def test_open_pull_requests_lists_then_views_each_one(fake_gh):
    cfg = GhConfig(root=Path.cwd(), integration_branch="develop")
    listing = "pr list --base develop --state open --json number --jq sort_by(.number)"
    script(
        fake_gh,
        {
            listing: {"out": json.dumps([{"number": 4}, {"number": 7}])},
            f"pr view 4 --json {merge_train._PR_FIELDS}": {
                "out": json.dumps({"number": 4, "title": "four"})
            },
            f"pr view 7 --json {merge_train._PR_FIELDS}": {
                "out": json.dumps({"number": 7, "title": "seven"})
            },
        },
    )
    assert [pr["title"] for pr in merge_train.open_pull_requests(cfg)] == ["four", "seven"]


def test_an_empty_listing_yields_no_pull_requests(fake_gh):
    cfg = GhConfig(root=Path.cwd(), integration_branch="develop")
    script(
        fake_gh,
        {"pr list --base develop --state open --json number --jq sort_by(.number)": {"out": ""}},
    )
    assert merge_train.open_pull_requests(cfg) == []


def test_a_failing_gh_call_raises_with_its_stderr(fake_gh):
    cfg = GhConfig(root=Path.cwd(), integration_branch="develop")
    script(fake_gh, {})
    with pytest.raises(RuntimeError, match="no scripted answer"):
        merge_train.open_pull_requests(cfg)


def test_merge_prefers_a_plain_merge(fake_gh):
    script(fake_gh, {"pr merge 5 --squash": {"code": 0}})
    assert merge_train.merge(5) == (True, False, "")
    assert calls(fake_gh) == ["pr merge 5 --squash"]


def test_merge_injects_a_squash_body_when_given_one(fake_gh):
    """The trailer rides in the squash body. A bot's pull request body never carries it,
    and without this the train manufactures the exact trailer-less commit the provenance
    check exists to refuse — five of which once blocked a promotion outright."""
    script(fake_gh, {"pr merge 5 --squash --body deps\n\nMade-With: x": {"code": 0}})
    assert merge_train.merge(5, "squash", "deps\n\nMade-With: x") == (True, False, "")
    assert calls(fake_gh)[0].startswith("pr merge 5 --squash --body")


def test_merge_never_injects_a_body_into_a_rebase(fake_gh):
    """A rebase preserves the branch's own commits; --body would be rejected by gh."""
    script(fake_gh, {"pr merge 5 --rebase": {"code": 0}})
    assert merge_train.merge(5, "rebase", "ignored") == (True, False, "")
    assert calls(fake_gh) == ["pr merge 5 --rebase"]


def test_merge_falls_back_to_admin_and_reports_the_bypass(fake_gh):
    script(fake_gh, {"pr merge 5 --rebase --admin": {"code": 0}})
    assert merge_train.merge(5, "rebase") == (True, True, "")
    assert calls(fake_gh)[-1].endswith("--admin")


def test_merge_reports_failure_when_even_admin_is_refused(fake_gh):
    """The third element is the diagnosis. Discarding it once turned a token-scope
    problem into an hour of ruleset archaeology: every failure read "the ruleset
    refused it" while the API was naming the actual cause the whole time."""
    script(fake_gh, {})
    merged, bypassed, error = merge_train.merge(5)
    assert (merged, bypassed) == (False, True)
    assert error  # the scripted stub's own refusal text, but never empty


@pytest.mark.parametrize(
    "pr,expected",
    [
        ({"headRefName": "fix/thing"}, True),
        ({"headRefName": "feature/thing"}, True),
        ({"headRefName": "develop"}, False),
        ({"headRefName": "main"}, False),
        ({"headRefName": "trunk"}, False),
        ({"headRefName": "stable"}, False),
        ({"headRefName": "fix/fork", "isCrossRepository": True}, False),
        ({}, False),
    ],
)
def test_only_same_repo_topic_branches_are_cleanup_candidates(pr, expected):
    cfg = GhConfig(root=Path.cwd(), integration_branch="trunk", release_branch="stable")
    assert merge_train.should_delete_head(pr, cfg) is expected


def test_topic_branch_cleanup_uses_the_exact_ref(fake_gh):
    script(
        fake_gh,
        {
            "repo view --json nameWithOwner": {"out": '{"nameWithOwner":"o/r"}'},
            "api repos/o/r/git/refs/heads/fix/thing --method DELETE": {},
        },
    )
    assert merge_train.delete_head_branch({"headRefName": "fix/thing"}) is True


def test_topic_branch_cleanup_reports_api_refusal(fake_gh):
    script(
        fake_gh,
        {"repo view --json nameWithOwner": {"out": '{"nameWithOwner":"o/r"}'}},
    )
    assert merge_train.delete_head_branch({"headRefName": "fix/thing"}) is False


# ---------------------------------------------------------------- realign


@pytest.fixture
def pair(tmp_path: Path) -> tuple[Path, Path]:
    """A bare origin plus a clone with `main` and `develop`, both at the same commit."""
    origin = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True)

    work = tmp_path / "work"
    init(work)
    (work / "a.txt").write_text("one\n")
    git(work, "add", "-A")
    git(work, "commit", "-qm", "one")
    git(work, "remote", "add", "origin", str(origin))
    git(work, "push", "-q", "origin", "main")
    git(work, "push", "-q", "origin", "main:develop")
    git(work, "fetch", "-q", "origin")
    return origin, work


def gh_cfg(root: Path) -> GhConfig:
    return GhConfig(root=root, integration_branch="develop", release_branch="main")


def test_realign_is_a_no_op_when_the_branches_are_the_same_commit(pair):
    _, work = pair
    changed, message = realign.realign(gh_cfg(work))
    assert changed is False
    assert "already matches" in message


def test_realign_refuses_when_develop_has_content_main_does_not(pair):
    _origin, work = pair
    git(work, "checkout", "-qB", "develop", "origin/develop")
    (work / "b.txt").write_text("extra\n")
    git(work, "add", "-A")
    git(work, "commit", "-qm", "extra")
    git(work, "push", "-q", "origin", "develop")

    changed, message = realign.realign(gh_cfg(work))
    assert changed is False
    assert "left untouched" in message
    assert git(work, "rev-parse", "origin/develop") != git(work, "rev-parse", "origin/main")


def test_realign_converges_identical_trees_onto_one_history(pair):
    _origin, work = pair
    # Rewrite develop as a different commit with the SAME tree — what a rebase-merge
    # leaves behind, and the only case realign exists to fix.
    git(work, "checkout", "-qB", "develop", "origin/develop")
    git(work, "commit", "-q", "--allow-empty", "-m", "rewritten copy")
    git(work, "push", "-q", "origin", "develop")
    git(work, "fetch", "-q", "origin")
    assert git(work, "rev-parse", "origin/develop") != git(work, "rev-parse", "origin/main")

    changed, message = realign.realign(gh_cfg(work))
    assert changed is True
    assert "histories converged" in message
    git(work, "fetch", "-q", "origin")
    assert git(work, "rev-parse", "origin/develop") == git(work, "rev-parse", "origin/main")


def test_a_refused_push_is_raised_with_the_manual_command(pair):
    origin, work = pair
    git(work, "checkout", "-qB", "develop", "origin/develop")
    git(work, "commit", "-q", "--allow-empty", "-m", "rewritten copy")
    git(work, "push", "-q", "origin", "develop")
    git(work, "fetch", "-q", "origin")

    # Only now: realign must get past the tree check and be refused at the push, which is
    # exactly how a branch ruleset refuses a token without the admin role.
    hooks = origin / "hooks"
    hooks.mkdir(exist_ok=True)
    (hooks / "pre-receive").write_text("#!/bin/sh\necho 'blocked by the ruleset' >&2\nexit 1\n")
    (hooks / "pre-receive").chmod(0o755)

    with pytest.raises(RuntimeError, match="could not realign develop") as raised:
        realign.realign(gh_cfg(work))
    assert "blocked by the ruleset" in str(raised.value)
    assert "git push --force-with-lease origin main:develop" in str(raised.value)


# ---------------------------------------------------------------- TOML versions


PYPROJECT = """[build-system]
requires = ["hatchling"]

[project]
name = "demo"
version = "1.2.3"
description = "x"

[tool.poetry]
version = "9.9.9"
"""


def test_a_toml_version_is_read_from_the_project_table(tmp_path):
    (tmp_path / "pyproject.toml").write_text(PYPROJECT)
    cfg = cfg_with_versions(tmp_path, "pyproject.toml")
    assert versioning.read_version(cfg) == "1.2.3"


def test_a_toml_without_a_project_version_is_skipped(tmp_path):
    (tmp_path / "a.toml").write_text('[tool.other]\nversion = "9.9.9"\n')
    (tmp_path / "v.py").write_text('__version__ = "2.0.0"\n')
    cfg = cfg_with_versions(tmp_path, "a.toml", "v.py")
    assert versioning.read_version(cfg) == "2.0.0"


def test_a_toml_that_does_not_parse_is_skipped(tmp_path):
    (tmp_path / "broken.toml").write_text("[project\nname = ")
    (tmp_path / "v.py").write_text('__version__ = "2.0.0"\n')
    cfg = cfg_with_versions(tmp_path, "broken.toml", "v.py")
    assert versioning.read_version(cfg) == "2.0.0"


def test_a_toml_version_is_read_at_a_git_ref(repo):
    (repo / "pyproject.toml").write_text(PYPROJECT)
    (repo / "broken.toml").write_text("[project\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "base")

    cfg = cfg_with_versions(repo, "broken.toml", "pyproject.toml")
    assert versioning.read_version_at(cfg, "HEAD") == "1.2.3"


def test_bumping_a_toml_touches_only_the_project_table(tmp_path):
    path = tmp_path / "pyproject.toml"
    path.write_text(PYPROJECT)
    cfg = cfg_with_versions(tmp_path, "pyproject.toml")

    assert versioning.apply_version(cfg, "1.3.0") == ["pyproject.toml"]
    patched = path.read_text()
    assert 'version = "1.3.0"' in patched
    assert 'version = "9.9.9"' in patched  # [tool.poetry] left alone
    assert versioning.read_version(cfg) == "1.3.0"


def test_bumping_a_toml_relocks_uv_when_a_lockfile_is_present(tmp_path):
    """A uv.lock pins its own project's version (editable-installed, so it is
    self-referencing) -- leave it stale and `uv lock --check` fails on this
    commit and only this commit, which is exactly the one promotion just
    produced. Reproduced live: vibey's own 0.5.0 and 0.6.0 releases both
    shipped a uv.lock still reading the prior version."""
    path = tmp_path / "pyproject.toml"
    path.write_text('[project]\nname = "demo"\nversion = "1.2.3"\nrequires-python = ">=3.12"\n')
    subprocess.run(["uv", "lock"], cwd=tmp_path, check=True, capture_output=True)
    stale_lock = (tmp_path / "uv.lock").read_text()
    assert "1.2.3" in stale_lock

    cfg = cfg_with_versions(tmp_path, "pyproject.toml")
    written = versioning.apply_version(cfg, "1.3.0")

    assert written == ["pyproject.toml", "uv.lock"]
    fresh_lock = (tmp_path / "uv.lock").read_text()
    assert "1.3.0" in fresh_lock
    assert fresh_lock != stale_lock


def test_bumping_a_toml_without_a_lockfile_does_not_invent_one(tmp_path):
    path = tmp_path / "pyproject.toml"
    path.write_text('[project]\nname = "demo"\nversion = "1.2.3"\n')
    cfg = cfg_with_versions(tmp_path, "pyproject.toml")

    assert versioning.apply_version(cfg, "1.3.0") == ["pyproject.toml"]
    assert not (tmp_path / "uv.lock").exists()


def test_a_relock_failure_surfaces_as_a_runtime_error(tmp_path, monkeypatch):
    path = tmp_path / "pyproject.toml"
    path.write_text('[project]\nname = "demo"\nversion = "1.2.3"\n')
    (tmp_path / "uv.lock").write_text("stale")
    cfg = cfg_with_versions(tmp_path, "pyproject.toml")

    def fake_run(cmd, **kwargs):
        assert cmd == ["uv", "lock"]
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="boom")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="uv lock: boom"):
        versioning.apply_version(cfg, "1.3.0")


def test_bumping_a_toml_whose_project_table_is_last(tmp_path):
    path = tmp_path / "pyproject.toml"
    path.write_text('[project]\nname = "demo"\nversion = "1.2.3"\n')
    cfg = cfg_with_versions(tmp_path, "pyproject.toml")
    versioning.apply_version(cfg, "1.3.0")
    assert versioning.read_version(cfg) == "1.3.0"


def test_a_toml_with_no_project_table_cannot_be_bumped(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[tool.black]\nline-length = 100\n")
    cfg = cfg_with_versions(tmp_path, "pyproject.toml")
    with pytest.raises(RuntimeError, match="no \\[project\\] table"):
        versioning.apply_version(cfg, "1.3.0")


def test_a_project_table_carrying_no_version_cannot_be_bumped(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "demo"\n\n[tool.x]\n')
    cfg = cfg_with_versions(tmp_path, "pyproject.toml")
    with pytest.raises(RuntimeError, match="expected one \\[project\\] version"):
        versioning.apply_version(cfg, "1.3.0")


# ---------------------------------------------------------------- managed workflows


def test_by_default_every_bundled_workflow_is_managed(repo):
    cfg = GhConfig(root=repo)
    names = {a.hook for a in install.install(cfg)}
    assert ".github/workflows/provenance.yml" in names
    assert ".github/workflows/merge-train.yml" in names
    assert install.installed(cfg) == (True, [])


def test_a_repository_can_take_the_hooks_without_the_workflows(repo):
    """The case that matters: a repo whose own workflows already do more.

    Without this, `check` fails forever on workflows the repository deliberately does not
    want — and a check that cannot pass is a check people route around.
    """
    cfg = GhConfig(root=repo, managed_workflows=())
    actions = install.install(cfg)

    # The hooks and the append-only merge rule are install-level concerns that do not
    # depend on any workflow, so they arrive even when no workflow is wanted.
    assert {a.hook for a in actions} == {"commit-msg", "pre-push", ".gitattributes"}
    assert not (repo / ".github/workflows/provenance.yml").exists()
    assert install.installed(cfg) == (True, [])


def test_a_repository_can_take_just_one_of_them(repo):
    cfg = GhConfig(root=repo, managed_workflows=("provenance.yml",))
    install.install(cfg)

    assert (repo / ".github/workflows/provenance.yml").exists()
    assert not (repo / ".github/workflows/merge-train.yml").exists()
    assert install.installed(cfg) == (True, [])


def test_an_unmanaged_workflow_that_drifts_is_not_reported(repo):
    """It is the repository's file, not ours; saying otherwise would be noise."""
    full = GhConfig(root=repo)
    install.install(full)
    (repo / ".github/workflows/merge-train.yml").write_text("name: mine now\n")

    assert install.installed(full)[0] is False  # managed: drift is reported
    hooks_only = GhConfig(root=repo, managed_workflows=("provenance.yml",))
    assert install.installed(hooks_only) == (True, [])


def test_the_workflow_list_is_read_from_the_config_file(tmp_path):
    from vibey_gh.config import load_config

    (tmp_path / ".git").mkdir()
    (tmp_path / ".vibey-gh.toml").write_text('[install]\nworkflows = ["provenance.yml"]\n')
    assert load_config(tmp_path).managed_workflows == ("provenance.yml",)

    (tmp_path / ".vibey-gh.toml").write_text("[install]\nworkflows = []\n")
    assert load_config(tmp_path).managed_workflows == ()


def test_omitting_the_section_means_all_of_them(tmp_path):
    from vibey_gh.config import load_config

    (tmp_path / ".git").mkdir()
    (tmp_path / ".vibey-gh.toml").write_text("[branches]\nintegration = 'dev'\n")
    assert load_config(tmp_path).managed_workflows is None


# ---------------------------------------------------------------- pinned tooling version


def test_pin_version_defaults_to_false_and_is_read_from_config(tmp_path):
    from vibey_gh.config import load_config

    assert GhConfig(root=tmp_path).pin_version is False

    (tmp_path / ".git").mkdir()
    (tmp_path / ".vibey-gh.toml").write_text("[install]\npin_version = true\n")
    assert load_config(tmp_path).pin_version is True


def test_pinning_the_tooling_version_is_a_visible_one_line_diff(repo):
    """Turning the key on, and a later release, both show up as one changed line."""
    from vibey_gh import __version__
    from vibey_gh.install import WORKFLOWS, render_workflow

    floating = render_workflow(WORKFLOWS / "merge-train.yml", GhConfig(root=repo))
    assert "python -m pip install --quiet vibey-gh\n" in floating
    assert "vibey-gh==" not in floating

    pinned = render_workflow(WORKFLOWS / "merge-train.yml", GhConfig(root=repo, pin_version=True))
    assert f'python -m pip install --quiet "vibey-gh=={__version__}"\n' in pinned
    assert "python -m pip install --quiet vibey-gh\n" not in pinned
    # The self-hosting branch is untouched either way — it cannot pin to a published
    # release that may not exist yet.
    assert "python -m pip install --quiet -e .\n" in floating
    assert "python -m pip install --quiet -e .\n" in pinned


# ---------------------------------------------------------------- holding for review


def a_held_verdict(number: int = 7) -> merge_train.Verdict:
    return merge_train.Verdict(
        number, "their work", "outsider", "needs review", held_for_review=True
    )


def test_holding_labels_the_pull_request_and_mentions_the_owner(fake_gh):
    cfg = GhConfig(root=Path.cwd(), owner="theowner")
    script(
        fake_gh,
        {
            "pr edit 7 --add-label needs-human-review": {},
            "pr view 7 --json comments -q .comments[].body": {"out": "some unrelated comment\n"},
            # the comment body is long; the fake matches on the exact argv, so allow anything
        },
    )
    merge_train.hold_for_review(a_held_verdict(), cfg)

    joined = "\n".join(calls(fake_gh))
    assert "pr edit 7 --add-label needs-human-review" in joined
    assert "@theowner" in joined and "@outsider" in joined
    assert "awaiting your review" in joined


def test_a_missing_label_is_created_then_applied(fake_gh):
    cfg = GhConfig(root=Path.cwd(), owner="theowner")
    # No scripted answer for `pr edit`, so it fails — as it does when the label does not
    # exist in the repository yet.
    script(fake_gh, {"pr view 7 --json comments -q .comments[].body": {"out": ""}})
    merge_train.hold_for_review(a_held_verdict(), cfg)

    made = [c for c in calls(fake_gh) if c.startswith("label create")]
    assert made and "needs-human-review" in made[0] and "D93F0B" in made[0]
    # and it retries the edit afterwards
    assert len([c for c in calls(fake_gh) if c.startswith("pr edit 7")]) == 2


def test_the_owner_is_mentioned_only_once(fake_gh):
    """Repeating it every week would train the owner to ignore it."""
    cfg = GhConfig(root=Path.cwd(), owner="theowner")
    script(
        fake_gh,
        {
            "pr edit 7 --add-label needs-human-review": {},
            "pr view 7 --json comments -q .comments[].body": {
                "out": "@theowner ... it is **awaiting your review** rather than merging\n"
            },
        },
    )
    merge_train.hold_for_review(a_held_verdict(), cfg)
    assert not [c for c in calls(fake_gh) if c.startswith("pr comment")]


def test_without_a_configured_owner_nobody_is_mentioned(fake_gh):
    cfg = GhConfig(root=Path.cwd(), owner="")
    script(fake_gh, {"pr edit 7 --add-label needs-human-review": {}})
    merge_train.hold_for_review(a_held_verdict(), cfg)
    assert not [c for c in calls(fake_gh) if c.startswith("pr comment")]


def test_an_empty_label_skips_labelling_but_still_notifies(fake_gh):
    cfg = GhConfig(root=Path.cwd(), owner="theowner")
    script(fake_gh, {"pr view 7 --json comments -q .comments[].body": {"out": ""}})
    merge_train.hold_for_review(a_held_verdict(), cfg, label="")

    assert not [c for c in calls(fake_gh) if c.startswith("pr edit")]
    assert [c for c in calls(fake_gh) if c.startswith("pr comment")]


def test_a_gh_that_cannot_read_the_comments_still_notifies(fake_gh):
    """Better a duplicate mention than a silent hold."""
    cfg = GhConfig(root=Path.cwd(), owner="theowner")
    script(fake_gh, {"pr edit 7 --add-label needs-human-review": {}})
    merge_train.hold_for_review(a_held_verdict(), cfg)
    assert [c for c in calls(fake_gh) if c.startswith("pr comment")]


def test_the_trust_gate_marks_the_verdict_as_held():
    cfg = GhConfig(
        root=Path.cwd(),
        owner="theowner",
        trusted_authors=("theowner",),
        pr_automation=PrAutomationConfig(enabled=False),
    )
    outside = merge_train.judge({"number": 7, "title": "t", "author": {"login": "outsider"}}, cfg)
    assert outside.held_for_review is True


def test_merge_train_trust_without_an_owner():
    cfg = GhConfig(root=Path.cwd(), owner="", trusted_authors=("trusted",))
    verdict = merge_train.judge({"number": 7, "title": "t", "author": {"login": "trusted"}}, cfg)
    assert "PR automation gate" in verdict.reason


def test_event_driven_merge_guards_and_single_pr_lookup(monkeypatch):
    cfg = GhConfig(root=Path.cwd(), owner="owner", trusted_authors=("owner",))
    trusted_without_gate = merge_train.judge(
        {"number": 1, "title": "t", "author": {"login": "owner"}}, cfg
    )
    assert "PR automation gate" in trusted_without_gate.reason
    unreviewed = merge_train.judge(
        {"number": 1, "title": "t", "author": {"login": "outsider"}}, cfg
    )
    assert "automated outside-author review" in unreviewed.reason
    behind = merge_train.judge(
        {"number": 1, "title": "t", "author": {"login": "owner"}, "mergeStateStatus": "BEHIND"},
        cfg,
    )
    assert "behind" in behind.reason
    blocked = merge_train.judge(
        {"number": 1, "title": "t", "author": {"login": "owner"}, "labels": [pa.BLOCKED_LABEL]},
        cfg,
    )
    assert "operator" in blocked.reason
    outsider = merge_train.judge(
        {
            "number": 1,
            "title": "t",
            "author": {"login": "outsider"},
            "statusCheckRollup": [
                {"name": "PR automation / gate", "status": "COMPLETED", "conclusion": "SUCCESS"}
            ],
        },
        cfg,
    )
    assert outsider.ready
    monkeypatch.setattr(merge_train, "_gh_json", lambda *a: {"number": 9})
    assert merge_train.pull_request(9) == {"number": 9, "statusCheckRollup": []}
    assert merge_train.open_pull_requests(cfg, 9) == [{"number": 9, "statusCheckRollup": []}]
    assert merge_train.method_for({"baseRefName": "main"}, cfg, "squash") == "rebase"
    assert merge_train.method_for({"baseRefName": "develop"}, cfg, "merge") == "merge"

    draft = merge_train.judge(
        {"number": 8, "title": "t", "isDraft": True, "author": {"login": "outsider"}}, cfg
    )
    assert draft.held_for_review is False  # a draft is the contributor's to fix


def test_read_text_uses_the_value_when_the_path_probe_itself_fails(monkeypatch):
    """`_read_text` accepts a literal value, a path, or `-`. Deciding which means probing
    the filesystem, and that probe can itself raise: a long inline JSON payload can exceed
    the platform's filename limit. The value must still be usable when it does — the probe
    failing says nothing about the value being valid.
    """
    from pathlib import Path

    from vibey_gh import cli

    def explode(self: Path) -> bool:
        raise OSError(63, "File name too long")

    monkeypatch.setattr(Path, "is_file", explode)

    payload = '{"pass": true}'
    assert cli._read_text(payload) == payload


def test_owed_at_rederives_against_an_arbitrary_committed_head(repo):
    """#254: the merge-time question. A head that gained code changes after the last
    bump owes a release commit; a head with a staged bump owes nothing; docs-only
    heads owe nothing."""
    import subprocess

    from vibey_gh import versioning
    from vibey_gh.config import load_config

    def git(*a):
        subprocess.run(["git", *a], cwd=repo, capture_output=True, check=True)

    (repo / ".vibey-gh.toml").write_text(
        '[version]\nfiles = ["src/__init__.py", "manifest.json"]\n'
        'code_paths = ["src/"]\ncontent_paths = ["content/"]\n',
        encoding="utf-8",
    )
    (repo / "src").mkdir()
    (repo / "src" / "__init__.py").write_text('__version__ = "1.0.0"\n')
    (repo / "manifest.json").write_text('{"metadata": {"version": "1.0.0"}}\n')
    git("add", "-A")
    git("commit", "-qm", "base")
    cfg = load_config(repo)
    git("branch", "release-line")
    (repo / "src" / "mod.py").write_text("x = 1\n")
    git("add", "-A")
    git("commit", "-qm", "feat: code change without a bump")
    owed, why = versioning.owed_at(cfg, "release-line", "HEAD")
    assert owed is not None and "code changed" in why

    (repo / "src" / "__init__.py").write_text('__version__ = "1.1.0"\n')
    (repo / "manifest.json").write_text('{"metadata": {"version": "1.1.0"}}\n')
    git("add", "-A")
    git("commit", "-qm", "chore(release): 1.1.0")
    owed, why = versioning.owed_at(cfg, "release-line", "HEAD")
    assert owed is None and "deliberate bump" in why

    owed, why = versioning.owed_at(cfg, "no-such-ref", "HEAD")
    assert owed is None and "refusing to guess" in why
    owed, why = versioning.owed_at(cfg, "release-line", "also-no-such-ref")
    assert owed is None and "refusing to guess" in why


def test_the_train_holds_an_unbumped_promotion(repo, monkeypatch):
    """#254's teeth: a promotion whose current head owes a bump is not ready, and the
    reason names the exact release commit owed."""
    from vibey_gh import merge_train, versioning
    from vibey_gh.config import load_config

    cfg = load_config(repo)
    promotion = {
        "number": 9,
        "title": "chore(release): 1.0.0",
        "author": {"login": cfg.owner or "owner"},
        "isDraft": False,
        "mergeable": "MERGEABLE",
        "mergeStateStatus": "CLEAN",
        "reviewDecision": "",
        "labels": [],
        "statusCheckRollup": [
            {
                "name": "PR automation / gate",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
            }
        ],
        "baseRefName": cfg.release_branch,
        "headRefName": cfg.integration_branch,
        "headRefOid": "deadbeef",
    }
    monkeypatch.setattr(
        versioning, "owed_at", lambda c, since, head: ("1.1.0", "only internal code changed")
    )
    verdict = merge_train.judge(promotion, cfg)
    assert not verdict.ready
    assert "chore(release): 1.1.0" in (verdict.reason or "")

    monkeypatch.setattr(
        versioning, "owed_at", lambda c, since, head: (None, "a deliberate bump is in place")
    )
    verdict = merge_train.judge(promotion, cfg)
    assert verdict.ready
