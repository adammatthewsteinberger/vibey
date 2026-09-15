# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Reconciling repository rulesets from `.vibey-gh.toml`.

The policy half — building a desired ruleset and comparing it against a fetched one — is
pure and has no I/O, so it is tested directly and exhaustively. The GitHub adapters are
tested the same way `vibey_gh.reconcile` tests them: `subprocess.run` monkeypatched to a
recorder, never a real network call.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

from vibey_gh import rulesets as rs
from vibey_gh.config import (
    DEFAULT_INTEGRATION_RULESET_CHECKS,
    DEFAULT_RELEASE_RULESET_CHECKS,
    GhConfig,
    RulesetConfig,
    RulesetsConfig,
    load_config,
)
from vibey_gh.install import render_workflow


def completed(code=0, out="", err=""):
    return subprocess.CompletedProcess([], code, out, err)


def policy(**changes) -> RulesetConfig:
    value = dict(required_checks=("CI", "Docs"), required_approvals=1)
    value.update(changes)
    return RulesetConfig(**value)


# ------------------------------------------------------------------------ configuration


@pytest.mark.parametrize("field", ["allow_force_pushes", "allow_deletions"])
def test_force_pushes_and_deletions_can_never_be_allowed(field):
    with pytest.raises(ValueError, match="must not be true for a permanent branch"):
        RulesetConfig(**{field: True})


@pytest.mark.parametrize("value", [-1, 7])
def test_required_approvals_is_bounded(value):
    with pytest.raises(ValueError, match="between 0 and 6"):
        RulesetConfig(required_approvals=value)


def test_required_checks_must_be_unique_and_nonempty():
    with pytest.raises(ValueError, match="unique"):
        RulesetConfig(required_checks=("CI", "CI"))
    with pytest.raises(ValueError, match="non-empty"):
        RulesetConfig(required_checks=("CI", " "))


@pytest.mark.parametrize("actor", ["nocolon", "Team:", ":5", "RepositoryRole:abc"])
def test_bypass_actors_must_be_type_colon_numeric_id(actor):
    with pytest.raises(ValueError, match="malformed"):
        RulesetConfig(bypass_actors=(actor,))


def test_an_empty_bypass_actor_is_rejected_as_nonempty_before_format():
    with pytest.raises(ValueError, match="non-empty"):
        RulesetConfig(bypass_actors=("",))


def test_a_well_formed_bypass_actor_is_accepted():
    cfg = RulesetConfig(bypass_actors=("RepositoryRole:5",))
    assert cfg.bypass_actors == ("RepositoryRole:5",)


def test_rulesets_are_enabled_and_defaulted_without_any_configuration(tmp_path):
    cfg = load_config(tmp_path)
    assert cfg.rulesets.enabled is True
    assert cfg.rulesets.integration.required_approvals == 0
    assert cfg.rulesets.release.required_approvals == 1
    assert "PR automation / gate" in cfg.rulesets.integration.required_checks
    assert cfg.rulesets.release.required_checks == (
        "Provenance",
        "Analyze Python",
        "Documentation contract",
    )


def template_check_names() -> set[str]:
    """Every check-run name the bundled workflow templates can produce.

    A check run is named for its job, except when the workflow is triggered by
    `workflow_run`, where GitHub prefixes it with the workflow's name — so both spellings
    count. Rendered first: every workflow name is configurable, so a raw template carries
    `__VIBEY_GH_WF_*__` where its name goes. Parsed with `re` rather than a YAML library
    because the rendered text still carries other placeholders and the test suite takes no
    new dependency.
    """
    names: set[str] = set()
    for path in sorted((Path(rs.__file__).parent / "templates" / "workflows").glob("*.yml")):
        text = render_workflow(path, GhConfig(root=Path(".")))
        workflow = re.search(r"(?m)^name: *(.+)$", text)
        workflow_name = workflow.group(1).strip().strip("\"'") if workflow else ""
        for job in re.findall(r"(?m)^    name: *(.+)$", text):
            job_name = job.strip().strip("\"'")
            names.add(job_name)
            names.add(f"{workflow_name} / {job_name}")
    return names


