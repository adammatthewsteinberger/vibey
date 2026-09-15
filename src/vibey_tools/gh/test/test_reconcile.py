# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Reconciling branches stranded by a realign rewrite.

This module rewrites and deletes branches, so most of what matters here is what it
*refuses* to touch. A permanent branch must be unreachable from every mutating path, a
fork must never be mutated at all, and a contributor's own work must survive untouched no
matter how inconvenient its conflict is.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from vibey_gh import reconcile as rc
from vibey_gh.config import BranchSyncConfig, GhConfig, RealignConfig


def cfg(tmp_path: Path, **realign) -> GhConfig:
    return GhConfig(root=tmp_path, realign=RealignConfig(**realign))


def facts(**changes) -> rc.BranchFacts:
    value = dict(number=7, branch="vibey-gh/issue/1-abc", fork=False, unique_commits=1, behind=True)
    value.update(changes)
    return rc.BranchFacts(**value)


def completed(code=0, out="", err=""):
    return subprocess.CompletedProcess([], code, out, err)


# ------------------------------------------------------------------------ policy


@pytest.mark.parametrize(
    "kwargs,match",
    [
        ({"automation_prefixes": ()}, "must not be empty"),
        ({"automation_prefixes": ("a", "a")}, "must be unique"),
        ({"automation_prefixes": (" ",)}, "must be non-empty"),
        ({"automation_prefixes": ("-bad/",)}, "safe ref prefixes"),
        ({"automation_prefixes": ("/bad/",)}, "safe ref prefixes"),
        ({"automation_prefixes": ("a/../b",)}, "safe ref prefixes"),
        ({"automation_prefixes": ("a:b",)}, "safe ref prefixes"),
    ],
)
def test_invalid_realign_configuration_is_rejected(kwargs, match):
    with pytest.raises(ValueError, match=match):
        RealignConfig(**kwargs)


@pytest.mark.parametrize("value", [-1, 11])
def test_an_out_of_range_self_heal_budget_is_rejected(value):
    with pytest.raises(ValueError, match="between 0 and 10"):
        BranchSyncConfig(max_self_heals=value)


def test_an_empty_prefix_list_is_allowed_when_reconciliation_is_off():
    assert RealignConfig(reconcile_branches=False, automation_prefixes=()).automation_prefixes == ()


@pytest.mark.parametrize("branch", ["develop", "main", "", "-x", "a:b", "a/../b"])
def test_no_permanent_or_unsafe_ref_is_ever_deletable_or_rebasable(tmp_path, branch):
    config = cfg(tmp_path)
    assert not rc.deletable(branch, config)
    assert not rc.rebasable(branch, config)


def test_a_fork_branch_is_never_deletable(tmp_path):
    assert not rc.deletable("feature", cfg(tmp_path), fork=True)
    assert rc.deletable("feature", cfg(tmp_path))


def test_a_configured_permanent_branch_is_protected_under_its_own_name(tmp_path):
    config = GhConfig(root=tmp_path, integration_branch="trunk", release_branch="ship")
    assert not rc.deletable("trunk", config)
    assert not rc.deletable("ship", config)
    # The literal defaults stay denied independently, as defence in depth.
    assert not rc.deletable("develop", config)
    assert not rc.deletable("main", config)


def test_a_fully_duplicated_branch_is_closed_and_deleted(tmp_path):
    decision = rc.decide(facts(unique_commits=0), cfg(tmp_path))
    assert decision.action == rc.CLOSE
    assert decision.delete_branch
    assert "already upstream by patch identity" in decision.reason
    assert "deleted its branch" in decision.describe()


def test_deletion_and_closing_are_each_independently_configurable(tmp_path):
    kept = rc.decide(facts(unique_commits=0), cfg(tmp_path, delete_duplicate_branches=False))
    assert kept.action == rc.CLOSE and not kept.delete_branch
    assert "deleted its branch" not in kept.describe()

    left = rc.decide(facts(unique_commits=0), cfg(tmp_path, close_duplicates=False))
    assert left.action == rc.LEAVE and "disabled" in left.reason


