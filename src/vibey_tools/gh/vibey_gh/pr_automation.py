# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Policy and durable state for event-driven pull-request automation.

The workflow is intentionally thin.  It gathers GitHub data, asks this module for a
decision, and dispatches an agent only for the explicit ``repair`` or ``review`` states.
That keeps stale-SHA rejection, trust, retry limits, and check classification testable.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, cast

from vibey_gh import github_state
from vibey_gh.config import GhConfig, normalise_actor
from vibey_gh.issue_automation import sanitize

STATE_MARKER = "vibey-gh-pr-automation"
EXTERNAL_REPAIR_LABEL = "vibey-gh:external-repair"
REPAIRING_LABEL = "vibey-gh:repairing"
EXHAUSTED_LABEL = "vibey-gh:repair-exhausted"
BLOCKED_LABEL = "vibey-gh:automation-blocked"
AUTOMATION_LABELS = (EXTERNAL_REPAIR_LABEL, REPAIRING_LABEL, EXHAUSTED_LABEL, BLOCKED_LABEL)
PASSING = {"SUCCESS", "NEUTRAL", "SKIPPED"}
FAILING = {"FAILURE", "TIMED_OUT", "STARTUP_FAILURE", "ACTION_REQUIRED"}
OPERATIONAL = {"CANCELLED", "STALE"}
# Every check this workflow publishes itself. None may be counted in the rollup it
# computes, and one of them makes that urgent rather than tidy: `Evaluate current head` is
# still IN_PROGRESS *while* it computes the rollup, so counting it means the state is
# always "pending". That normally survives only because a later run sees the earlier
# evaluate completed — and when the last scan finishes before some other gating check
# does, no later run is coming. The pull request then sits blocked with every check green
# and nothing to rerun, until the scheduled backstop notices hours later.
#
# GitHub names a check run for its job, and prefixes it with the workflow name when the
# run came from `workflow_run`, so both spellings are excluded.
OWN_JOBS = (
    "Dispatch recovery evaluations",
    "Evaluate current head",
    "Exact-head code and documentation review",
    "Mirror fork for safe repair",
    "Repair failed scans or review findings",
    "Resolve merge conflicts",
    "Escalate exhausted repair lineage",
    "Local review fallback",
    "gate",
)
OWN_CHECKS = frozenset(
    [name for job in OWN_JOBS for name in (job, f"PR automation / {job}")] + ["Merge train / merge"]
)
PULL_REQUEST_TRIGGERS = ("pull_request", "pull_request_target")
_STATE_RE = github_state.marker_pattern(STATE_MARKER)
_NAME_RE = re.compile(r"""^(?:name|"name"|'name'):\s*(.*?)\s*(?:#.*)?$""")
_ON_RE = re.compile(r"""^(?:on|"on"|'on'):\s*(.*?)\s*(?:#.*)?$""")
_KEY_RE = re.compile(r"^([A-Za-z_]+):")


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    conclusion: str | None
    url: str = ""


@dataclass
class AutomationState:
    lineage_sha: str
    current_sha: str
    attempts: int = 0
    review_sha: str | None = None
    review_passed: bool | None = None
    replacement_pr: int | None = None
    heals: int = 0
    history: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class Evaluation:
    pr: int
    head_sha: str
    base: str
    author: str
    trusted: bool
    state: str
    pending_checks: tuple[str, ...] = ()
    failed_checks: tuple[str, ...] = ()
    repair_attempt: int = 0
    repair_branch: str | None = None
    reason: str = ""

    def to_json(self) -> str:
        payload = asdict(self)
        payload["pending_checks"] = list(self.pending_checks)
        payload["failed_checks"] = list(self.failed_checks)
        return json.dumps(payload, sort_keys=True)


@dataclass(frozen=True)
class ScanWorkflowReport:
    problems: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.problems


def _workflow_name(text: str) -> str | None:
    """The workflow's display `name:`, matched the way GitHub matches `workflow_run`."""
    for line in text.splitlines():
        match = _NAME_RE.match(line)
        if match:
            return match.group(1).strip("'\"") or None
    return None


