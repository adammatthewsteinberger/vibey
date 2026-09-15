# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Policy, persistence, and privileged-workflow tests for PR automation."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from vibey_gh import pr_automation as pa
from vibey_gh.config import (
    GhConfig,
    PrAutomationConfig,
    PrAutomationObservabilityConfig,
    load_config,
)
from vibey_gh.install import WORKFLOWS, installation_notices, render_workflow


def cfg(tmp_path: Path, **automation) -> GhConfig:
    return GhConfig(
        root=tmp_path,
        owner="owner",
        trusted_authors=("trusted[bot]",),
        pr_automation=PrAutomationConfig(**automation),
    )


def pr(**changes):
    value = {
        "number": 12,
        "title": "change",
        "state": "OPEN",
        "isDraft": False,
        "mergeable": "MERGEABLE",
        "reviewDecision": "",
        "headRefOid": "abc",
        "headRefName": "topic",
        "baseRefName": "develop",
        "author": {"login": "owner"},
        "labels": [],
        "comments": [],
        "statusCheckRollup": [],
    }
    value.update(changes)
    return value


def check(name="CI", status="COMPLETED", conclusion="SUCCESS", **extra):
    return {"name": name, "status": status, "conclusion": conclusion, **extra}


@pytest.mark.parametrize(
    "kwargs,match",
    [
        ({"scan_workflows": ()}, "must not be empty"),
        ({"max_repair_attempts": 0}, "between 1 and 10"),
        ({"max_repair_attempts": 11}, "between 1 and 10"),
        ({"model": "  "}, "model must not be empty"),
        ({"scan_workflows": ("CI", "")}, "entries must be non-empty"),
        ({"ignored_checks": ("x", "x")}, "entries must be unique"),
    ],
)
def test_config_validation(kwargs, match):
    with pytest.raises(ValueError, match=match):
        PrAutomationConfig(**kwargs)


def test_config_parses_public_surface(tmp_path):
    (tmp_path / ".vibey-gh.toml").write_text("""[pr_automation]
enabled = false
scan_workflows = []
ignored_checks = ["custom"]
max_repair_attempts = 7
model = "model-x"
review_untrusted_authors = false
repair_untrusted_authors = false
replace_fork_prs = false
retain_schedule_backstop = false

[pr_automation.observability]
sanitized_progress = false
archive_execution_file = false
allow_private_full_output = true
""")
    value = load_config(tmp_path).pr_automation
    assert value == PrAutomationConfig(
        enabled=False,
        scan_workflows=(),
        ignored_checks=("custom",),
        max_repair_attempts=7,
        model="model-x",
        review_untrusted_authors=False,
        repair_untrusted_authors=False,
        replace_fork_prs=False,
        retain_schedule_backstop=False,
        observability=PrAutomationObservabilityConfig(
            sanitized_progress=False,
            archive_execution_file=False,
            allow_private_full_output=True,
        ),
    )


def test_rendered_workflow_uses_config_and_is_valid_yaml_shape(tmp_path):
    source = Path(pa.__file__).parent / "templates/workflows/pr-automation.yml"
    rendered = render_workflow(
        source,
        cfg(
            tmp_path,
            scan_workflows=("CI: strict", "Docs"),
            model="chosen-model",
            retain_schedule_backstop=False,
            observability=PrAutomationObservabilityConfig(
                sanitized_progress=False,
                archive_execution_file=False,
                allow_private_full_output=True,
            ),
        ),
    )
    assert 'workflows: ["CI: strict", "Docs"]' in rendered
    assert "--model chosen-model" in rendered
    assert "schedule backstop disabled" in rendered
    assert "track_progress: ${{ false &&" in rendered
    assert "github.event_name == 'pull_request'" in rendered
    assert (
        "github.event_name == 'workflow_dispatch'"
        not in rendered.split("track_progress:", 1)[1].splitlines()[0]
    )
    assert "&& true }}" in rendered
    assert "execution_file != '' && false" in rendered
    assert "__VIBEY_GH_" not in rendered

    intake = source.with_name("branch-intake.yml")
    rendered_intake = render_workflow(intake, cfg(tmp_path))
    assert "- develop" in rendered_intake
    assert "- main" in rendered_intake
    assert "__VIBEY_GH_" not in rendered_intake


def test_installation_notices_report_missing_secrets(monkeypatch):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess([], 0, '[{"name":"ANTHROPIC_API_KEY"}]', ""),
    )
    notices = installation_notices()
    assert any("AUTOMERGE_TOKEN" in item for item in notices)
    assert not any("ANTHROPIC_API_KEY" in item for item in notices)
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: subprocess.CompletedProcess([], 0, "not-json", "")
    )
    assert any("ANTHROPIC_API_KEY" in item for item in installation_notices())