def test_an_automation_branch_with_real_work_is_rebased(tmp_path):
    decision = rc.decide(facts(unique_commits=2), cfg(tmp_path))
    assert decision.action == rc.REBASE
    assert "2 unique commit(s)" in decision.reason


def test_a_contributor_branch_is_never_rewritten_only_merged_or_left(tmp_path):
    """Whatever else happens, a human's history is never rearranged underneath them."""
    config = GhConfig(
        root=tmp_path, branch_sync=BranchSyncConfig(update_contributor_branches=False)
    )
    decision = rc.decide(facts(branch="feature/mine", unique_commits=1), config)
    assert decision.action == rc.LEAVE and decision.notify
    assert "left for its author" in decision.reason

    quiet = rc.decide(
        facts(branch="feature/mine"),
        GhConfig(
            root=tmp_path,
            realign=RealignConfig(notify_contributor_branches=False),
            branch_sync=BranchSyncConfig(update_contributor_branches=False),
        ),
    )
    assert quiet.action == rc.LEAVE and not quiet.notify
    # No contributor branch reaches a rewriting action under any configuration.
    for policy in (cfg(tmp_path), config):
        assert rc.decide(facts(branch="feature/mine"), policy).action != rc.REBASE


@pytest.mark.parametrize(
    "changes,reason",
    [
        ({"branch": "develop"}, "permanent and unsafe"),
        ({"branch": "-hostile"}, "permanent and unsafe"),
    ],
)
def test_untouchable_branches_are_left_regardless_of_their_contents(tmp_path, changes, reason):
    decision = rc.decide(facts(unique_commits=0, **changes), cfg(tmp_path))
    assert decision.action == rc.LEAVE and reason in decision.reason


def test_a_fork_may_be_moved_forward_but_never_rewritten(tmp_path):
    """The whole fork invariant in one place: forward-merge yes, rewrite never.

    `update-branch` is GitHub's own button and only succeeds where the contributor left
    maintainer edits enabled, so it carries their consent. Rebasing, closing, and deleting
    someone else's fork must stay unreachable under every configuration and every content.
    """
    behind = rc.decide(facts(fork=True, behind=True), cfg(tmp_path))
    assert behind.action == rc.UPDATE and not behind.delete_branch

    current = rc.decide(facts(fork=True, behind=False), cfg(tmp_path))
    assert current.action == rc.LEAVE

    for policy in (
        cfg(tmp_path),
        cfg(tmp_path, close_duplicates=True, delete_duplicate_branches=True),
        GhConfig(root=tmp_path, branch_sync=BranchSyncConfig(update_contributor_branches=False)),
    ):
        for content in (0, 1, 5):
            decision = rc.decide(facts(fork=True, unique_commits=content), policy)
            assert decision.action in {rc.UPDATE, rc.LEAVE}
            assert not decision.delete_branch
    assert not rc.deletable("anything", cfg(tmp_path), fork=True)
    assert not rc.rebasable("anything", cfg(tmp_path), fork=True)


def test_reconciliation_can_be_switched_off_entirely(tmp_path):
    assert rc.decide(facts(), cfg(tmp_path, reconcile_branches=False)).action == rc.LEAVE
    assert rc.reconcile(cfg(tmp_path, reconcile_branches=False)) == []


def test_prefixes_decide_what_counts_as_automation_owned(tmp_path):
    config = cfg(tmp_path, automation_prefixes=("bots/", "vibey-gh/"))
    assert rc.automation_owned("bots/x", config)
    assert rc.automation_owned("vibey-gh/issue/1", config)
    assert not rc.automation_owned("feature/x", config)