def _workflow_triggers(text: str) -> set[str]:
    """Best-effort top-level `on:` trigger keys.

    Not a general YAML parser — every shipped and generated workflow indents its `on:`
    block consistently, and that convention, not full YAML semantics, is all this reads.
    """
    lines = text.splitlines()
    for index, line in enumerate(lines):
        match = _ON_RE.match(line)
        if not match:
            continue
        inline = match.group(1).strip()
        if inline:
            return {
                part.strip().strip("'\"") for part in inline.strip("[]").split(",") if part.strip()
            }
        triggers: set[str] = set()
        base_indent: int | None = None
        for follower in lines[index + 1 :]:
            if not follower.strip() or follower.lstrip().startswith("#"):
                continue
            indent = len(follower) - len(follower.lstrip())
            if base_indent is None:
                base_indent = indent
            if indent < base_indent:
                break
            if indent == base_indent:
                key = _KEY_RE.match(follower.strip())
                if key:
                    triggers.add(key.group(1))
        return triggers
    return set()


def check_scan_workflows(cfg: GhConfig) -> ScanWorkflowReport:
    """Every `pr_automation.scan_workflows` entry must be able to fire for a pull request.

    `evaluate` waits for a `workflow_run` completion from each name. A workflow that
    exists but triggers only on `push` can structurally never complete for a pull
    request: `state` never leaves `pending`, the gate never publishes, and — if it is a
    required check — no pull request can ever merge, silently and permanently. A name
    absent from `.github/workflows/` is not this failure; it may live elsewhere or under
    another name, so it is left alone.
    """
    if not cfg.pr_automation.enabled:
        return ScanWorkflowReport(())
    directory = cfg.root / ".github" / "workflows"
    if not directory.is_dir():
        return ScanWorkflowReport(())
    by_name: dict[str, tuple[Path, set[str]]] = {}
    for path in sorted(directory.glob("*.yml")) + sorted(directory.glob("*.yaml")):
        text = path.read_text(encoding="utf-8")
        name = _workflow_name(text)
        if name and name not in by_name:
            by_name[name] = (path, _workflow_triggers(text))
    problems: list[str] = []
    for wanted in cfg.pr_automation.scan_workflows:
        found = by_name.get(wanted)
        if found is None:
            continue
        path, triggers = found
        if not triggers.intersection(PULL_REQUEST_TRIGGERS):
            problems.append(
                f"pr_automation.scan_workflows names {wanted!r} ({path.relative_to(cfg.root)}), "
                "which has no `pull_request` or `pull_request_target` trigger and can never "
                "complete for a pull request — this permanently blocks the gate"
            )
    return ScanWorkflowReport(tuple(problems))


def _check(raw: dict[str, Any]) -> Check:
    return Check(
        name=str(raw.get("name") or raw.get("context") or "unnamed check"),
        status=str(raw.get("status") or "COMPLETED").upper(),
        conclusion=(str(raw["conclusion"]).upper() if raw.get("conclusion") else None),
        url=str(raw.get("detailsUrl") or raw.get("targetUrl") or ""),
    )


