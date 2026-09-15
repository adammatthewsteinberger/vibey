# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for the `vibey-gh` command surface.

The CLI is thin by design — the decisions live in the modules beside it — so these tests
check wiring and exit codes rather than re-testing the logic.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from vibey_gh import (
    github_release,
    issue_automation,
    merge_train,
    pr_automation,
    realign as realign_mod,
    reconcile,
    rulesets,
)
from vibey_gh.cli import main
from vibey_gh.config import load_config
from vibey_gh.merge_train import Verdict


@pytest.fixture
def repo(tmp_path: Path, monkeypatch) -> Path:
    def git(*a):
        subprocess.run(["git", *a], cwd=tmp_path, capture_output=True, check=True)

    git("init", "-q", ".")
    git("config", "user.email", "t@example.com")
    git("config", "user.name", "t")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "__init__.py").write_text('__version__ = "1.0.0"\n')
    (tmp_path / "manifest.json").write_text(json.dumps({"metadata": {"version": "1.0.0"}}) + "\n")
    (tmp_path / "content").mkdir()
    (tmp_path / "content" / "a.md").write_text("a\n")
    (tmp_path / ".vibey-gh.toml").write_text(
        '[fingerprint]\nsources = ["src/*.py"]\n'
        '[version]\nfiles = ["src/__init__.py", "manifest.json"]\n'
        'content_paths = ["content/"]\ncode_paths = ["src/"]\n'
        '[merge_train]\nowner = "owner"\ntrusted_authors = ["owner"]\n'
        "[documentation]\nenabled = false\n"
    )
    git("add", "-A")
    git("commit", "-qm", "base")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_install_then_check_passes(repo, capsys):
    assert main(["check", "--ci"]) == 1  # nothing installed, no headers
    assert main(["install"]) == 0
    assert main(["check", "--ci", "--apply"]) == 0
    assert "ok" in capsys.readouterr().out


def test_check_quiet_is_exit_status_only(repo, capsys):
    assert main(["check", "--ci", "--quiet"]) == 1
    assert capsys.readouterr().out == ""


def test_check_quiet_succeeds_after_install(repo, capsys):
    main(["install"])
    main(["check", "--ci", "--apply"])
    assert main(["check", "--ci", "--quiet"]) == 0


def test_check_reports_missing_documentation(repo, capsys):
    """The agent-docs layout is owed by every managed repository; this project's own
    narrative is not owed by anyone else."""
    config = repo / ".vibey-gh.toml"
    config.write_text(config.read_text().replace("enabled = false", "enabled = true"))
    assert main(["check", "--ci"]) == 1
    err = capsys.readouterr().err
    assert "documentation:" in err
    assert "AGENTS.md is missing" in err
    # Nothing is demanded of their README beyond existing — its subject is their product.
    for imposed in ("Why vibey-gh", "provenance sentence", "project surface"):
        assert imposed not in err, imposed


def test_check_reports_a_scan_workflow_that_cannot_fire_for_a_pull_request(repo, capsys):
    main(["install"])
    assert main(["check", "--ci", "--apply"]) == 0
    config = repo / ".vibey-gh.toml"
    config.write_text(config.read_text() + '\n[pr_automation]\nscan_workflows = ["Custom"]\n')
    workflows = repo / ".github" / "workflows"
    (workflows / "custom.yml").write_text("name: Custom\non:\n  push:\n")
    assert main(["check", "--ci"]) == 1
    err = capsys.readouterr().err
    assert "'Custom'" in err
    assert "pull_request" in err


def test_check_reports_a_duplicate_header(repo, capsys):
    cfg = load_config(repo)
    target = repo / "src" / "__init__.py"
    target.write_text(f"{cfg.header}\n{cfg.header}\n" + target.read_text())
    assert main(["check", "--ci"]) == 1
    assert "more than once" in capsys.readouterr().err