def test_a_contributor_branch_that_is_behind_is_merged_forward_not_rewritten(tmp_path):
    """GitHub's own "Update branch" semantics: a merge, never a rewrite of their history."""
    decision = rc.decide(facts(branch="feature/mine", behind=True), cfg(tmp_path))
    assert decision.action == rc.UPDATE
    assert "merging the integration branch forward" in decision.reason

    current = rc.decide(facts(branch="feature/mine", behind=False), cfg(tmp_path))
    assert current.action == rc.LEAVE and not current.notify

    off = rc.decide(
        facts(branch="feature/mine", behind=True),
        GhConfig(
            root=tmp_path,
            branch_sync=BranchSyncConfig(update_contributor_branches=False),
        ),
    )
    assert off.action == rc.LEAVE and off.notify


def test_an_automation_branch_already_current_is_left_alone(tmp_path):
    assert rc.decide(facts(behind=False), cfg(tmp_path)).action == rc.LEAVE
    assert rc.decide(facts(behind=True), cfg(tmp_path)).action == rc.REBASE


# -------------------------------------------------------------------------- git


def test_patch_identity_decides_what_counts_as_unique(tmp_path, monkeypatch):
    config = cfg(tmp_path)
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: completed(out="+ aaa\n- bbb\n+ ccc\n"))
    assert rc.unique_commits(config, "topic") == 2

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: completed(out="- bbb\n"))
    assert rc.unique_commits(config, "topic") == 0

    # An unreadable ref must never be reported as "nothing unique", which would close a PR.
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: completed(1, err="bad ref"))
    assert rc.unique_commits(config, "topic") == 1


def test_measure_only_runs_git_for_branches_that_could_be_acted_on(tmp_path, monkeypatch):
    config = cfg(tmp_path)
    monkeypatch.setattr(rc, "unique_commits", lambda c, b: 5)
    monkeypatch.setattr(rc, "is_behind", lambda c, b: True)
    assert rc.measure(config, facts()).unique_commits == 5
    for skipped in (facts(branch="develop"), facts(branch="-x")):
        assert rc.measure(config, skipped) is skipped
    # A fork's ref is not in this repository, so neither Git question can be asked of it.
    monkeypatch.setattr(rc, "unique_commits", lambda c, b: pytest.fail("no git on a fork"))
    monkeypatch.setattr(rc, "is_behind", lambda c, b: pytest.fail("no git on a fork"))
    measured = rc.measure(config, facts(fork=True))
    assert measured.fork and measured.behind and measured.unique_commits == 1


def test_rebase_replays_a_branch_and_refuses_to_force_over_newer_work(tmp_path, monkeypatch):
    config = cfg(tmp_path)
    calls: list[list[str]] = []

    def run(args, **kwargs):
        calls.append(args)
        if args[:2] == ["git", "rev-parse"]:
            remote = any(str(a).startswith("origin/") for a in args)
            return completed(out=("old\n" if remote else "new\n"))
        return completed()

    monkeypatch.setattr(subprocess, "run", run)
    changed, detail = rc.rebase_branch(config, "vibey-gh/issue/1")
    assert changed and "onto the new tip" in detail
    pushed = next(c for c in calls if c[:2] == ["git", "push"])
    assert "--force-with-lease=refs/heads/vibey-gh/issue/1:old" in pushed
    assert "HEAD:refs/heads/vibey-gh/issue/1" in pushed
    assert not any("--delete" in " ".join(c) for c in calls)


@pytest.mark.parametrize("branch", ["develop", "main", "-x", "a:b"])
def test_rebase_refuses_a_protected_or_unsafe_branch(tmp_path, branch):
    with pytest.raises(ValueError, match="refusing to rebase"):
        rc.rebase_branch(cfg(tmp_path), branch)


@pytest.mark.parametrize("branch", ["develop", "main", "-x", "a:b"])
def test_delete_refuses_a_protected_or_unsafe_branch(tmp_path, branch):
    with pytest.raises(ValueError, match="refusing to delete"):
        rc.delete_branch(cfg(tmp_path), branch)