@pytest.mark.parametrize(
    "changes,state,reason",
    [
        ({"headRefOid": "new"}, "blocked", "stale event"),
        ({"state": "CLOSED"}, "blocked", "not open"),
        ({"isDraft": True}, "pending", "draft awaiting a stable head"),
        ({"mergeable": "CONFLICTING"}, "conflict", "conflicts"),
        ({"reviewDecision": "CHANGES_REQUESTED"}, "blocked", "requested changes"),
        ({"labels": [pa.BLOCKED_LABEL]}, "blocked", "operator"),
        ({"labels": [{"name": pa.EXHAUSTED_LABEL}]}, "blocked", "exhausted"),
        (
            {"statusCheckRollup": [check(status="IN_PROGRESS", conclusion=None)]},
            "pending",
            "running",
        ),
        ({"statusCheckRollup": [check(conclusion="CANCELLED")]}, "blocked", "rerun"),
        ({"statusCheckRollup": [check(conclusion="FAILURE")]}, "repair", "failing"),
    ],
)
def test_evaluation_states(tmp_path, changes, state, reason):
    result = pa.evaluate(pr(**changes), cfg(tmp_path), expected_sha="abc")
    assert result.state == state
    assert reason in result.reason
    assert json.loads(result.to_json())["state"] == state


def test_evaluation_ignores_own_checks_and_accepts_context_shape(tmp_path):
    result = pa.evaluate(
        pr(
            statusCheckRollup=[
                check("PR automation / gate", conclusion="FAILURE"),
                check("gate", conclusion="FAILURE"),
                {"context": "legacy", "conclusion": "NEUTRAL", "targetUrl": "u"},
                {"name": "skip", "conclusion": "SKIPPED", "detailsUrl": "v"},
            ]
        ),
        cfg(tmp_path),
        expected_sha="abc",
    )
    # Reaching the review stage is what proves the rollup was read correctly: the two own
    # checks were ignored and the legacy `context` entry counted as a real passing scan.
    assert result.state == "review"


def test_a_conflicted_draft_is_resolved_rather_than_stranded(tmp_path):
    """The deadlock: `ready_draft` will not promote a conflicted draft *because* it
    conflicts, and conflict resolution never ran *because* it was a draft. Every
    branch-intake and issue-solution pull request starts as a draft, so this stranded all
    of them.
    """
    config = cfg(tmp_path)
    conflicted = pr(isDraft=True, mergeable="CONFLICTING")
    decision = pa.evaluate(conflicted, config, expected_sha="abc")
    assert decision.state == "conflict"
    assert decision.repair_attempt == 1

    # A fork draft still stays untouched: its conflict path closes the contributor's PR.
    fork = pr(isDraft=True, mergeable="CONFLICTING", isCrossRepository=True)
    assert pa.evaluate(fork, config, expected_sha="abc").state == "pending"
    # Once that fork PR is ready for review, the ordinary replacement path applies again.
    ready_fork = pr(mergeable="CONFLICTING", isCrossRepository=True)
    assert pa.evaluate(ready_fork, config, expected_sha="abc").state == "conflict"

    # An ordinary draft with no conflict is still nonterminal.
    assert pa.evaluate(pr(isDraft=True), config, expected_sha="abc").state == "pending"

    # Operator control still outranks conflict resolution for a draft.
    blocked = pr(isDraft=True, mergeable="CONFLICTING", labels=[{"name": pa.BLOCKED_LABEL}])
    assert pa.evaluate(blocked, config, expected_sha="abc").state == "blocked"
    spent = pa.AutomationState("abc", "abc", attempts=3)
    exhausted = pa.evaluate(conflicted, config, expected_sha="abc", stored=spent)
    assert exhausted.state == "blocked"
    assert "conflict resolution budget is exhausted" in exhausted.reason


def test_an_outside_author_can_never_steer_automation_at_a_permanent_branch(tmp_path):
    """GitHub already refuses them write access; this is the defence behind that.

    Both shapes are terminal, so no review, repair, conflict resolution, or gate runs —
    automation simply never acts on a pull request from an outside author that points at
    a permanent branch from either end.
    """
    config = cfg(tmp_path)
    outsider = {"login": "stranger"}

    for head in ("develop", "main", config.integration_branch, config.release_branch):
        decision = pa.evaluate(
            pr(author=outsider, headRefName=head, statusCheckRollup=[check()]),
            config,
            expected_sha="abc",
        )
        assert decision.state == "blocked"
        assert "may not propose from" in decision.reason

    for base in ("main", config.release_branch):
        decision = pa.evaluate(
            pr(author=outsider, baseRefName=base, statusCheckRollup=[check()]),
            config,
            expected_sha="abc",
        )
        assert decision.state == "blocked"
        assert "may not target" in decision.reason

    # A trusted author still promotes normally: the promotion PR's head IS the
    # integration branch, and blocking that would stop every release.
    promotion = pr(headRefName="develop", baseRefName="main", statusCheckRollup=[check()])
    assert pa.evaluate(promotion, config, expected_sha="abc").state != "blocked"
    # And an outside author's ordinary contribution is unaffected.
    ordinary = pr(author=outsider, headRefName="feature/x", statusCheckRollup=[check()])
    assert pa.evaluate(ordinary, config, expected_sha="abc").state != "blocked"