@pytest.mark.parametrize(
    "checks",
    [DEFAULT_INTEGRATION_RULESET_CHECKS, DEFAULT_RELEASE_RULESET_CHECKS],
    ids=["integration", "release"],
)
def test_every_default_required_check_is_a_job_a_bundled_template_renders(checks):
    """The invariant the original defaults broke, pinned so it cannot break again.

    A required status check names a *check run*, not a workflow. The defaults were once
    built from `DEFAULT_SCAN_WORKFLOWS`, so they required "CI", "Docs", and "API drift
    (Cloud Agents OpenAPI)" — workflow names with no job behind them. Nothing reported
    them, and every merge to the protected branch was refused with no way through, since a
    ruleset never exempts administrators on its own. Overlap with a workflow name is fine
    where a job genuinely shares it, which is why this checks membership rather than
    disjointness: "Provenance" is both, and legitimately so.
    """
    renderable = template_check_names()
    assert renderable, "no job names parsed out of the bundled templates"
    assert set(checks) <= renderable, f"cannot ever report: {sorted(set(checks) - renderable)}"


def test_the_default_bypass_keeps_a_stuck_branch_recoverable(tmp_path):
    """Without this, a check that stops reporting is unrecoverable except by hand.

    Classic branch protection had an "include administrators" toggle that defaulted to
    off; a ruleset has no equivalent, so an empty bypass list means nobody — owner
    included — can merge past a check that will never arrive.
    """
    assert RulesetConfig().bypass_actors == ("RepositoryRole:5",)
    cfg = load_config(tmp_path)
    assert cfg.rulesets.integration.bypass_actors == ("RepositoryRole:5",)
    assert cfg.rulesets.release.bypass_actors == ("RepositoryRole:5",)


def test_a_toml_rulesets_block_overrides_the_defaults(tmp_path):
    (tmp_path / ".vibey-gh.toml").write_text(
        "[rulesets]\n"
        "enabled = false\n"
        "[rulesets.integration]\n"
        'required_checks = ["CI"]\n'
        "required_approvals = 2\n"
        'bypass_actors = ["RepositoryRole:5"]\n'
        "[rulesets.release]\n"
        "require_signed_commits = true\n"
    )
    cfg = load_config(tmp_path)
    assert cfg.rulesets.enabled is False
    assert cfg.rulesets.integration.required_checks == ("CI",)
    assert cfg.rulesets.integration.required_approvals == 2
    assert cfg.rulesets.integration.bypass_actors == ("RepositoryRole:5",)
    assert cfg.rulesets.release.require_signed_commits is True
    # An overridden section still keeps every other field's own default.
    assert cfg.rulesets.release.required_approvals == 1


def test_loading_rejects_a_configured_deletion_or_force_push_allowance(tmp_path):
    (tmp_path / ".vibey-gh.toml").write_text("[rulesets.release]\nallow_deletions = true\n")
    with pytest.raises(ValueError, match="allow_deletions must not be true"):
        load_config(tmp_path)


# -------------------------------------------------------------------------------- policy


def test_desired_rules_always_blocks_deletion_and_force_pushes():
    rules = rs.desired_rules(policy())
    types = [rule["type"] for rule in rules]
    assert rs.DELETION in types and rs.NON_FAST_FORWARD in types


def test_linear_history_and_signatures_are_each_independently_optional():
    both_off = rs.desired_rules(policy(require_linear_history=False, require_signed_commits=False))
    assert rs.LINEAR_HISTORY not in [r["type"] for r in both_off]
    assert rs.SIGNATURES not in [r["type"] for r in both_off]

    both_on = rs.desired_rules(policy(require_linear_history=True, require_signed_commits=True))
    types = [r["type"] for r in both_on]
    assert rs.LINEAR_HISTORY in types and rs.SIGNATURES in types