def test_rebase_reports_every_way_it_can_decline(tmp_path, monkeypatch):
    config = cfg(tmp_path)

    def responder(**outcomes):
        def run(args, **kwargs):
            if args[:2] == ["git", "rev-parse"]:
                return completed(out=outcomes.get("rev", "old") + "\n")
            for key in ("checkout", "rebase", "push"):
                if args[1] == key and outcomes.get(key):
                    return completed(1, err="boom")
            return completed()

        return run

    monkeypatch.setattr(subprocess, "run", responder(rev=""))
    assert rc.rebase_branch(config, "vibey-gh/a") == (False, "branch no longer exists")

    monkeypatch.setattr(subprocess, "run", responder(checkout=True))
    assert rc.rebase_branch(config, "vibey-gh/a")[1] == "could not check the branch out"

    monkeypatch.setattr(subprocess, "run", responder(rebase=True))
    assert "conflicted" in rc.rebase_branch(config, "vibey-gh/a")[1]

    # Identical before and after means the branch was already current.
    monkeypatch.setattr(subprocess, "run", responder())
    assert rc.rebase_branch(config, "vibey-gh/a") == (False, "already on the current tip")

    def diverged(args, **kwargs):
        if args[:2] == ["git", "rev-parse"]:
            return completed(out=("old\n" if "origin/" in " ".join(args) else "new\n"))
        return completed(1, err="stale") if args[1] == "push" else completed()

    monkeypatch.setattr(subprocess, "run", diverged)
    assert "push refused" in rc.rebase_branch(config, "vibey-gh/a")[1]


def test_behind_is_ancestry_of_the_integration_tip(tmp_path, monkeypatch):
    config = cfg(tmp_path)
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: completed(0))
    assert rc.is_behind(config, "topic") is False
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: completed(1))
    assert rc.is_behind(config, "topic") is True


def test_update_branch_uses_githubs_own_endpoint_and_reports_refusals(tmp_path, monkeypatch):
    monkeypatch.setenv("GH_REPO", "o/r")
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda args, **k: calls.append(args) or completed())
    applied, detail = rc.update_branch(cfg(tmp_path), 12)
    assert applied and "merged the base forward" in detail
    assert "repos/o/r/pulls/12/update-branch" in calls[0]
    assert "PUT" in calls[0]

    # A refusal must say why: "not applied, no detail" is how two branches sat stuck.
    monkeypatch.setattr(
        subprocess, "run", lambda args, **k: completed(1, err="gh: merge conflict (HTTP 422)")
    )
    applied, detail = rc.update_branch(cfg(tmp_path), 12)
    assert not applied and "422" in detail


def test_a_branch_github_refuses_is_merged_forward_locally(tmp_path, monkeypatch):
    """GitHub computes mergeability without this repository's merge drivers, so it calls a
    branch conflicting that merges cleanly here. The fallback is a merge, never a rewrite."""
    config = cfg(tmp_path)
    calls: list = []

    def run(args, **kwargs):
        calls.append(args)
        if args[:2] == ["git", "rev-parse"]:
            remote = any(str(a).startswith("origin/") for a in args)
            return completed(out=("old\n" if remote else "new\n"))
        return completed()

    monkeypatch.setattr(subprocess, "run", run)
    applied, detail = rc.merge_forward(config, "feature/theirs")
    assert applied and "merged develop forward" in detail
    pushed = next(c for c in calls if c[:2] == ["git", "push"])
    assert "HEAD:refs/heads/feature/theirs" in pushed
    assert not any("force" in " ".join(c) for c in calls), "a merge never rewrites history"