def test_the_review_loop_is_bounded_for_a_trusted_author_too(tmp_path):
    """The workflow reviews every author, so every author's review loop needs a budget.

    A trusted author previously fell straight through to `ready`, leaving the
    review-to-repair cycle in the workflow with nothing bounding it at all.
    """
    config = cfg(tmp_path, max_repair_attempts=2)
    green = pr(statusCheckRollup=[check()])
    assert pa._trusted(green, config), "fixture must be a trusted author for this test"

    below = pa.AutomationState("abc", "abc", attempts=1)
    assert pa.evaluate(green, config, expected_sha="abc", stored=below).state == "review"

    verdict = pa.AutomationState("abc", "abc", attempts=1, review_sha="abc", review_passed=False)
    findings = pa.evaluate(green, config, expected_sha="abc", stored=verdict)
    assert findings.state == "repair" and findings.repair_attempt == 2

    # A head that has never been reviewed always gets one, even with the budget spent: a
    # repair that already fixed every finding must not be escalated on a superseded verdict
    # from the head it replaced (issue #161). Dispatching the review costs no attempt.
    spent_but_unreviewed = pa.AutomationState("abc", "abc", attempts=2)
    fresh_review = pa.evaluate(green, config, expected_sha="abc", stored=spent_but_unreviewed)
    assert fresh_review.state == "review"

    # Only a CURRENT review's own actionable findings, with the budget spent, is exhaustion.
    spent = pa.AutomationState("abc", "abc", attempts=2, review_sha="abc", review_passed=False)
    blocked = pa.evaluate(green, config, expected_sha="abc", stored=spent)
    assert blocked.state == "blocked"
    assert "review repair budget is exhausted" in blocked.reason

    passed = pa.AutomationState("abc", "abc", attempts=1, review_sha="abc", review_passed=True)
    assert pa.evaluate(green, config, expected_sha="abc", stored=passed).state == "ready"

    # Even with the budget fully spent, a current, passing review still reaches ready.
    spent_and_passed = pa.AutomationState(
        "abc", "abc", attempts=2, review_sha="abc", review_passed=True
    )
    assert pa.evaluate(green, config, expected_sha="abc", stored=spent_and_passed).state == "ready"


def test_an_outside_author_with_review_disabled_still_reaches_ready(tmp_path):
    config = cfg(tmp_path, review_untrusted_authors=False)
    green = pr(author={"login": "stranger"}, statusCheckRollup=[check()])
    assert pa.evaluate(green, config, expected_sha="abc", stored=None).state == "ready"


def test_a_spent_repair_budget_can_be_refilled_a_bounded_number_of_times(monkeypatch, tmp_path):
    """A budget that never refills turns a transient outage into a permanent stop; one
    that refills forever is no budget. So the refill is itself budgeted."""
    from vibey_gh.config import BranchSyncConfig

    config = GhConfig(root=tmp_path, owner="owner", branch_sync=BranchSyncConfig(max_self_heals=2))
    state = pa.AutomationState("abc", "abc", attempts=3)
    current = pr(labels=[{"name": pa.EXHAUSTED_LABEL}], comments=[pa.state_body(state, "x")])
    monkeypatch.setattr(pa, "fetch_pr", lambda number: current)
    monkeypatch.setenv("GH_REPO", "o/r")
    saved: list = []
    monkeypatch.setattr(pa, "upsert_state", lambda *a: saved.append(a))
    calls: list = []
    monkeypatch.setattr(subprocess, "run", lambda args, **k: calls.append(args) or completed())

    first = pa.self_heal(12, config)
    assert first["healed"] and first["heal"] == 1
    healed = saved[0][1]
    assert healed.attempts == 0 and healed.heals == 1
    assert healed.review_sha is None and healed.review_passed is None
    assert [h["kind"] for h in healed.history][-1] == "self-heal"
    assert any("--remove-label" in c for c in calls)

    # The refill count rides in the same durable state, so it survives to bound the next.
    spent = pa.AutomationState("abc", "abc", attempts=3, heals=2)
    monkeypatch.setattr(
        pa,
        "fetch_pr",
        lambda number: pr(
            labels=[{"name": pa.EXHAUSTED_LABEL}], comments=[pa.state_body(spent, "x")]
        ),
    )
    refused = pa.self_heal(12, config)
    assert not refused["healed"] and "budget of 2 is spent" in refused["reason"]

    monkeypatch.setattr(pa, "fetch_pr", lambda number: pr())
    assert pa.self_heal(12, config) == {"pr": 12, "healed": False, "reason": "not exhausted"}