def test_pull_request_rule_carries_approvals_and_conversation_resolution():
    both = policy(required_approvals=0, require_conversation_resolution=True)
    rule = next(r for r in rs.desired_rules(both) if r["type"] == rs.PULL_REQUEST)
    assert rule["parameters"]["required_approving_review_count"] == 0
    assert rule["parameters"]["required_review_thread_resolution"] is True


def test_status_checks_rule_is_omitted_when_no_checks_are_declared():
    rules = rs.desired_rules(policy(required_checks=()))
    assert rs.STATUS_CHECKS not in [r["type"] for r in rules]


def test_status_checks_rule_carries_every_configured_context():
    rules = rs.desired_rules(policy(required_checks=("CI", "Docs")))
    rule = next(r for r in rules if r["type"] == rs.STATUS_CHECKS)
    assert rule["parameters"]["required_status_checks"] == [
        {"context": "CI"},
        {"context": "Docs"},
    ]
    assert rule["parameters"]["strict_required_status_checks_policy"] is True


def test_bypass_actor_payload_splits_type_and_numeric_id():
    payload = rs.bypass_actor_payload(("RepositoryRole:5", "Team:12"))
    assert payload == [
        {"actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "always"},
        {"actor_id": 12, "actor_type": "Team", "bypass_mode": "always"},
    ]


def test_build_ruleset_names_targets_and_conditions_the_payload():
    payload = rs.build_ruleset("develop", policy())
    assert payload["name"] == "vibey-gh: develop"
    assert payload["target"] == "branch"
    assert payload["enforcement"] == "active"
    assert payload["conditions"] == {"ref_name": {"include": ["refs/heads/develop"], "exclude": []}}


# ------------------------------------------------------------------------------ diffing


def test_a_missing_ruleset_is_always_reported_changed_with_no_unexpected_rules():
    desired = rs.build_ruleset("develop", policy())
    result = rs.diff_ruleset(desired, None)
    assert result.changed and result.unexpected_rules == ()
    assert result.payload == desired


def test_an_identical_existing_ruleset_reports_no_drift():
    desired = rs.build_ruleset("develop", policy())
    existing = {**desired, "id": 1}
    result = rs.diff_ruleset(desired, existing)
    assert not result.changed
    assert result.unexpected_rules == ()


def test_a_changed_rule_parameter_is_reported_as_drift():
    desired = rs.build_ruleset("develop", policy(required_approvals=1))
    existing = {**desired, "id": 1, "rules": rs.desired_rules(policy(required_approvals=0))}
    result = rs.diff_ruleset(desired, existing)
    assert result.changed


def test_an_unmentioned_existing_rule_is_preserved_and_reported_not_deleted():
    desired = rs.build_ruleset("develop", policy())
    extra_rule = {"type": "creation"}
    existing = {**desired, "id": 1, "rules": [*desired["rules"], extra_rule]}
    result = rs.diff_ruleset(desired, existing)
    assert not result.changed  # every declared rule already matches
    assert result.unexpected_rules == ("creation",)
    assert extra_rule in result.payload["rules"]
    # The desired rules are present too — nothing declared was dropped.
    for rule in desired["rules"]:
        assert rule in result.payload["rules"]


def test_bypass_actor_drift_is_detected_independent_of_list_order():
    desired = rs.build_ruleset("develop", policy(bypass_actors=("Team:1", "RepositoryRole:2")))
    reordered = [
        {"actor_id": 2, "actor_type": "RepositoryRole", "bypass_mode": "always"},
        {"actor_id": 1, "actor_type": "Team", "bypass_mode": "always"},
    ]
    existing = {**desired, "id": 1, "bypass_actors": reordered}
    assert not rs.diff_ruleset(desired, existing).changed

    existing_missing_one = {**desired, "id": 1, "bypass_actors": reordered[:1]}
    assert rs.diff_ruleset(desired, existing_missing_one).changed


def test_target_enforcement_and_conditions_drift_are_each_detected():
    desired = rs.build_ruleset("develop", policy())
    assert rs.diff_ruleset(desired, {**desired, "id": 1, "target": "tag"}).changed
    assert rs.diff_ruleset(desired, {**desired, "id": 1, "enforcement": "disabled"}).changed
    assert rs.diff_ruleset(
        desired, {**desired, "id": 1, "conditions": {"ref_name": {"include": [], "exclude": []}}}
    ).changed


# -------------------------------------------------------------------------- gh adapters


def test_api_raises_with_the_apis_own_reason_on_failure(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: completed(1, err="422 already exists"))
    with pytest.raises(RuntimeError, match="422 already exists"):
        rs._api("repos/o/r/rulesets")


def test_api_returns_none_for_an_empty_body(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: completed(out=""))
    assert rs._api("repos/o/r/rulesets/1", "--method", "DELETE") is None


def test_fetch_ruleset_refetches_the_named_entry_by_id_for_its_rules(monkeypatch):
    monkeypatch.setenv("GH_REPO", "o/r")
    calls = []

    def fake_api(*args, input_json=None):
        calls.append(args)
        if args == ("repos/o/r/rulesets",):
            return [{"id": 1, "name": "other"}, {"id": 2, "name": "vibey-gh: develop"}]
        if args == ("repos/o/r/rulesets/2",):
            return {"id": 2, "name": "vibey-gh: develop", "rules": []}
        raise AssertionError(f"unexpected call: {args}")

    monkeypatch.setattr(rs, "_api", fake_api)
    found = rs.fetch_ruleset("vibey-gh: develop")
    assert found == {"id": 2, "name": "vibey-gh: develop", "rules": []}


def test_fetch_ruleset_end_to_end_through_the_real_gh_adapter(monkeypatch):
    """Exercises the real `_api`, not a stand-in, including a genuine non-empty response."""
    monkeypatch.setenv("GH_REPO", "o/r")

    def run(args, **kwargs):
        if args[-1] == "repos/o/r/rulesets":
            return completed(out=json.dumps([{"id": 2, "name": "vibey-gh: develop"}]))
        if args[-1] == "repos/o/r/rulesets/2":
            return completed(out=json.dumps({"id": 2, "name": "vibey-gh: develop", "rules": []}))
        raise AssertionError(f"unexpected gh invocation: {args}")

    monkeypatch.setattr(subprocess, "run", run)
    found = rs.fetch_ruleset("vibey-gh: develop")
    assert found == {"id": 2, "name": "vibey-gh: develop", "rules": []}


def test_fetch_ruleset_returns_none_when_no_ruleset_has_that_name(monkeypatch):
    monkeypatch.setenv("GH_REPO", "o/r")
    monkeypatch.setattr(rs, "_api", lambda *a, **k: [{"id": 1, "name": "other"}])
    assert rs.fetch_ruleset("vibey-gh: develop") is None


def test_create_and_update_ruleset_post_the_payload_as_json(monkeypatch):
    monkeypatch.setenv("GH_REPO", "o/r")
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda args, **k: calls.append((args, k)) or completed())
    rs.create_ruleset({"name": "x"})
    args, kwargs = calls[0]
    assert args[:2] == ["gh", "api"] and "repos/o/r/rulesets" in args and "POST" in args
    assert json.loads(kwargs["input"]) == {"name": "x"}

    rs.update_ruleset(7, {"name": "x"})
    args, kwargs = calls[1]
    assert "repos/o/r/rulesets/7" in args and "PUT" in args