def newest_per_name(rollup: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """One entry per check name: the most recently started run of it.

    A rollup carries EVERY check run for the head, not the current one per name. When
    concurrency cancels a superseded run, its jobs stay in the rollup as CANCELLED beside
    the successful jobs of the run that replaced them — same head, same names, two verdicts.
    Counting both reads as "cancelled or stale checks require a rerun", and the pull request
    sits blocked with nothing wrong and nothing to fix but a manual rerun of a workflow that
    already succeeded. Cancelling a superseded run is ordinary, so this was ordinary too.

    Deduplicating by name keeps the exact-head guarantee: every entry still belongs to this
    head. It drops only the older of two runs OF THE SAME CHECK, which is precisely the
    stale evidence the check was refusing to trust.

    Entries with no timestamp sort oldest, so a real result always displaces a placeholder.
    """
    newest: dict[str, dict[str, Any]] = {}
    for item in rollup:
        name = str(item.get("name") or item.get("context") or "unnamed check")
        current = newest.get(name)
        if current is None or _started(item) >= _started(current):
            newest[name] = item
    return list(newest.values())


def _started(raw: dict[str, Any]) -> str:
    return str(raw.get("startedAt") or raw.get("completedAt") or "")


def parse_state(comments: Sequence[dict[str, Any] | str]) -> AutomationState | None:
    """Return the newest valid state marker, ignoring ordinary or malformed comments."""
    data = github_state.parse_payload(comments, _STATE_RE)
    if data is None:
        return None
    try:
        return AutomationState(
            lineage_sha=str(data["lineage_sha"]),
            current_sha=str(data["current_sha"]),
            attempts=int(data.get("attempts", 0)),
            review_sha=data.get("review_sha"),
            review_passed=data.get("review_passed"),
            replacement_pr=data.get("replacement_pr"),
            heals=int(data.get("heals", 0)),
            history=list(data.get("history", [])),
        )
    except (KeyError, TypeError, ValueError):
        return None


def state_body(state: AutomationState, summary: str) -> str:
    return github_state.render_body(STATE_MARKER, asdict(state), "Vibey GH PR automation", summary)


def _labels(pr: dict[str, Any]) -> set[str]:
    return {
        str(label.get("name", "")) if isinstance(label, dict) else str(label)
        for label in pr.get("labels") or []
    }


def repair_refspec(branch: str) -> str:
    """Build an update-only refspec; deletion refspecs have an empty source before `:`."""
    if not branch or ":" in branch or branch.startswith("-"):
        raise ValueError(f"unsafe repair branch {branch!r}")
    return f"HEAD:refs/heads/{branch}"


def _trusted(pr: dict[str, Any], cfg: GhConfig) -> bool:
    if EXTERNAL_REPAIR_LABEL in _labels(pr):
        return False
    actor = normalise_actor(str((pr.get("author") or {}).get("login", "")))
    trusted = {normalise_actor(value) for value in cfg.trusted_authors}
    if cfg.owner:
        trusted.add(normalise_actor(cfg.owner))
    return actor in trusted


def lineage_for(stored: AutomationState | None, head: str) -> AutomationState:
    """The state that applies to `head`, starting a new lineage when it has moved on.

    `current_sha` tracks the last head automation itself produced or evaluated, so a head
    that differs from it arrived from a human. That starts a fresh attempt budget — which
    is the documented contract, and was previously computed by `evaluate` and then thrown
    away, because the persisting path built its own state and never applied the same rule.
    Both callers share this so the decision and the record cannot disagree again.
    """
    if stored is None or stored.current_sha != head:
        return AutomationState(
            lineage_sha=head,
            current_sha=head,
            history=list(stored.history) if stored else [],
        )
    return stored


def evaluate(
    pr: dict[str, Any],
    cfg: GhConfig,
    *,
    expected_sha: str,
    stored: AutomationState | None = None,
) -> Evaluation:
    """Classify one exact PR head without mutating GitHub."""
    number = int(pr["number"])
    head = str(pr.get("headRefOid") or "")
    base = str(pr.get("baseRefName") or cfg.integration_branch)
    author = str((pr.get("author") or {}).get("login", ""))
    trusted = _trusted(pr, cfg)

    def result(state: str, reason: str, **kw: Any) -> Evaluation:
        return Evaluation(number, head, base, author, trusted, state, reason=reason, **kw)

    if head != expected_sha:
        return result("blocked", f"stale event for {expected_sha}; current head is {head}")
    if pr.get("state", "OPEN") != "OPEN":
        return result("blocked", "pull request is not open")
    state = lineage_for(stored, head)

    # An outside contributor must not be able to steer automation at a permanent branch,
    # by any route. GitHub already refuses them write access, so this is defence in depth
    # against the shapes that would slip past it: a pull request whose HEAD is a permanent
    # branch (whose repair push would land there), and one aimed straight at the release
    # branch (which must only ever receive a promotion). Both are terminal, so no review,
    # repair, conflict resolution, or gate ever runs for them.
    permanent = {cfg.integration_branch, cfg.release_branch, "develop", "main"}
    if not trusted:
        head_ref = str(pr.get("headRefName") or "")
        if head_ref in permanent:
            return result("blocked", f"an outside author may not propose from {head_ref}")
        if base in {cfg.release_branch, "main"}:
            return result(
                "blocked",
                f"an outside author may not target {base}; open it against "
                f"{cfg.integration_branch} instead",
            )

    labels = _labels(pr)
    if BLOCKED_LABEL in labels:
        return result("blocked", "automation is blocked pending operator action")
    if EXHAUSTED_LABEL in labels:
        return result("blocked", "repair budget is exhausted")

    draft = bool(pr.get("isDraft"))
    # A conflict is a property of the branch against its base, not of review readiness, so
    # it is classified before the draft short-circuit. Leaving it after strands a
    # conflicted draft forever: `ready_draft` refuses to promote it *because* it
    # conflicts, and conflict resolution never runs *because* it is a draft — and every
    # branch-intake and issue-solution pull request starts as a draft. No gate is
    # published for `conflict`, so this stays within the rule that a draft never
    # publishes a failing gate.
    #
    # Fork drafts remain excluded. Their conflict path opens a repository-owned
    # replacement and closes the original, which must never happen to a contributor's
    # work in progress.
    if pr.get("mergeable") == "CONFLICTING" and not (draft and pr.get("isCrossRepository")):
        if state.attempts >= cfg.pr_automation.max_repair_attempts:
            return result(
                "blocked",
                "conflict resolution budget is exhausted",
                repair_attempt=state.attempts,
            )
        return result(
            "conflict",
            f"conflicts with {base}",
            failed_checks=(f"Merge conflict with {base}",),
            repair_attempt=state.attempts + 1,
        )
    if draft:
        # Draft intake is otherwise nonterminal. `ready_draft` promotes the exact head
        # once its scans are stable; until then no failing gate may be published.
        return result("pending", "pull request is a draft awaiting a stable head")
    if pr.get("reviewDecision") == "CHANGES_REQUESTED":
        return result("blocked", "a human requested changes")

    ignored = set(cfg.pr_automation.ignored_checks) | OWN_CHECKS
    checks = [_check(item) for item in newest_per_name(pr.get("statusCheckRollup") or [])]
    checks = [item for item in checks if item.name not in ignored]
    if not checks:
        return result("pending", "no current-head scan results are available")
    pending = tuple(item.name for item in checks if item.status != "COMPLETED")
    if pending:
        return result("pending", "checks are still running", pending_checks=pending)

    operational = tuple(item.name for item in checks if item.conclusion in OPERATIONAL)
    if operational:
        return result(
            "blocked",
            "cancelled or stale checks require a rerun",
            failed_checks=operational,
        )

    failed = tuple(item.name for item in checks if item.conclusion in FAILING)
    if failed:
        if state.attempts >= cfg.pr_automation.max_repair_attempts:
            return result(
                "blocked",
                "repair budget is exhausted",
                failed_checks=failed,
                repair_attempt=state.attempts,
            )
        if not trusted and not cfg.pr_automation.repair_untrusted_authors:
            return result(
                "blocked", "repairs for untrusted authors are disabled", failed_checks=failed
            )
        return result(
            "repair",
            "completed checks are failing",
            failed_checks=failed,
            repair_attempt=state.attempts + 1,
        )

    # Every author's exact head is reviewed — the documentation audit is repository-wide,
    # and only the *scope* of the review widens for an outside author. A head that has
    # never been reviewed always gets one, even once the repair budget is fully spent:
    # dispatching a review costs nothing (the budget counts repairs, not reviews), and a
    # verdict recorded for an older head must never stand in for a review of the head that
    # exists now — that substitution is exactly what escalated a fixed pull request as
    # unrepairable. Only a CURRENT review's own actionable findings may spend another
    # attempt, so the budget check sits immediately before that spend, mirroring the
    # check-failure branch above. It is still reachable and still finite: every head
    # advance is itself produced by a repair, and repairs are capped by this same budget.
    reviewable = trusted or cfg.pr_automation.review_untrusted_authors
    if reviewable:
        if state.review_sha != head:
            return result("review", "current head requires automated review")
        if state.review_passed is not True:
            if state.attempts >= cfg.pr_automation.max_repair_attempts:
                return result(
                    "blocked", "review repair budget is exhausted", repair_attempt=state.attempts
                )
            return result(
                "repair",
                "automated review has actionable findings",
                failed_checks=("Automated review",),
                repair_attempt=state.attempts + 1,
            )

    return result("ready", "all scans and applicable reviews passed")


_gh_json = github_state.gh_json


def fetch_pr(number: int) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        _gh_json(
            "pr",
            "view",
            str(number),
            "--json",
            "number,title,state,isDraft,mergeable,mergeStateStatus,reviewDecision,"
            "statusCheckRollup,author,labels,comments,headRefOid,headRefName,headRepository,"
            "headRepositoryOwner,isCrossRepository,baseRefName,body",
        ),
    )