def test_self_heal_starts_a_lineage_when_no_state_exists(monkeypatch, tmp_path):
    monkeypatch.setenv("GH_REPO", "o/r")
    monkeypatch.setattr(pa, "fetch_pr", lambda n: pr(labels=[{"name": pa.EXHAUSTED_LABEL}]))
    saved: list = []
    monkeypatch.setattr(pa, "upsert_state", lambda *a: saved.append(a))
    monkeypatch.setattr(subprocess, "run", lambda args, **k: completed())
    assert pa.self_heal(12, GhConfig(root=tmp_path))["healed"]
    assert saved[0][1].lineage_sha == "abc"


def test_exhausted_pull_requests_are_listed_by_label(monkeypatch, tmp_path):
    monkeypatch.setenv("GH_REPO", "o/r")
    captured: list = []
    monkeypatch.setattr(
        pa.github_state, "gh_json", lambda *a: captured.append(a) or [{"number": 4}, {"number": 9}]
    )
    assert pa.exhausted_pull_requests(GhConfig(root=tmp_path)) == [4, 9]
    assert pa.EXHAUSTED_LABEL in captured[0]
    monkeypatch.setattr(pa.github_state, "gh_json", lambda *a: None)
    assert pa.exhausted_pull_requests(GhConfig(root=tmp_path)) == []


def test_a_human_push_persists_a_fresh_attempt_budget():
    """`evaluate` always computed the lineage reset; only the record never applied it."""
    spent = pa.AutomationState(lineage_sha="old", current_sha="old", attempts=3)
    pushed = pr(headRefOid="new", comments=[pa.state_body(spent, "x")])
    fresh = pa.updated_state(pushed, {"head_sha": "new", "pass": True}, kind="review")
    assert fresh.attempts == 0
    assert fresh.lineage_sha == "new" and fresh.current_sha == "new"
    assert [item["kind"] for item in fresh.history] == ["review"]

    # A bot repair advances the head as it records, so it must NOT look like a new
    # lineage — otherwise the budget would reset on every repair and bound nothing.
    carried = pa.AutomationState(lineage_sha="new", current_sha="new", attempts=1)
    repaired = pr(headRefOid="newer", comments=[pa.state_body(carried, "x")])
    after = pa.updated_state(repaired, {"head_sha": "newer", "fixable": True}, kind="repair")
    assert after.attempts == 2 and after.lineage_sha == "new" and after.current_sha == "newer"

    # And a review recorded for the head that repair just produced continues the lineage.
    again = pr(headRefOid="newer", comments=[pa.state_body(after, "x")])
    continued = pa.updated_state(again, {"head_sha": "newer", "pass": False}, kind="review")
    assert continued.attempts == 2 and continued.lineage_sha == "new"


def test_evaluation_waits_when_no_scan_result_exists(tmp_path):
    result = pa.evaluate(pr(), cfg(tmp_path), expected_sha="abc")
    assert result.state == "pending" and "no current-head" in result.reason


def test_retry_and_untrusted_review_policy(tmp_path):
    failed = pr(author={"login": "outsider"}, statusCheckRollup=[check(conclusion="FAILURE")])
    state = pa.AutomationState("abc", "abc", attempts=3)
    assert pa.evaluate(failed, cfg(tmp_path), expected_sha="abc", stored=state).state == "blocked"
    assert (
        pa.evaluate(failed, cfg(tmp_path, repair_untrusted_authors=False), expected_sha="abc").state
        == "blocked"
    )

    green = pr(author={"login": "outsider"}, statusCheckRollup=[check()])
    assert pa.evaluate(green, cfg(tmp_path), expected_sha="abc").state == "review"
    findings = pa.AutomationState("abc", "abc", review_sha="abc", review_passed=False)
    assert pa.evaluate(green, cfg(tmp_path), expected_sha="abc", stored=findings).state == "repair"
    findings.attempts = 3
    assert pa.evaluate(green, cfg(tmp_path), expected_sha="abc", stored=findings).state == "blocked"
    passed = pa.AutomationState("abc", "abc", review_sha="abc", review_passed=True)
    assert pa.evaluate(green, cfg(tmp_path), expected_sha="abc", stored=passed).state == "ready"
    assert (
        pa.evaluate(green, cfg(tmp_path, review_untrusted_authors=False), expected_sha="abc").state
        == "ready"
    )