def test_merging_forward_reports_every_way_it_can_decline(tmp_path, monkeypatch):
    config = cfg(tmp_path)

    def responder(**outcomes):
        def run(args, **kwargs):
            if args[:2] == ["git", "rev-parse"]:
                return completed(out=outcomes.get("rev", "old") + "\n")
            for key in ("checkout", "merge", "push"):
                if args[1] == key and outcomes.get(key):
                    return completed(1, err="boom")
            return completed()

        return run

    monkeypatch.setattr(subprocess, "run", responder(rev=""))
    assert rc.merge_forward(config, "feature/x") == (False, "branch no longer exists")

    monkeypatch.setattr(subprocess, "run", responder(checkout=True))
    assert rc.merge_forward(config, "feature/x")[1] == "could not check the branch out"

    monkeypatch.setattr(subprocess, "run", responder(merge=True))
    assert "conflicted" in rc.merge_forward(config, "feature/x")[1]

    # Identical before and after means the base was already in the branch.
    monkeypatch.setattr(subprocess, "run", responder())
    assert rc.merge_forward(config, "feature/x") == (False, "already current")

    def diverged(args, **kwargs):
        if args[:2] == ["git", "rev-parse"]:
            return completed(out=("old\n" if "origin/" in " ".join(args) else "new\n"))
        return completed(1, err="stale") if args[1] == "push" else completed()

    monkeypatch.setattr(subprocess, "run", diverged)
    assert "push refused" in rc.merge_forward(config, "feature/x")[1]


@pytest.mark.parametrize("branch", ["develop", "main", "-x", "a:b"])
def test_merging_forward_refuses_a_protected_or_unsafe_branch(tmp_path, branch):
    with pytest.raises(ValueError, match="refusing to merge into"):
        rc.merge_forward(cfg(tmp_path), branch)


# ------------------------------------------------------------------- gh adapters


def test_open_pull_requests_reads_branch_ownership(monkeypatch, tmp_path):
    monkeypatch.setenv("GH_REPO", "o/r")
    monkeypatch.setattr(
        rc.github_state,
        "gh_json",
        lambda *a: [
            {"number": 1, "headRefName": "vibey-gh/issue/1", "isCrossRepository": False},
            {"number": 2, "headRefName": "theirs", "isCrossRepository": True},
        ],
    )
    listed = rc.open_pull_requests(cfg(tmp_path))
    assert [(f.number, f.fork) for f in listed] == [(1, False), (2, True)]

    monkeypatch.setattr(rc.github_state, "gh_json", lambda *a: None)
    assert rc.open_pull_requests(cfg(tmp_path)) == []


def test_closing_explains_itself_before_it_closes(monkeypatch, tmp_path):
    monkeypatch.setenv("GH_REPO", "o/r")
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda args, **k: calls.append(args) or completed())
    rc.close_pull_request(cfg(tmp_path), rc.Decision(3, "b", rc.CLOSE, "why"))
    assert calls[0][:3] == ["gh", "pr", "comment"]
    assert "already on" in calls[0][-1] and "nothing is lost" in calls[0][-1]
    assert calls[1][:3] == ["gh", "pr", "close"]


def test_a_contributor_is_told_how_to_recover_their_own_branch(monkeypatch, tmp_path):
    monkeypatch.setenv("GH_REPO", "o/r")
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda args, **k: calls.append(args) or completed())
    rc.notify(cfg(tmp_path), rc.Decision(4, "feature/x", rc.LEAVE, "why", notify=True))
    body = calls[0][-1]
    assert "git rebase origin/develop" in body
    assert "left the branch untouched" in body


def test_delete_branch_reports_whether_github_accepted_it(monkeypatch, tmp_path):
    monkeypatch.setenv("GH_REPO", "o/r")
    monkeypatch.setattr(subprocess, "run", lambda args, **k: completed())
    assert rc.delete_branch(cfg(tmp_path), "vibey-gh/issue/1") is True
    monkeypatch.setattr(subprocess, "run", lambda args, **k: completed(1))
    assert rc.delete_branch(cfg(tmp_path), "vibey-gh/issue/1") is False


# ----------------------------------------------------------------- orchestration