def evaluate_pr(number: int, head_sha: str, cfg: GhConfig) -> Evaluation:
    pr = fetch_pr(number)
    return evaluate(pr, cfg, expected_sha=head_sha, stored=parse_state(pr.get("comments") or []))


def ready_draft(number: int, head_sha: str, cfg: GhConfig) -> dict[str, Any]:
    """Promote one exact, green draft head; every unstable condition is a no-op."""
    pr = fetch_pr(number)
    if str(pr.get("headRefOid") or "") != head_sha:
        return {"promoted": False, "reason": "stale head"}
    if pr.get("state", "OPEN") != "OPEN" or not pr.get("isDraft"):
        return {"promoted": False, "reason": "not an open draft"}
    if pr.get("isCrossRepository"):
        return {"promoted": False, "reason": "fork drafts are not mutated"}

    candidate = dict(pr)
    candidate["isDraft"] = False
    decision = evaluate(
        candidate,
        cfg,
        expected_sha=head_sha,
        stored=parse_state(pr.get("comments") or []),
    )
    if decision.state not in {"ready", "review"}:
        return {"promoted": False, "reason": decision.reason}

    run = subprocess.run(
        ["gh", "pr", "ready", str(number)], capture_output=True, text=True, check=False
    )
    if run.returncode:
        raise RuntimeError(f"could not mark PR ready: {run.stderr.strip()}")
    return {"promoted": True, "reason": "current head is stable"}