def test_conflict_resolution_uses_and_enforces_repair_budget(tmp_path):
    conflicting = pr(mergeable="CONFLICTING", statusCheckRollup=[check()])
    first = pa.evaluate(conflicting, cfg(tmp_path), expected_sha="abc")
    assert first.state == "conflict"
    assert first.repair_attempt == 1
    assert first.failed_checks == ("Merge conflict with develop",)
    exhausted = pa.AutomationState("abc", "abc", attempts=3)
    result = pa.evaluate(conflicting, cfg(tmp_path), expected_sha="abc", stored=exhausted)
    assert result.state == "blocked"
    assert "conflict resolution budget" in result.reason


def test_operator_block_takes_precedence_over_conflict(tmp_path):
    blocked_and_conflicting = pr(
        mergeable="CONFLICTING",
        labels=[pa.BLOCKED_LABEL],
        statusCheckRollup=[check()],
    )
    result = pa.evaluate(blocked_and_conflicting, cfg(tmp_path), expected_sha="abc")
    assert result.state == "blocked"
    assert "operator" in result.reason


def test_external_repair_is_untrusted_even_for_owner(tmp_path):
    result = pa.evaluate(
        pr(labels=[pa.EXTERNAL_REPAIR_LABEL], statusCheckRollup=[check()]),
        cfg(tmp_path),
        expected_sha="abc",
    )
    assert result.trusted is False and result.state == "review"


@pytest.mark.parametrize("branch", ("", ":main", "topic:other", "--delete"))
def test_repair_refspec_rejects_deletion_or_option_syntax(branch):
    with pytest.raises(ValueError, match="unsafe repair branch"):
        pa.repair_refspec(branch)


@pytest.mark.parametrize("branch", ("topic", "develop", "main"))
def test_repair_refspec_allows_forward_updates_including_protected_branches(branch):
    assert pa.repair_refspec(branch) == f"HEAD:refs/heads/{branch}"


def test_state_marker_round_trip_and_malformed_comments():
    assert pa.parse_state(["ordinary", "<!-- vibey-gh-pr-automation:{bad} -->"]) is None
    # A well-formed payload from an older or foreign schema is not usable state.
    assert pa.parse_state(['<!-- vibey-gh-pr-automation:{"attempts":1} -->']) is None
    state = pa.AutomationState("a", "b", 2, history=[{"kind": "repair"}])
    body = pa.state_body(state, " summary ")
    assert pa.parse_state([{"body": body}]) == state
    assert "summary" in body


def test_state_updates_review_repair_and_rejects_unknown_kind():
    review = pa.updated_state(pr(), {"head_sha": "abc", "pass": True}, kind="review")
    assert review.review_sha == "abc" and review.review_passed is True
    repair = pa.updated_state(
        pr(comments=[pa.state_body(review, "x")]),
        {"head_sha": "def", "fixable": True},
        kind="repair",
    )
    assert repair.attempts == 1 and repair.current_sha == "def" and repair.review_sha is None
    no_charge = pa.updated_state(pr(), {"fixable": False}, kind="repair")
    assert no_charge.attempts == 0
    with pytest.raises(ValueError, match="unknown record kind"):
        pa.updated_state(pr(), {}, kind="other")


def completed(code=0, out="", err=""):
    return subprocess.CompletedProcess([], code, out, err)


def test_github_helpers_and_state_persistence(monkeypatch, tmp_path):
    calls = []

    def run(args, **kwargs):
        calls.append(args)
        if args[:3] == ["gh", "repo", "view"]:
            return completed(out='{"nameWithOwner":"o/r"}')
        return completed(out="{}")

    monkeypatch.setattr(subprocess, "run", run)
    assert pa._gh_json("repo", "view") == {"nameWithOwner": "o/r"}
    state = pa.AutomationState("a", "a")
    pa.upsert_state(1, state, "new", [])
    pa.upsert_state(1, state, "new after ordinary comment", [{"body": "hello"}])
    pa.upsert_state(1, state, "edit", [{"body": pa.state_body(state, "x"), "databaseId": 9}])
    pa.upsert_state(
        1,
        state,
        "graphql edit",
        [{"body": pa.state_body(state, "x"), "databaseId": None, "id": "IC_node"}],
    )
    assert any(command[:3] == ["gh", "pr", "comment"] for command in calls)
    assert any("issues/comments/9" in " ".join(command) for command in calls)
    assert any(command[:3] == ["gh", "api", "graphql"] for command in calls)
    with pytest.raises(RuntimeError, match="comment has no ID"):
        pa.upsert_state(1, state, "bad", [{"body": pa.state_body(state, "x")}])

    monkeypatch.setenv("GH_REPO", "explicit/repository")
    calls.clear()
    pa.upsert_state(2, state, "explicit", [])
    assert "explicit/repository" in calls[0]

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: completed(1, err="boom"))
    with pytest.raises(RuntimeError, match="gh api"):
        pa._gh_json("api", "x")
    with pytest.raises(RuntimeError, match="persist"):
        pa.upsert_state(1, state, "x", [])