def test_reconcile_applies_one_action_per_pull_request(monkeypatch, tmp_path):
    config = cfg(tmp_path)
    monkeypatch.setattr(
        rc,
        "open_pull_requests",
        lambda c: [
            rc.BranchFacts(1, "vibey-gh/issue/dup"),
            rc.BranchFacts(2, "vibey-gh/issue/work"),
            rc.BranchFacts(3, "feature/theirs"),
            rc.BranchFacts(4, "theirs", fork=True),
            rc.BranchFacts(5, "vibey-gh/issue/current"),
        ],
    )
    counts = {
        "vibey-gh/issue/dup": 0,
        "vibey-gh/issue/work": 2,
        "feature/theirs": 1,
        "theirs": 1,
        "vibey-gh/issue/current": 1,
    }
    monkeypatch.setattr(rc, "unique_commits", lambda c, b: counts[b])
    monkeypatch.setattr(rc, "is_behind", lambda c, b: b != "vibey-gh/issue/current")
    monkeypatch.setattr(
        rc, "update_branch", lambda c, n: (done.append(f"update #{n}") or True, "ok")
    )
    done: list[str] = []
    monkeypatch.setattr(
        rc, "rebase_branch", lambda c, b: done.append(f"rebase {b}") or (True, "ok")
    )
    monkeypatch.setattr(rc, "close_pull_request", lambda c, d: done.append(f"close {d.branch}"))
    monkeypatch.setattr(rc, "delete_branch", lambda c, b: done.append(f"delete {b}") or True)
    monkeypatch.setattr(rc, "notify", lambda c, d: done.append(f"notify {d.branch}"))

    outcomes = rc.reconcile(config)
    assert [o["action"] for o in outcomes] == [
        rc.CLOSE,
        rc.REBASE,
        rc.UPDATE,
        rc.UPDATE,
        rc.LEAVE,
    ]
    assert done == [
        "close vibey-gh/issue/dup",
        "delete vibey-gh/issue/dup",
        "rebase vibey-gh/issue/work",
        "update #3",
        "update #4",
    ]
    assert outcomes[0]["deleted"] is True
    assert outcomes[1]["applied"] is True and outcomes[1]["detail"] == "ok"
    assert outcomes[2]["applied"] is True
    # The fork was moved forward by merge, never rewritten.
    assert outcomes[3]["applied"] is True and not outcomes[3]["delete_branch"]
    # A branch already on the tip is reported and otherwise untouched.
    assert "applied" not in outcomes[4] and "notified" not in outcomes[4]
    assert "already current" in outcomes[4]["reason"]


def test_a_closed_duplicate_keeps_its_branch_when_deletion_is_disabled(monkeypatch, tmp_path):
    monkeypatch.setattr(rc, "open_pull_requests", lambda c: [rc.BranchFacts(1, "vibey-gh/a")])
    monkeypatch.setattr(rc, "unique_commits", lambda c, b: 0)
    monkeypatch.setattr(rc, "close_pull_request", lambda c, d: None)
    monkeypatch.setattr(
        rc, "delete_branch", lambda c, b: pytest.fail("deletion is disabled by configuration")
    )
    outcome = rc.reconcile(cfg(tmp_path, delete_duplicate_branches=False))[0]
    assert outcome["action"] == rc.CLOSE and outcome["applied"] is True
    assert "deleted" not in outcome


def test_a_contributor_is_notified_when_updating_their_branch_is_disabled(monkeypatch, tmp_path):
    config = GhConfig(
        root=tmp_path, branch_sync=BranchSyncConfig(update_contributor_branches=False)
    )
    monkeypatch.setattr(rc, "open_pull_requests", lambda c: [rc.BranchFacts(3, "feature/theirs")])
    monkeypatch.setattr(rc, "unique_commits", lambda c, b: 1)
    monkeypatch.setattr(rc, "is_behind", lambda c, b: True)
    told: list = []
    monkeypatch.setattr(rc, "notify", lambda c, d: told.append(d.branch))
    outcome = rc.reconcile(config)[0]
    assert outcome["action"] == rc.LEAVE and outcome["notified"] is True
    assert told == ["feature/theirs"]