# ----------------------------------------------------------------- orchestration


def test_reconcile_one_creates_when_nothing_exists(monkeypatch):
    monkeypatch.setattr(rs, "fetch_ruleset", lambda name: None)
    created = []
    monkeypatch.setattr(rs, "create_ruleset", lambda payload: created.append(payload))
    outcome = rs.reconcile_one("develop", policy())
    assert outcome["changed"] and outcome["applied"] and created
    assert outcome["ruleset"] == "vibey-gh: develop"
    assert outcome["unexpected_rules"] == []


def test_reconcile_one_is_a_noop_when_nothing_has_drifted(monkeypatch):
    desired = rs.build_ruleset("develop", policy())
    monkeypatch.setattr(rs, "fetch_ruleset", lambda name: {**desired, "id": 9})
    monkeypatch.setattr(
        rs, "update_ruleset", lambda rid, payload: pytest.fail("nothing drifted; must not update")
    )
    monkeypatch.setattr(
        rs, "create_ruleset", lambda payload: pytest.fail("must not create when it exists")
    )
    outcome = rs.reconcile_one("develop", policy())
    assert not outcome["changed"] and not outcome["applied"]


def test_reconcile_one_updates_the_existing_ruleset_by_id_when_drifted(monkeypatch):
    desired = rs.build_ruleset("develop", policy(required_approvals=1))
    stale = {**desired, "id": 9, "rules": rs.desired_rules(policy(required_approvals=0))}
    monkeypatch.setattr(rs, "fetch_ruleset", lambda name: stale)
    updated = []
    monkeypatch.setattr(rs, "update_ruleset", lambda rid, payload: updated.append((rid, payload)))
    monkeypatch.setattr(
        rs, "create_ruleset", lambda payload: pytest.fail("must not create when it exists")
    )
    outcome = rs.reconcile_one("develop", policy(required_approvals=1))
    assert outcome["changed"] and outcome["applied"]
    assert updated and updated[0][0] == 9