def test_trust_without_an_owner(tmp_path):
    config = GhConfig(root=tmp_path, owner="", trusted_authors=("trusted",))
    assert pa._trusted(pr(author={"login": "trusted"}), config)


def test_fetch_evaluate_record_and_labels(monkeypatch, tmp_path):
    monkeypatch.setattr(pa, "_gh_json", lambda *a: pr())
    assert pa.fetch_pr(12)["number"] == 12
    assert pa.evaluate_pr(12, "abc", cfg(tmp_path)).state == "pending"
    captured = []
    monkeypatch.setattr(pa, "upsert_state", lambda *a: captured.append(a))
    state = pa.record(12, {"head_sha": "abc", "pass": True, "summary": "ok"}, "review")
    assert state.review_passed and captured
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda args, **kw: calls.append(args) or completed())
    pa.ensure_labels()
    assert len(calls) == 4 and all(call[:3] == ["gh", "label", "create"] for call in calls)


@pytest.mark.parametrize(
    "changes,reason",
    [
        ({"headRefOid": "new"}, "stale head"),
        ({"state": "CLOSED", "isDraft": True}, "not an open draft"),
        ({"isDraft": False}, "not an open draft"),
        ({"isDraft": True, "isCrossRepository": True}, "fork drafts"),
        ({"isDraft": True}, "no current-head"),
    ],
)
def test_ready_draft_unstable_states_are_noops(monkeypatch, tmp_path, changes, reason):
    monkeypatch.setattr(pa, "fetch_pr", lambda number: pr(**changes))
    result = pa.ready_draft(12, "abc", cfg(tmp_path))
    assert result["promoted"] is False
    assert reason in result["reason"]


@pytest.mark.parametrize("author", ("owner", "outsider"))
def test_ready_draft_promotes_green_trusted_or_reviewable_head(monkeypatch, tmp_path, author):
    draft = pr(
        isDraft=True,
        isCrossRepository=False,
        author={"login": author},
        statusCheckRollup=[check()],
    )
    monkeypatch.setattr(pa, "fetch_pr", lambda number: draft)
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda args, **kwargs: calls.append(args) or completed())
    assert pa.ready_draft(12, "abc", cfg(tmp_path))["promoted"] is True
    assert calls == [["gh", "pr", "ready", "12"]]


def test_ready_draft_reports_github_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(
        pa,
        "fetch_pr",
        lambda number: pr(isDraft=True, isCrossRepository=False, statusCheckRollup=[check()]),
    )
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: completed(1, err="denied"))
    with pytest.raises(RuntimeError, match="could not mark PR ready"):
        pa.ready_draft(12, "abc", cfg(tmp_path))


def test_mirror_fork_success_and_failures(monkeypatch, tmp_path):
    fork = pr(
        author={"login": "alice"},
        headRepositoryOwner={"login": "alice"},
        headRepository={"name": "fork"},
    )
    monkeypatch.setattr(pa, "fetch_pr", lambda n: fork)
    calls = []

    def success(args, **kwargs):
        calls.append(args)
        if args[:3] == ["gh", "pr", "create"]:
            return completed(out="https://github.com/o/r/pull/44\n")
        return completed()

    monkeypatch.setattr(subprocess, "run", success)
    result = pa.mirror_fork(12, cfg(tmp_path))
    assert result["replacement_pr"] == 44
    assert any(command[:3] == ["gh", "pr", "close"] for command in calls)

    monkeypatch.setattr(pa, "fetch_pr", lambda n: pr(headRepositoryOwner={}, headRepository={}))
    with pytest.raises(RuntimeError, match="does not expose"):
        pa.mirror_fork(12, cfg(tmp_path))

    monkeypatch.setattr(pa, "fetch_pr", lambda n: fork)
    for failure, message in (("fetch", "fetch fork"), ("push", "publish"), ("create", "open")):

        def fail(args, failure=failure, **kwargs):
            joined = " ".join(args)
            if failure in joined or (failure == "create" and args[:3] == ["gh", "pr", "create"]):
                return completed(1, err="no")
            return completed()

        monkeypatch.setattr(subprocess, "run", fail)
        with pytest.raises(RuntimeError, match=message):
            pa.mirror_fork(12, cfg(tmp_path))


