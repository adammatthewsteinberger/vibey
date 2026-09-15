# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Reconcile GitHub repository rulesets from `.vibey-gh.toml`.

`repository-profile.yml` reconciles description, topics, and collaboration settings, then
only *verifies* that the integration and release branches are protected — nothing ever set
that protection. This module is what sets it, using the same idempotent read-compare-write
shape that verification already trusts.

Building a desired ruleset and comparing it against a fetched one is pure and dependency
free, so that logic lives here with no I/O; the functions that talk to `gh` sit beside it,
exactly the split `vibey_gh.reconcile` already uses for branch reconciliation. A rule type
the configuration does not mention is never removed from an existing ruleset — it is
carried forward untouched and reported as unexpected, because a silent deletion of someone
else's rule is indistinguishable from data loss.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from typing import Any, cast

from vibey_gh import github_state
from vibey_gh.config import GhConfig, RulesetConfig

# The rule types this module ever declares. Anything else found on an existing ruleset is
# somebody else's addition and is preserved rather than reconciled away.
DELETION = "deletion"
NON_FAST_FORWARD = "non_fast_forward"
LINEAR_HISTORY = "required_linear_history"
SIGNATURES = "required_signatures"
PULL_REQUEST = "pull_request"
STATUS_CHECKS = "required_status_checks"


def ruleset_name(branch: str) -> str:
    """The name this automation looks for and creates. Stable across a branch rename in
    `[branches]`, because it is derived from the resolved branch, not the config key."""
    return f"vibey-gh: {branch}"


def desired_rules(policy: RulesetConfig) -> list[dict[str, Any]]:
    """The rule list one ruleset should declare, built from policy alone.

    `deletion` and `non_fast_forward` are unconditional: `RulesetConfig` already refuses to
    construct with `allow_deletions` or `allow_force_pushes` true, so every desired ruleset
    blocks both by construction rather than by a runtime branch here.
    """
    rules: list[dict[str, Any]] = [{"type": DELETION}, {"type": NON_FAST_FORWARD}]
    if policy.require_linear_history:
        rules.append({"type": LINEAR_HISTORY})
    if policy.require_signed_commits:
        rules.append({"type": SIGNATURES})
    rules.append(
        {
            "type": PULL_REQUEST,
            "parameters": {
                "required_approving_review_count": policy.required_approvals,
                "dismiss_stale_reviews_on_push": policy.dismiss_stale_reviews,
                "require_code_owner_review": False,
                "require_last_push_approval": False,
                "required_review_thread_resolution": policy.require_conversation_resolution,
            },
        }
    )
    if policy.required_checks:
        rules.append(
            {
                "type": STATUS_CHECKS,
                "parameters": {
                    "required_status_checks": [
                        {"context": check} for check in policy.required_checks
                    ],
                    "strict_required_status_checks_policy": policy.strict_required_checks,
                },
            }
        )
    return rules


def bypass_actor_payload(bypass_actors: tuple[str, ...]) -> list[dict[str, Any]]:
    """`"RepositoryRole:5"` becomes the actor object the rulesets API expects.

    `RulesetConfig` already validates the `<type>:<id>` shape, so this only ever splits
    already-trusted strings.
    """
    payload = []
    for actor in bypass_actors:
        actor_type, _, actor_id = actor.partition(":")
        payload.append(
            {"actor_id": int(actor_id), "actor_type": actor_type, "bypass_mode": "always"}
        )
    return payload


def build_ruleset(branch: str, policy: RulesetConfig) -> dict[str, Any]:
    """The complete desired ruleset payload for one branch, ready to `POST` or `PUT`."""
    return {
        "name": ruleset_name(branch),
        "target": "branch",
        "enforcement": "active",
        "bypass_actors": bypass_actor_payload(policy.bypass_actors),
        "conditions": {"ref_name": {"include": [f"refs/heads/{branch}"], "exclude": []}},
        "rules": desired_rules(policy),
    }