def test_a_dry_run_never_creates_or_updates_anything(monkeypatch):
    def exploded(*a, **k):
        pytest.fail("dry run must not apply anything")

    monkeypatch.setattr(rs, "fetch_ruleset", lambda name: None)
    monkeypatch.setattr(rs, "create_ruleset", exploded)
    monkeypatch.setattr(rs, "update_ruleset", exploded)
    outcome = rs.reconcile_one("develop", policy(), dry_run=True)
    assert outcome["changed"] and not outcome["applied"]


def test_a_refused_ruleset_raises_rather_than_skipping_silently(monkeypatch):
    monkeypatch.setattr(rs, "fetch_ruleset", lambda name: None)

    def refused(payload):
        raise RuntimeError("422 required status check contexts must be unique")

    monkeypatch.setattr(rs, "create_ruleset", refused)
    with pytest.raises(RuntimeError, match="must be unique"):
        rs.reconcile_one("develop", policy())


def test_reconcile_covers_the_integration_and_release_branches(monkeypatch, tmp_path):
    cfg = GhConfig(
        root=tmp_path,
        integration_branch="develop",
        release_branch="main",
        rulesets=RulesetsConfig(integration=policy(), release=policy(required_approvals=2)),
    )
    seen = []

    def record(branch, p, dry_run=False):
        seen.append((branch, p, dry_run))
        return {}

    monkeypatch.setattr(rs, "reconcile_one", record)
    rs.reconcile(cfg, dry_run=True)
    assert seen == [
        ("develop", cfg.rulesets.integration, True),
        ("main", cfg.rulesets.release, True),
    ]


def test_reconcile_is_a_noop_when_disabled(monkeypatch, tmp_path):
    cfg = GhConfig(root=tmp_path, rulesets=RulesetsConfig(enabled=False))
    monkeypatch.setattr(
        rs, "reconcile_one", lambda *a, **k: pytest.fail("disabled must reconcile nothing")
    )
    assert rs.reconcile(cfg) == []


def test_a_request_body_is_actually_sent(monkeypatch):
    """`gh api` ignores stdin unless told to read it.

    Every ruleset reconciliation failed in production with HTTP 422 "data cannot be null"
    while the payload it had built was perfectly good — it simply never left the process.
    """
    import subprocess

    captured: list = []

    def run(command, **kwargs):
        captured.append((command, kwargs.get("input")))
        return subprocess.CompletedProcess(command, 0, "{}", "")

    monkeypatch.setattr(subprocess, "run", run)
    rs._api("repos/o/r/rulesets", "--method", "POST", input_json={"name": "x"})
    command, sent = captured[0]
    assert "--input" in command and command[command.index("--input") + 1] == "-"
    assert sent and '"name": "x"' in sent

    # A read needs no body and must not claim to have one.
    captured.clear()
    rs._api("repos/o/r/rulesets")
    assert "--input" not in captured[0][0]