def _workflow(tmp_path: Path, filename: str, name: str, body: str) -> None:
    directory = tmp_path / ".github" / "workflows"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / filename).write_text(f"name: {name}\n\non:\n{body}\n")


def test_scan_workflows_check_is_a_noop_when_disabled_or_absent(tmp_path):
    assert pa.check_scan_workflows(cfg(tmp_path, enabled=False)).ok
    assert pa.check_scan_workflows(cfg(tmp_path, scan_workflows=("Docs",))).ok


def test_scan_workflows_check_ignores_a_name_absent_from_the_repository(tmp_path):
    _workflow(tmp_path, "ci.yml", "CI", "  push:\n")
    report = pa.check_scan_workflows(cfg(tmp_path, scan_workflows=("Docs",)))
    assert report.ok


@pytest.mark.parametrize("trigger", ["pull_request", "pull_request_target"])
def test_scan_workflows_check_accepts_either_pull_request_spelling(tmp_path, trigger):
    _workflow(tmp_path, "docs.yml", "Docs", f"  {trigger}:\n  push:\n")
    report = pa.check_scan_workflows(cfg(tmp_path, scan_workflows=("Docs",)))
    assert report.ok


def test_scan_workflows_check_fails_a_push_only_workflow_with_a_clear_message(tmp_path):
    _workflow(tmp_path, "docs.yml", "Docs", '  push:\n    branches: ["main"]\n')
    report = pa.check_scan_workflows(cfg(tmp_path, scan_workflows=("Docs",)))
    assert not report.ok
    assert len(report.problems) == 1
    problem = report.problems[0]
    assert "'Docs'" in problem
    assert "docs.yml" in problem
    assert "pull_request" in problem and "pull_request_target" in problem


def test_scan_workflows_check_reads_inline_and_bare_on_triggers(tmp_path):
    directory = tmp_path / ".github" / "workflows"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "push-only.yml").write_text("name: Push only\non: push\n")
    (directory / "bracketed.yml").write_text("name: Bracketed\non: [push, pull_request]\n")
    report = pa.check_scan_workflows(cfg(tmp_path, scan_workflows=("Push only", "Bracketed")))
    assert len(report.problems) == 1
    assert "'Push only'" in report.problems[0]


def test_scan_workflows_check_ignores_a_workflow_file_with_no_name_field(tmp_path):
    directory = tmp_path / ".github" / "workflows"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "nameless.yml").write_text("on:\n  push:\n")
    report = pa.check_scan_workflows(cfg(tmp_path, scan_workflows=("Docs",)))
    assert report.ok


def test_scan_workflows_check_ignores_a_non_key_line_at_trigger_indentation(tmp_path):
    _workflow(tmp_path, "weird.yml", "Weird", "  push:\n  - not-a-trigger\n")
    report = pa.check_scan_workflows(cfg(tmp_path, scan_workflows=("Weird",)))
    assert not report.ok
    assert "'Weird'" in report.problems[0]


def test_scan_workflows_check_stops_reading_triggers_at_the_next_top_level_key(tmp_path):
    body = "  pull_request:\npermissions:\n  contents: read\n"
    _workflow(tmp_path, "trailing.yml", "Trailing", body)
    report = pa.check_scan_workflows(cfg(tmp_path, scan_workflows=("Trailing",)))
    assert report.ok


def test_a_workflow_with_no_trigger_block_reports_no_triggers():
    """A malformed or trigger-less workflow must report nothing rather than guess.

    Reporting a trigger it does not have would let a workflow that can never fire for a
    pull request pass the check — which is the exact silent merge lockout this validation
    exists to prevent.
    """
    assert pa._workflow_triggers("name: CI\njobs:\n  build:\n    runs-on: ubuntu-latest\n") == set()
    assert pa._workflow_triggers("") == set()
    # And one that does declare them is still read correctly.
    assert pa._workflow_triggers("on:\n  pull_request:\n  push:\n") == {"pull_request", "push"}


def test_the_evaluation_never_waits_on_the_job_computing_it(tmp_path: Path):
    """The rollup counted `Evaluate current head`, which is running while it counts.

    That makes the state permanently "pending" from inside its own run. It survived only
    because a later run saw the earlier evaluate completed — so it bit the moment no later
    run was coming: a pull request sat blocked with every check green, nothing failing and
    nothing to rerun, waiting on the job that was doing the waiting.
    """
    rollup = [
        check(name="CI"),
        check(name="Evaluate current head", status="IN_PROGRESS", conclusion=None),
        check(name="PR automation / gate", status="IN_PROGRESS", conclusion=None),
    ]
    decision = pa.evaluate(pr(statusCheckRollup=rollup), cfg(tmp_path), expected_sha="abc")
    # The point is not which state it reaches but that it stops waiting on itself: the
    # rollup is complete, so evaluation proceeds instead of reporting its own job pending.
    assert decision.state != "pending", decision.reason
    assert not decision.pending_checks