def test_a_branch_github_refuses_falls_back_to_a_local_merge(monkeypatch, tmp_path):
    """The refusal is the normal case for the branches that most need updating."""
    monkeypatch.setattr(rc, "open_pull_requests", lambda c: [rc.BranchFacts(3, "feature/theirs")])
    monkeypatch.setattr(rc, "unique_commits", lambda c, b: 1)
    monkeypatch.setattr(rc, "is_behind", lambda c, b: True)
    monkeypatch.setattr(rc, "update_branch", lambda c, n: (False, "merge conflict (HTTP 422)"))
    done: list = []
    monkeypatch.setattr(
        rc,
        "merge_forward",
        lambda c, b: (done.append(b) or True, "merged develop forward as abc1234"),
    )
    outcome = rc.reconcile(cfg(tmp_path))[0]
    assert done == ["feature/theirs"], "the local merge must be attempted"
    assert outcome["applied"] is True
    assert "merged develop forward" in outcome["detail"]


def test_a_fork_github_refuses_is_never_merged_locally(monkeypatch, tmp_path):
    """A fork's branch is not this repository's to write to, whatever GitHub answered."""
    monkeypatch.setattr(
        rc, "open_pull_requests", lambda c: [rc.BranchFacts(4, "theirs", fork=True)]
    )
    monkeypatch.setattr(rc, "update_branch", lambda c, n: (False, "refused"))
    monkeypatch.setattr(
        rc, "merge_forward", lambda c, b: pytest.fail("a fork is never written to locally")
    )
    outcome = rc.reconcile(cfg(tmp_path))[0]
    assert outcome["applied"] is False and outcome["detail"] == "refused"


def test_a_dry_run_decides_without_touching_anything(monkeypatch, tmp_path):
    monkeypatch.setattr(rc, "open_pull_requests", lambda c: [rc.BranchFacts(1, "vibey-gh/a")])
    monkeypatch.setattr(rc, "unique_commits", lambda c, b: 0)

    def exploded(*a, **k):
        pytest.fail("dry run must not mutate")

    monkeypatch.setattr(rc, "close_pull_request", exploded)
    monkeypatch.setattr(rc, "delete_branch", exploded)
    monkeypatch.setattr(rc, "rebase_branch", exploded)
    outcomes = rc.reconcile(cfg(tmp_path), dry_run=True)
    assert outcomes[0]["action"] == rc.CLOSE and "applied" not in outcomes[0]


def test_a_realign_stands_even_when_reconciliation_cannot_reach_github(monkeypatch, tmp_path):
    """The realign has already happened; a follow-up that needs credentials this context
    lacks must not report it as failed and leave the caller thinking it never converged."""
    from vibey_gh import realign as realign_mod

    def run(args, **kwargs):
        if args[:2] == ["git", "rev-parse"]:
            return completed(out=("dev\n" if args[-1].endswith("develop") else "rel\n"))
        return completed()

    monkeypatch.setattr(subprocess, "run", run)

    def unreachable(cfg):
        raise RuntimeError("gh repo view: no credentials in this context")

    monkeypatch.setattr(realign_mod.reconcile, "reconcile", unreachable)
    changed, message = realign_mod.realign(cfg(tmp_path))
    assert changed, "the realign itself succeeded and must be reported as such"
    assert "realigned to main" in message
    assert "branches were not reconciled" in message
    assert "no credentials" in message


def test_realign_reconciles_the_branches_its_rewrite_stranded(monkeypatch, tmp_path):
    from vibey_gh import realign as realign_mod

    config = cfg(tmp_path)

    # `realign` only pushes when the two branches differ but their trees are identical.
    def run(args, **kwargs):
        if args[:2] == ["git", "rev-parse"]:
            return completed(out=("dev\n" if args[-1].endswith("develop") else "rel\n"))
        return completed()

    monkeypatch.setattr(subprocess, "run", run)
    monkeypatch.setattr(
        realign_mod.reconcile,
        "reconcile",
        lambda c: [{"pr": 9, "branch": "vibey-gh/issue/x", "action": rc.CLOSE}],
    )
    changed, message = realign_mod.realign(config)
    assert changed
    assert "realigned to main" in message
    assert "9 (vibey-gh/issue/x): close" in message