def updated_state(
    pr: dict[str, Any],
    payload: dict[str, Any],
    *,
    kind: str,
) -> AutomationState:
    current = parse_state(pr.get("comments") or [])
    head = str(payload.get("head_sha") or pr.get("headRefOid") or "")
    if kind == "review":
        # A review is recorded for the exact head just evaluated, so this is the one
        # record that can tell a human push apart from an automation repair — a repair
        # advances `current_sha` to its own new head as it is recorded, leaving them
        # equal. Applying the reset here is what finally persists a new lineage.
        state = lineage_for(current, head)
        state.review_sha = head
        state.review_passed = bool(payload.get("pass"))
    elif kind == "repair":
        state = current or AutomationState(lineage_sha=head, current_sha=head)
        if payload.get("fixable") is not False:
            state.attempts += 1
        state.current_sha = head
        state.review_sha = None
        state.review_passed = None
    else:
        raise ValueError(f"unknown record kind: {kind}")
    state.history.append({"kind": kind, **payload})
    return state


def upsert_state(
    number: int, state: AutomationState, summary: str, comments: list[dict[str, Any]]
) -> None:
    github_state.upsert_comment(
        number,
        state_body(state, summary),
        comments,
        _STATE_RE,
        subject="pr",
        error="could not persist PR automation state",
    )


def record(number: int, payload: dict[str, Any], kind: str) -> AutomationState:
    pr = fetch_pr(number)
    state = updated_state(pr, payload, kind=kind)
    summary = str(payload.get("summary") or f"Recorded {kind} for `{state.current_sha}`.")
    upsert_state(number, state, summary, list(pr.get("comments") or []))
    return state


def exhausted_pull_requests(cfg: GhConfig) -> list[int]:
    """Every open pull request whose repair budget is spent."""
    listed = github_state.gh_json(
        "pr",
        "list",
        "--repo",
        github_state.repository(),
        "--state",
        "open",
        "--label",
        EXHAUSTED_LABEL,
        "--json",
        "number",
    )
    return [int(item["number"]) for item in listed or []]


def self_heal(number: int, cfg: GhConfig) -> dict[str, Any]:
    """Give an exhausted pull request one more bounded round of repair.

    A budget that can never be refilled turns a transient failure — an outage, an
    exhausted credit balance, a formatter the agent could not run — into a permanent stop
    that a human must notice. A budget that refills forever is no budget at all. So the
    refill is itself budgeted: `branch_sync.max_self_heals` bounds how many times one
    lineage may be revived, the count rides in the same durable state as the attempts, and
    once it is spent the pull request stays exhausted until a human intervenes.
    """
    pr = fetch_pr(number)
    if EXHAUSTED_LABEL not in _labels(pr):
        return {"pr": number, "healed": False, "reason": "not exhausted"}
    head = str(pr.get("headRefOid") or "")
    state = parse_state(pr.get("comments") or []) or AutomationState(
        lineage_sha=head, current_sha=head
    )
    if state.heals >= cfg.branch_sync.max_self_heals:
        return {
            "pr": number,
            "healed": False,
            "reason": f"self-heal budget of {cfg.branch_sync.max_self_heals} is spent",
        }
    state.heals += 1
    state.attempts = 0
    state.review_sha = None
    state.review_passed = None
    state.history.append({"kind": "self-heal", "head_sha": head, "heal": state.heals})
    summary = (
        f"Repair budget refilled automatically (self-heal {state.heals} of "
        f"{cfg.branch_sync.max_self_heals}). The previous attempts are retained above; "
        "if this round exhausts the budget again the pull request stays blocked for a human."
    )
    upsert_state(number, state, summary, list(pr.get("comments") or []))
    subprocess.run(
        [
            "gh",
            "pr",
            "edit",
            str(number),
            "--repo",
            github_state.repository(),
            "--remove-label",
            EXHAUSTED_LABEL,
        ],
        capture_output=True,
        check=False,
    )
    return {"pr": number, "healed": True, "heal": state.heals, "head_sha": head}