def test_every_job_this_workflow_publishes_is_excluded_from_its_own_rollup():
    """Pinned against the template, so a job added later cannot start gating itself."""
    text = (WORKFLOWS / "pr-automation.yml").read_text(encoding="utf-8")
    published = {
        line.split("name:", 1)[1].strip()
        for line in text.splitlines()
        if line.startswith("    name:")
    }
    assert published, "no job names parsed out of pr-automation.yml"
    missing = sorted(job for job in published if job not in pa.OWN_CHECKS)
    assert not missing, f"these publish a check but are not excluded from the rollup: {missing}"


def test_a_gating_check_belongs_to_a_workflow_that_can_re_trigger_evaluation(tmp_path: Path):
    """`scan_workflows` is also the `workflow_run` trigger list, which is the trap.

    A workflow whose check gates but which is absent there can never announce that it
    finished. `Conventional Commits` was exactly that: its `enforce` check was counted,
    the last scan to complete fired the final evaluation, `enforce` finished after it, and
    nothing looked again.
    """
    from vibey_gh.config import DEFAULT_SCAN_WORKFLOWS

    assert "Conventional Commits" in DEFAULT_SCAN_WORKFLOWS
    rendered = render_workflow(WORKFLOWS / "pr-automation.yml", cfg(tmp_path))
    triggers = next(line for line in rendered.splitlines() if line.strip().startswith("workflows:"))
    for workflow in DEFAULT_SCAN_WORKFLOWS:
        assert workflow in triggers, f"{workflow} gates but cannot re-trigger evaluation"


def test_a_superseded_runs_cancelled_jobs_do_not_block_the_gate():
    """Concurrency cancelling a superseded run is ordinary, not exceptional.

    Its jobs stay in the rollup as CANCELLED beside the successful jobs of the run that
    replaced them — same head, same names, two verdicts. Counting both read as "cancelled
    or stale checks require a rerun" and left the pull request blocked with nothing wrong
    and nothing to do but rerun a workflow that had already succeeded. Seen on
    vibey-gh #114, #117 and vibey-skills #62.
    """
    rollup = [
        {
            "name": "enforce",
            "status": "COMPLETED",
            "conclusion": "CANCELLED",
            "startedAt": "2026-08-27T16:05:51Z",
        },
        {
            "name": "enforce",
            "status": "COMPLETED",
            "conclusion": "SUCCESS",
            "startedAt": "2026-08-27T16:12:10Z",
        },
    ]
    kept = pa.newest_per_name(rollup)
    assert len(kept) == 1
    assert kept[0]["conclusion"] == "SUCCESS"

    # Rollup order is not guaranteed, so the newest must win from either direction.
    kept = pa.newest_per_name(list(reversed(rollup)))
    assert len(kept) == 1
    assert kept[0]["conclusion"] == "SUCCESS"


def test_a_newer_failure_is_never_masked_by_an_older_success():
    """The dedupe keeps the NEWEST run, not the happiest one. A check that passed and then
    failed on a rerun must read as failing, or this would hide real breakage."""
    rollup = [
        {
            "name": "CI",
            "status": "COMPLETED",
            "conclusion": "SUCCESS",
            "startedAt": "2026-08-27T10:00:00Z",
        },
        {
            "name": "CI",
            "status": "COMPLETED",
            "conclusion": "FAILURE",
            "startedAt": "2026-08-27T11:00:00Z",
        },
    ]
    kept = pa.newest_per_name(rollup)
    assert len(kept) == 1
    assert kept[0]["conclusion"] == "FAILURE"


def test_dedupe_keeps_distinct_checks_and_tolerates_missing_timestamps():
    """Different names are different checks and all survive. An entry with no timestamp
    sorts oldest, so a real result always displaces a placeholder rather than the reverse."""
    rollup = [
        {"name": "CI", "status": "COMPLETED", "conclusion": "SUCCESS"},
        {"name": "Provenance", "status": "COMPLETED", "conclusion": "SUCCESS"},
        {
            "name": "CI",
            "status": "COMPLETED",
            "conclusion": "FAILURE",
            "startedAt": "2026-08-27T11:00:00Z",
        },
    ]
    kept = {c["name"]: c for c in pa.newest_per_name(rollup)}
    assert set(kept) == {"CI", "Provenance"}
    assert kept["CI"]["conclusion"] == "FAILURE"