def test_check_reports_a_missing_commit_trailer(repo, capsys):
    main(["check", "--ci", "--apply"])
    # --no-verify, because `install` puts in the commit-msg hook that would add the
    # trailer for us — the point here is a commit that escaped it.
    subprocess.run(
        ["git", "commit", "-q", "--no-verify", "--allow-empty", "-m", "bare"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    assert main(["check", "--ci", "--commits", "HEAD~1..HEAD"]) == 1
    assert "trailer" in capsys.readouterr().err


def test_version_reports_none_when_nothing_shipped(repo, capsys):
    subprocess.run(["git", "branch", "-q", "base"], cwd=repo, check=True)
    (repo / "README.md").write_text("docs\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "docs"], cwd=repo, check=True, capture_output=True)
    assert main(["version", "--since", "base"]) == 0
    assert capsys.readouterr().out.strip() == "none"


def test_version_bumps_minor_and_can_apply(repo, capsys):
    subprocess.run(["git", "branch", "-q", "base"], cwd=repo, check=True)
    (repo / "content" / "a.md").write_text("changed\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "content"], cwd=repo, check=True, capture_output=True)

    assert main(["version", "--since", "base", "--explain", "--apply"]) == 0
    assert capsys.readouterr().out.strip() == "1.1.0"
    assert '__version__ = "1.1.0"' in (repo / "src" / "__init__.py").read_text()
    assert json.loads((repo / "manifest.json").read_text())["metadata"]["version"] == "1.1.0"


def test_version_bumps_without_explanation_or_apply(repo, capsys):
    subprocess.run(["git", "branch", "-q", "base"], cwd=repo, check=True)
    (repo / "content" / "a.md").write_text("changed\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "content"], cwd=repo, check=True)

    assert main(["version", "--since", "base"]) == 0
    assert capsys.readouterr().out.strip() == "1.1.0"


def test_version_dev_builds(repo, capsys):
    assert main(["version", "--dev", "11"]) == 0
    assert capsys.readouterr().out.strip() == "1.0.0.dev11"
    assert main(["version", "--dev", "12", "--apply"]) == 0
    capsys.readouterr()
    assert "1.0.0.dev12" in (repo / "src" / "__init__.py").read_text()


def test_merge_train_with_nothing_open(repo, capsys, monkeypatch):
    monkeypatch.setattr(merge_train, "open_pull_requests", lambda cfg: [])
    assert main(["merge-train"]) == 0
    assert "no open pull requests" in capsys.readouterr().out


def test_merge_train_merges_ready_and_skips_the_rest(repo, capsys, monkeypatch):
    prs = [{"number": 1}, {"number": 2}]
    monkeypatch.setattr(merge_train, "open_pull_requests", lambda cfg: prs)
    monkeypatch.setattr(
        merge_train,
        "judge",
        lambda pr, cfg: Verdict(pr["number"], "t", "owner", None if pr["number"] == 1 else "draft"),
    )
    merged: list[int] = []
    monkeypatch.setattr(
        merge_train, "merge", lambda n, m, b=None: (merged.append(n), (True, True, ""))[1]
    )

    assert main(["merge-train"]) == 0
    out = capsys.readouterr().out
    assert merged == [1]
    assert "#1 squash-merged (review requirement bypassed)" in out
    assert "#2 skipped — draft" in out
    assert "merged 1, skipped 1" in out


def test_merge_train_dry_run_merges_nothing(repo, capsys, monkeypatch):
    monkeypatch.setattr(merge_train, "open_pull_requests", lambda cfg: [{"number": 3}])
    monkeypatch.setattr(merge_train, "judge", lambda pr, cfg: Verdict(3, "t", "owner", None))
    monkeypatch.setattr(
        merge_train, "merge", lambda n, m, b=None: pytest.fail("dry run must not merge")
    )
    assert main(["merge-train", "--dry-run"]) == 0
    assert "would merge" in capsys.readouterr().out


def test_merge_train_reports_a_refused_merge(repo, capsys, monkeypatch):
    monkeypatch.setattr(merge_train, "open_pull_requests", lambda cfg: [{"number": 9}])
    monkeypatch.setattr(merge_train, "judge", lambda pr, cfg: Verdict(9, "t", "owner", None))
    monkeypatch.setattr(
        merge_train, "merge", lambda n, m, b=None: (False, True, "GraphQL: repo not granted")
    )
    assert main(["merge-train"]) == 0
    out = capsys.readouterr().out
    # The API's own words, not a guess. "refused it" alone sent a token-scope problem
    # into ruleset archaeology.
    assert "could not be merged — GraphQL: repo not granted" in out


def test_merge_train_supplies_the_trailer_for_a_body_that_lacks_it(repo, capsys, monkeypatch):
    """A squash commit takes its body from the pull request, and a bot's body never has
    the trailer — so the train supplies one, or it manufactures the exact trailer-less
    commit provenance refuses. A body that already carries it is left alone."""
    prs = [
        {"number": 4, "body": "bump things"},
        {"number": 5, "body": "done\n\n" + load_config().trailer},
    ]
    monkeypatch.setattr(merge_train, "open_pull_requests", lambda cfg: prs)
    monkeypatch.setattr(merge_train, "judge", lambda pr, cfg: Verdict(pr["number"], "t", "o", None))
    seen: dict[int, object] = {}
    monkeypatch.setattr(
        merge_train, "merge", lambda n, m, b=None: (seen.__setitem__(n, b), (True, False, ""))[1]
    )
    assert main(["merge-train"]) == 0
    trailer = load_config().trailer
    assert seen[4] is not None and seen[4].endswith(trailer) and "bump things" in seen[4]
    assert seen[5] is None


@pytest.mark.parametrize(
    "deleted,fragment",
    [(True, "deleted merged topic branch"), (False, "topic-branch cleanup failed")],
)
def test_merge_train_cleans_only_eligible_topic_branches(
    repo, capsys, monkeypatch, deleted, fragment
):
    pr = {"number": 9, "headRefName": "fix/thing"}
    monkeypatch.setattr(merge_train, "open_pull_requests", lambda cfg: [pr])
    monkeypatch.setattr(merge_train, "judge", lambda pr, cfg: Verdict(9, "t", "owner", None))
    monkeypatch.setattr(merge_train, "merge", lambda n, m, b=None: (True, False, ""))
    monkeypatch.setattr(merge_train, "delete_head_branch", lambda value: deleted)
    assert main(["merge-train"]) == 0
    assert fragment in capsys.readouterr().out


def test_realign_success_and_failure(repo, capsys, monkeypatch):
    monkeypatch.setattr(realign_mod, "realign", lambda cfg: (True, "converged"))
    assert main(["realign"]) == 0
    assert "converged" in capsys.readouterr().out

    def boom(cfg):
        raise RuntimeError("refused by the ruleset")

    monkeypatch.setattr(realign_mod, "realign", boom)
    assert main(["realign"]) == 1
    assert "refused by the ruleset" in capsys.readouterr().err


def test_trailer_helpers(repo, capsys):
    main(["trailer"])
    assert capsys.readouterr().out.startswith("Made-With:")
    main(["trailer-key"])
    assert capsys.readouterr().out.strip() == "Made-With"


def test_conventional_message_normalizes_file_and_stdin(repo, tmp_path, monkeypatch, capsys):
    message = tmp_path / "COMMIT_EDITMSG"
    message.write_text("Bad subject\n\nBody\n")
    assert main(["conventional-message", "--file", str(message)]) == 0
    assert message.read_text() == "chore: Bad subject\n\nBody\n"
    monkeypatch.setattr("sys.stdin.read", lambda: "fix: already valid\n")
    assert main(["conventional-message"]) == 0
    assert capsys.readouterr().out == "fix: already valid\n"


def test_conventional_check_reports_invalid_range(repo, capsys):
    subprocess.run(
        ["git", "commit", "-q", "--allow-empty", "-m", "Invalid subject"],
        cwd=repo,
        check=True,
    )
    assert main(["conventional-check", "--commits", "HEAD~1..HEAD"]) == 1
    assert "Invalid subject" in capsys.readouterr().out
    subprocess.run(
        ["git", "commit", "-q", "--allow-empty", "-m", "fix: valid subject"],
        cwd=repo,
        check=True,
    )
    assert main(["conventional-check", "--commits", "HEAD~1..HEAD"]) == 0


def test_check_names_the_commit_range_it_cleared(repo, capsys):
    main(["install"])
    main(["check", "--ci", "--apply"])
    capsys.readouterr()
    subprocess.run(
        ["git", "commit", "-q", "--allow-empty", "-m", "fingerprinted"],
        cwd=repo,
        check=True,
        capture_output=True,
    )  # the hook adds the trailer

    assert main(["check", "--ci", "--commits", "HEAD~1..HEAD"]) == 0
    assert "every commit in HEAD~1..HEAD" in capsys.readouterr().out


def held(number: int = 7, author: str = "outsider") -> Verdict:
    return Verdict(
        number,
        "their work",
        author,
        "from @outsider and not approved — needs owner's review",
        held_for_review=True,
    )


def test_a_pull_request_held_on_the_owner_is_labelled_and_announced(repo, monkeypatch, capsys):
    monkeypatch.setattr(merge_train, "open_pull_requests", lambda cfg: [{"number": 7}])
    monkeypatch.setattr(merge_train, "judge", lambda pr, cfg: held())
    calls: list[tuple] = []
    monkeypatch.setattr(
        merge_train, "hold_for_review", lambda v, cfg, label: calls.append((v.number, label))
    )

    assert main(["merge-train"]) == 0
    assert calls == [(7, "needs-human-review")]
    assert "#7 skipped" in capsys.readouterr().out


def test_a_dry_run_labels_nothing_and_announces_nothing(repo, monkeypatch):
    monkeypatch.setattr(merge_train, "open_pull_requests", lambda cfg: [{"number": 7}])
    monkeypatch.setattr(merge_train, "judge", lambda pr, cfg: held())
    monkeypatch.setattr(
        merge_train,
        "hold_for_review",
        lambda *a, **k: pytest.fail("a dry run must not touch the PR"),
    )
    assert main(["merge-train", "--dry-run"]) == 0


def test_labelling_can_be_turned_off(repo, monkeypatch):
    monkeypatch.setattr(merge_train, "open_pull_requests", lambda cfg: [{"number": 7}])
    monkeypatch.setattr(merge_train, "judge", lambda pr, cfg: held())
    monkeypatch.setattr(
        merge_train, "hold_for_review", lambda *a, **k: pytest.fail("--label '' means do nothing")
    )
    assert main(["merge-train", "--label", ""]) == 0


def test_an_ordinary_skip_is_not_announced(repo, monkeypatch):
    """A draft is the contributor's to fix; nobody needs paging about it."""
    monkeypatch.setattr(merge_train, "open_pull_requests", lambda cfg: [{"number": 7}])
    monkeypatch.setattr(merge_train, "judge", lambda pr, cfg: Verdict(7, "t", "someone", "draft"))
    monkeypatch.setattr(
        merge_train,
        "hold_for_review",
        lambda *a, **k: pytest.fail("a draft is not held for review"),
    )
    assert main(["merge-train"]) == 0


def test_the_run_writes_a_markdown_summary(repo, monkeypatch, tmp_path):
    monkeypatch.setattr(
        merge_train, "open_pull_requests", lambda cfg: [{"number": 1}, {"number": 2}]
    )
    monkeypatch.setattr(
        merge_train,
        "judge",
        lambda pr, cfg: Verdict(
            pr["number"], f"pr {pr['number']}", "owner", None if pr["number"] == 1 else "draft"
        ),
    )
    monkeypatch.setattr(merge_train, "merge", lambda n, m, b=None: (True, False, ""))

    out = tmp_path / "summary.md"
    assert main(["merge-train", "--summary", str(out)]) == 0

    body = out.read_text()
    assert "| PR | Title | Outcome |" in body
    assert "| #1 | pr 1 | squash-merged |" in body
    assert "| #2 | pr 2 | skipped — draft |" in body
    assert "Merged 1, skipped 1." in body


def test_the_summary_defaults_to_the_actions_job_summary(repo, monkeypatch, tmp_path):
    out = tmp_path / "gh-summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(out))
    monkeypatch.setattr(merge_train, "open_pull_requests", lambda cfg: [])
    assert main(["merge-train"]) == 0
    assert "No open pull requests." in out.read_text()


def test_a_summary_that_cannot_be_written_does_not_fail_the_train(
    repo, monkeypatch, capsys, tmp_path
):
    monkeypatch.setattr(merge_train, "open_pull_requests", lambda cfg: [])
    assert main(["merge-train", "--summary", str(tmp_path / "no-such-dir" / "s.md")]) == 0
    assert "could not write the summary" in capsys.readouterr().err


def test_promote_reports_what_happened(repo, monkeypatch, capsys, tmp_path):
    from vibey_gh import promote as promote_mod

    result = promote_mod.Promotion(
        changed_files=4, version="1.1.0", bumped="1.1.0", pull_request=42, merged=True
    )
    result.say("bumped to 1.1.0 and pushed to develop")
    result.say("#42 rebase-merged into main")
    monkeypatch.setattr(promote_mod, "promote", lambda cfg, **kw: result)

    out_file = tmp_path / "summary.md"
    assert main(["promote", "--summary", str(out_file)]) == 0

    out = capsys.readouterr().out
    assert "bumped to 1.1.0 and pushed to develop" in out
    assert "4 file(s) differ; version 1.1.0" in out

    body = out_file.read_text()
    assert body.startswith("## Promotion")
    assert "- #42 rebase-merged into main" in body
    assert "Version: `1.1.0`" in body


def test_promote_passes_its_flags_through(repo, monkeypatch):
    from vibey_gh import promote as promote_mod

    seen: dict = {}

    def fake(cfg, **kw):
        seen.update(kw)
        return promote_mod.Promotion()

    monkeypatch.setattr(promote_mod, "promote", fake)
    assert main(["promote", "--dry-run", "--no-wait", "--method", "squash"]) == 0
    assert seen == {"dry_run": True, "wait": False, "method": "squash"}


def test_a_promotion_that_cannot_proceed_is_an_error(repo, monkeypatch, capsys):
    from vibey_gh import promote as promote_mod

    def boom(cfg, **kw):
        raise RuntimeError("could not push the version bump to develop")

    monkeypatch.setattr(promote_mod, "promote", boom)
    assert main(["promote"]) == 1
    assert "could not push the version bump" in capsys.readouterr().err


def test_pr_automation_cli_surfaces(repo, monkeypatch, tmp_path, capsys):
    evaluation = pr_automation.Evaluation(7, "abc", "develop", "owner", True, "ready")
    monkeypatch.setattr(pr_automation, "evaluate_pr", lambda *a: evaluation)
    assert main(["pr-automation", "evaluate", "--pr", "7", "--head-sha", "abc"]) == 0
    assert json.loads(capsys.readouterr().out)["state"] == "ready"

    monkeypatch.setattr(
        pr_automation,
        "ready_draft",
        lambda *a: {"promoted": True, "reason": "current head is stable"},
    )
    assert main(["pr-automation", "ready-draft", "--pr", "7", "--head-sha", "abc"]) == 0
    assert json.loads(capsys.readouterr().out)["promoted"] is True

    state = pr_automation.AutomationState("abc", "abc")
    calls = []
    monkeypatch.setattr(
        pr_automation,
        "record",
        lambda number, payload, kind: calls.append((number, payload, kind)) or state,
    )
    payload = tmp_path / "payload.json"
    payload.write_text('{"pass": true}')
    assert main(["pr-automation", "record-review", "--pr", "7", "--input", str(payload)]) == 0
    monkeypatch.setattr("sys.stdin.read", lambda: '{"fixable": true}')
    assert main(["pr-automation", "record-repair", "--pr", "7", "--input", "-"]) == 0
    assert calls == [(7, {"pass": True}, "review"), (7, {"fixable": True}, "repair")]

    monkeypatch.setattr(
        pr_automation, "mirror_fork", lambda *a: {"original_pr": 7, "replacement_pr": 8}
    )
    assert main(["pr-automation", "mirror-fork", "--pr", "7"]) == 0
    monkeypatch.setattr(pr_automation, "ensure_labels", lambda: calls.append("labels"))
    assert main(["pr-automation", "ensure-labels"]) == 0
    assert calls[-1] == "labels"


def _evaluation(**changes):
    values = dict(
        issue=55,
        title="Conventional commits bug",
        author="owner",
        trusted=True,
        state="solve",
        fingerprint="a" * 64,
        base="develop",
        branch="vibey-gh/issue/55-aaaaaaaa-conventional-commits-bug",
        attempt=1,
    )
    values.update(changes)
    return issue_automation.Evaluation(**values)


def test_issue_automation_cli_surfaces(repo, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(issue_automation, "evaluate_issue", lambda *a: _evaluation())
    assert main(["issue-automation", "evaluate", "--issue", "55"]) == 0
    decision = json.loads(capsys.readouterr().out)
    assert decision["state"] == "solve"
    assert decision["pr_title"] == "fix: Conventional commits bug"

    monkeypatch.setattr(issue_automation, "fetch_issue", lambda number: {"number": number})
    monkeypatch.setattr(issue_automation, "context", lambda issue, max_bytes: "briefing\n")
    assert main(["issue-automation", "context", "--issue", "55"]) == 0
    assert capsys.readouterr().out == "briefing\n"

    target = tmp_path / "nested" / "issue.md"
    assert main(["issue-automation", "context", "--issue", "55", "--output", str(target)]) == 0
    assert target.read_text(encoding="utf-8") == "briefing\n"
    assert "wrote 9 bytes" in capsys.readouterr().out

    state = issue_automation.IssueState(issue=55, fingerprint="abc", attempts=1)
    calls = []
    monkeypatch.setattr(
        issue_automation,
        "record",
        lambda number, payload: calls.append((number, payload)) or state,
    )
    payload = tmp_path / "payload.json"
    payload.write_text('{"solved": true}')
    assert (
        main(["issue-automation", "record-solution", "--issue", "55", "--input", str(payload)]) == 0
    )
    assert json.loads(capsys.readouterr().out)["attempts"] == 1
    assert calls == [(55, {"solved": True})]

    monkeypatch.setattr(issue_automation, "eligible_issues", lambda cfg: [_evaluation()])
    assert main(["issue-automation", "list-eligible"]) == 0
    assert [item["issue"] for item in json.loads(capsys.readouterr().out)] == [55]

    monkeypatch.setattr(issue_automation, "ensure_labels", lambda: calls.append("labels"))
    assert main(["issue-automation", "ensure-labels"]) == 0
    assert calls[-1] == "labels"


def test_issue_automation_cli_reports_failures(repo, monkeypatch, capsys):
    def boom(*a, **k):
        raise RuntimeError("gh issue view: not found")

    monkeypatch.setattr(issue_automation, "evaluate_issue", boom)
    assert main(["issue-automation", "evaluate", "--issue", "55"]) == 1
    assert "not found" in capsys.readouterr().err

    assert main(["issue-automation", "record-solution", "--issue", "55", "--input", "[]"]) == 1
    assert "must be an object" in capsys.readouterr().err


def test_self_heal_cli_sweeps_or_targets_one_pull_request(repo, monkeypatch, capsys):
    monkeypatch.setattr(pr_automation, "exhausted_pull_requests", lambda cfg: [4, 9])
    monkeypatch.setattr(
        pr_automation, "self_heal", lambda number, cfg: {"pr": number, "healed": True}
    )
    assert main(["pr-automation", "self-heal"]) == 0
    assert [item["pr"] for item in json.loads(capsys.readouterr().out)] == [4, 9]

    assert main(["pr-automation", "self-heal", "--pr", "7"]) == 0
    assert [item["pr"] for item in json.loads(capsys.readouterr().out)] == [7]


def test_conversation_cli_surfaces(repo, monkeypatch, tmp_path, capsys):
    from vibey_gh import conversation

    thread = {
        "number": 7,
        "title": "t",
        "state": "OPEN",
        "comments": [
            {"id": 41, "author": {"login": "owner"}, "body": "earlier"},
            {"id": 42, "author": {"login": "owner"}, "body": "@vibey explain"},
        ],
    }
    monkeypatch.setattr(conversation, "fetch_subject", lambda n: thread)

    assert main(["conversation", "evaluate", "--subject", "7"]) == 0
    decision = json.loads(capsys.readouterr().out)
    assert decision["comment_id"] == "42", "the newest comment is used by default"

    assert main(["conversation", "evaluate", "--subject", "7", "--comment-id", "41"]) == 0
    assert json.loads(capsys.readouterr().out)["state"] == "skip"

    assert main(["conversation", "context", "--subject", "7"]) == 0
    assert "Untrusted conversation" in capsys.readouterr().out

    target = tmp_path / "nested" / "thread.md"
    assert main(["conversation", "context", "--subject", "7", "--output", str(target)]) == 0
    assert "Untrusted conversation" in target.read_text(encoding="utf-8")
    assert "wrote" in capsys.readouterr().out

    posted: list = []
    monkeypatch.setattr(
        conversation, "reply", lambda n, body, cfg: posted.append((n, body)) or True
    )
    body = tmp_path / "answer.md"
    body.write_text("from a file", encoding="utf-8")
    assert main(["conversation", "reply", "--subject", "7", "--body", str(body)]) == 0
    assert posted[-1] == (7, "from a file")
    assert main(["conversation", "reply", "--subject", "7", "--body", "inline text"]) == 0
    assert posted[-1] == (7, "inline text")
    monkeypatch.setattr("sys.stdin.read", lambda: "from stdin")
    assert main(["conversation", "reply", "--subject", "7", "--body", "-"]) == 0
    assert posted[-1] == (7, "from stdin")

    state = conversation.ConversationState(subject=7, interactions=1)
    monkeypatch.setattr(conversation, "record", lambda n, payload: state)
    capsys.readouterr()  # discard the reply confirmations above
    assert main(["conversation", "record-response", "--subject", "7", "--input", "{}"]) == 0
    assert json.loads(capsys.readouterr().out)["interactions"] == 1


def test_conversation_cli_reports_failures(repo, monkeypatch, capsys):
    from vibey_gh import conversation

    monkeypatch.setattr(conversation, "fetch_subject", lambda n: {"number": 7, "comments": []})
    monkeypatch.setattr(conversation, "reply", lambda n, b, c: False)
    assert main(["conversation", "reply", "--subject", "7", "--body", "x"]) == 1
    assert "could not post the reply" in capsys.readouterr().err

    def boom(n):
        raise RuntimeError("gh issue view: not found")

    monkeypatch.setattr(conversation, "fetch_subject", boom)
    assert main(["conversation", "evaluate", "--subject", "7"]) == 1
    assert "not found" in capsys.readouterr().err


def test_reconcile_branches_cli_reports_each_decision(repo, monkeypatch, capsys):
    monkeypatch.setattr(
        reconcile,
        "reconcile",
        lambda cfg, dry_run: [
            {"pr": 1, "branch": "vibey-gh/a", "action": "close", "reason": "duplicate"}
        ],
    )
    assert main(["reconcile-branches", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "#1 (vibey-gh/a): close — duplicate" in out
    assert "reconciled 1 open pull request(s)" in out


def test_reconcile_branches_cli_distinguishes_deciding_from_doing(repo, monkeypatch, capsys):
    """A decision printed alone reads exactly like a success, and hides a branch that
    never moved — which is how a rebase that conflicted looked green for four runs."""
    monkeypatch.setattr(
        reconcile,
        "reconcile",
        lambda cfg, dry_run: [
            {
                "pr": 1,
                "branch": "vibey-gh/a",
                "action": "rebase",
                "reason": "1 unique commit(s)",
                "applied": False,
                "detail": "rebase conflicted; left for ordinary conflict resolution",
            },
            {
                "pr": 2,
                "branch": "vibey-gh/b",
                "action": "rebase",
                "reason": "2 unique commit(s)",
                "applied": True,
                "detail": "rebased aaaaaaa onto the new tip as bbbbbbb",
            },
            {
                "pr": 3,
                "branch": "vibey-gh/c",
                "action": "close",
                "reason": "duplicate",
                "applied": True,
                "deleted": False,
            },
        ],
    )
    assert main(["reconcile-branches"]) == 0
    out = capsys.readouterr().out
    assert "not applied: rebase conflicted" in out
    assert "branch deletion was refused by GitHub" in out
    assert "1 action(s) did not take effect" in out
    # The one that worked is not reported as stalled.
    assert out.count("not applied") == 1


def test_reconcile_branches_cli_reports_failures(repo, monkeypatch, capsys):
    def boom(*a, **k):
        raise ValueError("refusing to delete protected or unsafe branch 'develop'")

    monkeypatch.setattr(reconcile, "reconcile", boom)
    assert main(["reconcile-branches"]) == 1
    assert "refusing to delete" in capsys.readouterr().err


def test_rulesets_cli_reports_each_outcome(repo, monkeypatch, capsys):
    monkeypatch.setattr(
        rulesets,
        "reconcile",
        lambda cfg, dry_run: [
            {
                "ruleset": "vibey-gh: develop",
                "branch": "develop",
                "changed": True,
                "unexpected_rules": ["creation"],
                "applied": not dry_run,
            },
            {
                "ruleset": "vibey-gh: main",
                "branch": "main",
                "changed": False,
                "unexpected_rules": [],
                "applied": False,
            },
        ],
    )
    assert main(["rulesets", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "vibey-gh: develop (develop): changed" in out
    assert "unexpected rule(s) preserved: creation" in out
    assert "vibey-gh: main (main): current" in out
    assert "reconciled 2 ruleset(s)" in out


def test_rulesets_cli_reports_failures(repo, monkeypatch, capsys):
    def boom(*a, **k):
        raise RuntimeError("422 required status check contexts must be unique")

    monkeypatch.setattr(rulesets, "reconcile", boom)
    assert main(["rulesets"]) == 1
    assert "must be unique" in capsys.readouterr().err


def test_api_and_mcp_surface_failures_return_nonzero(repo, monkeypatch, capsys):
    from vibey_gh import surfaces

    monkeypatch.setattr(surfaces, "api_dispatch", lambda *a: (404, {"error": "missing"}))
    assert main(["api", "check"]) == 1
    assert json.loads(capsys.readouterr().out) == {"error": "missing"}

    monkeypatch.setattr(surfaces, "mcp_dispatch", lambda *a: {"error": {"code": -1}})
    assert main(["mcp", "check"]) == 1
    assert "error" in json.loads(capsys.readouterr().out)


def test_check_reports_untraceable_debug_branches(repo, capsys):
    bad = repo / "src" / "bad.py"
    bad.write_text(load_config().header + "\nif:\n")
    assert main(["check"]) == 1
    assert "debug logging:" in capsys.readouterr().err


@pytest.mark.parametrize("value", ("[]", "{bad"))
def test_pr_automation_cli_rejects_bad_json(repo, capsys, value):
    assert main(["pr-automation", "record-review", "--pr", "7", "--input", value]) == 1
    assert "vibey-gh:" in capsys.readouterr().err


def test_pr_automation_cli_accepts_inline_json_longer_than_filename_limit(repo, monkeypatch):
    payload = {"pass": False, "summary": "incomplete " * 1024}
    recorded = []
    state = pr_automation.AutomationState("abc", "abc")
    monkeypatch.setattr(
        pr_automation,
        "record",
        lambda number, value, kind: recorded.append((number, value, kind)) or state,
    )

    assert (
        main(
            [
                "pr-automation",
                "record-review",
                "--pr",
                "7",
                "--input",
                json.dumps(payload),
            ]
        )
        == 0
    )
    assert recorded == [(7, payload, "review")]


def test_pr_automation_cli_reports_runtime_errors(repo, monkeypatch, capsys):
    def boom(*args):
        raise RuntimeError("offline")

    monkeypatch.setattr(pr_automation, "evaluate_pr", boom)
    assert main(["pr-automation", "evaluate", "--pr", "7", "--head-sha", "abc"]) == 1
    assert "offline" in capsys.readouterr().err


def test_merge_train_targets_one_pr(repo, monkeypatch):
    requested = []
    monkeypatch.setattr(
        merge_train,
        "open_pull_requests",
        lambda cfg, number=None: requested.append(number) or [],
    )
    assert main(["merge-train", "--pr", "19"]) == 0
    assert requested == [19]


def test_github_release_cli(repo, monkeypatch, capsys):
    result = github_release.ReleaseResult("v1.0.0", "abc", True, True)
    monkeypatch.setattr(github_release, "publish", lambda *a, **k: result)
    assert main(["github-release", "--target", "abc", "--version", "1.0.0"]) == 0
    assert json.loads(capsys.readouterr().out)["tag"] == "v1.0.0"

    def boom(*args, **kwargs):
        raise RuntimeError("tag conflict")

    monkeypatch.setattr(github_release, "publish", boom)
    assert main(["github-release", "--target", "abc"]) == 1
    assert "tag conflict" in capsys.readouterr().err


def test_check_prints_superseded_headers(repo, capsys):
    """A stale header must be NAMED, not folded into 'missing': the repair differs —
    replacement, not insertion — and the operator should know which they are running."""
    from vibey_gh.config import DEFAULT_SUPERSEDED_TEXTS

    (repo / "src" / "old.py").write_text(f"# {DEFAULT_SUPERSEDED_TEXTS[0]}\nx = 1\n")
    assert main(["check"]) == 1
    err = capsys.readouterr().err
    assert "carries a superseded fingerprint header" in err


def test_report_superseded_governance_range_triggers_article_v4(repo, capsys, monkeypatch):
    """A release range touching the constitution supersedes everything (Article V.4):
    the banner names the law, and the per-index switch plus the retention window are
    both overridden — the fixture's config never enables yank reporting at all."""
    from vibey_gh import yank

    base = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()
    (repo / "docs").mkdir()
    (repo / "docs" / "constitution.md").write_text("amended\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-qm", "ratify"], cwd=repo, capture_output=True, check=True)
    monkeypatch.setattr(
        yank, "released_versions", lambda index, project, timeout=30: ["1.0.0", "1.1.0", "1.2.0"]
    )
    assert (
        main(
            [
                "report-superseded",
                "--index",
                "pypi",
                "--project",
                "pkg",
                "--version",
                "1.2.0",
                "--governance-since",
                base,
            ]
        )
        == 0
    )
    out = capsys.readouterr().out
    assert "RATIFIED GOVERNANCE CHANGE" in out
    assert "1.1.0" in out and "1.0.0" in out
    assert "1.2.0" not in out.split("superseded by")[-1].split("Yank at")[0].replace(
        "1.2.0:", ""
    )  # the published version is the subject line, never a listed target


def test_report_superseded_unreadable_governance_range_is_loud_never_fatal(repo, capsys):
    """An unreadable range must not silently waive Article V.4 — and must not fail the
    release either: the publish already happened."""
    assert (
        main(
            [
                "report-superseded",
                "--index",
                "pypi",
                "--project",
                "pkg",
                "--version",
                "1.2.0",
                "--governance-since",
                "no-such-ref",
            ]
        )
        == 0
    )
    err = capsys.readouterr().err
    assert "could not read the governance range" in err
    assert "Article V.4 was NOT evaluated" in err


def test_failover_cli_runs_once_with_explicit_paths(repo, capsys, tmp_path, monkeypatch):
    assert (
        main(
            [
                "failover",
                "--once",
                "--config",
                str(tmp_path / "missing.toml"),
                "--state",
                str(tmp_path / "state.json"),
            ]
        )
        == 0
    )
    assert "disabled" in capsys.readouterr().out
    # Default paths resolve under HOME; point HOME at the sandbox and cover them too.
    monkeypatch.setenv("HOME", str(tmp_path))
    assert main(["failover", "--once"]) == 0
    assert "disabled" in capsys.readouterr().out