def ensure_labels() -> None:
    definitions = {
        EXTERNAL_REPAIR_LABEL: ("5319E7", "Repository-owned continuation of a fork PR"),
        REPAIRING_LABEL: ("FBCA04", "Automated scan repair is in progress"),
        EXHAUSTED_LABEL: ("D93F0B", "Automated repair budget is exhausted"),
        BLOCKED_LABEL: ("B60205", "Automation requires repository-operator action"),
    }
    for name, (colour, description) in definitions.items():
        subprocess.run(
            [
                "gh",
                "label",
                "create",
                name,
                "--color",
                colour,
                "--description",
                description,
                "--force",
            ],
            capture_output=True,
            check=False,
        )


def mirror_fork(number: int, cfg: GhConfig) -> dict[str, Any]:
    """Mirror an exact fork head and open a repository-owned replacement PR."""
    pr = fetch_pr(number)
    head = str(pr["headRefOid"])
    short = head[:12]
    branch = f"vibey-gh/repair/pr-{number}-{short}"
    refspec = repair_refspec(branch)
    owner = str((pr.get("headRepositoryOwner") or {}).get("login", ""))
    repo = str((pr.get("headRepository") or {}).get("name", ""))
    if not owner or not repo:
        raise RuntimeError("pull request does not expose a fork repository")
    fetch = subprocess.run(
        ["git", "fetch", "--quiet", f"https://github.com/{owner}/{repo}.git", head],
        cwd=cfg.root,
        capture_output=True,
        text=True,
        check=False,
    )
    if fetch.returncode:
        raise RuntimeError(f"could not fetch fork head: {fetch.stderr.strip()}")
    push = subprocess.run(
        ["git", "push", "origin", refspec.replace("HEAD", head, 1)],
        cwd=cfg.root,
        capture_output=True,
        text=True,
        check=False,
    )
    if push.returncode:
        raise RuntimeError(f"could not publish repair branch: {push.stderr.strip()}")
    author = sanitize(str((pr.get("author") or {}).get("login", "")), limit=100)
    title = sanitize(str(pr.get("title", "")), limit=200)
    body = (
        f"Repository-owned repair continuation of #{number} from @{author}.\n\n"
        f"Original head: `{head}`. The original contributor retains attribution; this branch "
        "exists only because privileged automation cannot write to a contributor fork."
    )
    create = subprocess.run(
        [
            "gh",
            "pr",
            "create",
            "--base",
            str(pr["baseRefName"]),
            "--head",
            branch,
            "--title",
            f"Repair #{number}: {title}",
            "--body",
            body,
        ],
        cwd=cfg.root,
        capture_output=True,
        text=True,
        check=False,
    )
    if create.returncode:
        raise RuntimeError(f"could not open replacement pull request: {create.stderr.strip()}")
    replacement = int(re.sub(r"\D", "", create.stdout.rsplit("/", 1)[-1]))
    subprocess.run(
        ["gh", "pr", "edit", str(replacement), "--add-label", EXTERNAL_REPAIR_LABEL],
        cwd=cfg.root,
        capture_output=True,
        check=False,
    )
    subprocess.run(
        [
            "gh",
            "pr",
            "comment",
            str(number),
            "--body",
            f"Repairs continue in #{replacement}; closing this fork PR only after preserving its exact head and attribution.",
        ],
        cwd=cfg.root,
        capture_output=True,
        check=False,
    )
    subprocess.run(
        ["gh", "pr", "close", str(number)], cwd=cfg.root, capture_output=True, check=False
    )
    return {
        "original_pr": number,
        "replacement_pr": replacement,
        "branch": branch,
        "head_sha": head,
    }