def _rules_by_type(rules: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {rule["type"]: rule for rule in rules}


def _bypass_key(actors: list[dict[str, Any]]) -> list[tuple[Any, Any, Any]]:
    return sorted(
        (actor.get("actor_id"), actor.get("actor_type"), actor.get("bypass_mode"))
        for actor in actors
    )


@dataclass(frozen=True)
class Diff:
    """The result of comparing a desired ruleset against what GitHub actually has."""

    changed: bool
    payload: dict[str, Any]
    unexpected_rules: tuple[str, ...]


def diff_ruleset(desired: dict[str, Any], existing: dict[str, Any] | None) -> Diff:
    """Compare `desired` against a fetched ruleset without ever discarding an unmentioned
    rule: `payload` always carries every rule `existing` had that `desired` did not."""
    if existing is None:
        return Diff(True, desired, ())

    desired_by_type = _rules_by_type(desired["rules"])
    existing_by_type = _rules_by_type(existing.get("rules", []))
    unexpected = tuple(sorted(set(existing_by_type) - set(desired_by_type)))
    merged_rules = [existing_by_type[kind] for kind in unexpected] + desired["rules"]

    changed = (
        existing.get("target") != desired["target"]
        or existing.get("enforcement") != desired["enforcement"]
        or _bypass_key(existing.get("bypass_actors") or []) != _bypass_key(desired["bypass_actors"])
        or existing.get("conditions") != desired["conditions"]
        or any(existing_by_type.get(kind) != rule for kind, rule in desired_by_type.items())
    )
    payload = {**desired, "rules": merged_rules}
    return Diff(changed, payload, unexpected)


# --------------------------------------------------------------------------- gh adapters


def _api(*args: str, input_json: dict[str, Any] | None = None) -> Any:
    command = ["gh", "api", *args]
    if input_json is not None:
        # `gh api` ignores stdin unless it is told to read it. Without this the body is
        # silently empty and GitHub answers "data cannot be null" — which is how every
        # ruleset reconciliation failed with a 422 while the payload was perfectly good.
        command += ["--input", "-"]
    run = subprocess.run(
        command,
        input=json.dumps(input_json) if input_json is not None else None,
        capture_output=True,
        text=True,
        check=False,
    )
    if run.returncode:
        raise RuntimeError(f"gh api {' '.join(args)}: {run.stderr.strip()}")
    return json.loads(run.stdout) if run.stdout.strip() else None


def fetch_ruleset(name: str) -> dict[str, Any] | None:
    """The named ruleset, fully populated with its rules — or `None` if none exists yet.

    The list endpoint's entries omit `rules`, so a match is re-fetched by ID rather than
    compared against the summary GitHub hands back from the list.
    """
    repository = github_state.repository()
    listing = _api(f"repos/{repository}/rulesets") or []
    for item in listing:
        if item.get("name") == name:
            return cast("dict[str, Any] | None", _api(f"repos/{repository}/rulesets/{item['id']}"))
    return None


def create_ruleset(payload: dict[str, Any]) -> None:
    _api(f"repos/{github_state.repository()}/rulesets", "--method", "POST", input_json=payload)


def update_ruleset(ruleset_id: int, payload: dict[str, Any]) -> None:
    _api(
        f"repos/{github_state.repository()}/rulesets/{ruleset_id}",
        "--method",
        "PUT",
        input_json=payload,
    )


def reconcile_one(branch: str, policy: RulesetConfig, *, dry_run: bool = False) -> dict[str, Any]:
    """Decide and, unless `dry_run`, apply the outcome for one branch's ruleset.

    A ruleset the API refuses raises rather than being swallowed: a skipped reconciliation
    is indistinguishable from a satisfied one, and that is exactly the silent-skip failure
    mode this module must not repeat.
    """
    name = ruleset_name(branch)
    desired = build_ruleset(branch, policy)
    existing = fetch_ruleset(name)
    result = diff_ruleset(desired, existing)
    outcome: dict[str, Any] = {
        "ruleset": name,
        "branch": branch,
        "changed": result.changed,
        "unexpected_rules": list(result.unexpected_rules),
        "applied": False,
    }
    if dry_run or not result.changed:
        return outcome
    if existing is None:
        create_ruleset(result.payload)
    else:
        update_ruleset(existing["id"], result.payload)
    outcome["applied"] = True
    return outcome


def reconcile(cfg: GhConfig, *, dry_run: bool = False) -> list[dict[str, Any]]:
    """Reconcile every configured ruleset. Empty when `[rulesets].enabled` is false."""
    if not cfg.rulesets.enabled:
        return []
    targets = (
        (cfg.integration_branch, cfg.rulesets.integration),
        (cfg.release_branch, cfg.rulesets.release),
    )
    return [reconcile_one(branch, policy, dry_run=dry_run) for branch, policy in targets]
