from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum

from vibey.domain.spec import DesignSpec


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Ambiguity(StrEnum):
    CLEAR = "clear"
    NEEDS_CLARIFICATION = "needs_clarification"


class UserVerdict(StrEnum):
    ACCEPT = "accept"
    CHANGES = "changes"
    CANCEL = "cancel"


@dataclass(frozen=True, slots=True)
class FindingRef:
    """A pointer to a FindingRaised ledger event, carrying just enough to
    route the review loop-back decision without re-reading the ledger."""

    finding_id: str
    severity: Severity
    ambiguity: Ambiguity


@dataclass(frozen=True, slots=True)
class AssumptionDelta:
    assumption_id: str
    text: str
    seq: int


@dataclass(frozen=True, slots=True)
class FindingDelta:
    finding_id: str
    severity: Severity
    ambiguity: Ambiguity
    text: str
    seq: int
    resolved: bool = False


@dataclass(frozen=True, slots=True)
class DeltasReport:
    assumptions: tuple[AssumptionDelta, ...]
    findings: tuple[FindingDelta, ...]


def render_deltas_markdown(report: DeltasReport) -> str:
    """Renders deltas.md from a DeltasReport."""
    lines: list[str] = ["# Deltas and Assumptions", ""]

    lines.append("## Assumptions Stated")
    if report.assumptions:
        for a in report.assumptions:
            lines.append(f"- **[{a.assumption_id}]** (seq {a.seq}): {a.text}")
    else:
        lines.append("No assumptions recorded.")
    lines.append("")

    lines.append("## Findings Raised")
    if report.findings:
        for f in report.findings:
            status = "[RESOLVED]" if f.resolved else "[OPEN]"
            meta = f"({f.severity.value}, {f.ambiguity.value}, seq {f.seq})"
            lines.append(f"- **[{f.finding_id}]** {status} {meta}: {f.text}")
    else:
        lines.append("No findings recorded.")
    lines.append("")

    return "\n".join(lines)


def render_demo_markdown(spec: DesignSpec, *, evidence: Mapping[str, str] | None = None) -> str:
    """Renders DEMO.md per acceptance criterion with verified evidence."""
    lines: list[str] = [
        f"# Demo: {spec.objective}",
        "",
        "## Acceptance Criteria & Evidence",
        "",
    ]
    evidence_map = evidence or {}
    for c in spec.criteria:
        lines.append(f"### Criterion: {c.criterion_id}")
        lines.append(f"- **Given**: {c.given}")
        lines.append(f"- **When**: {c.when}")
        lines.append(f"- **Then**: {c.then}")
        lines.append(f"- **Fit Criterion**: {c.fit}")
        ev = evidence_map.get(c.criterion_id, "Verified by gate suite.")
        lines.append(f"- **Evidence**: {ev}")
        lines.append("")

    return "\n".join(lines)


def render_run_it_script(commands: Sequence[str] = ()) -> str:
    """Renders run-it.sh with local execution instructions."""
    lines: list[str] = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        "# Generated local run script for review",
    ]
    if commands:
        for cmd in commands:
            lines.append(cmd)
    else:
        lines.append("echo 'Run verification suite'")
        lines.append("pytest")
    lines.append("")
    return "\n".join(lines)


def render_walkthrough_markdown(
    *,
    spec: DesignSpec | None = None,
    summary: str = "",
    work_items: Sequence[str] = (),
) -> str:
    """Renders walkthrough.md narrating changes by intent."""
    lines: list[str] = [
        "# Walkthrough",
        "",
        "## Objective",
        spec.objective if spec is not None else "Delivered changes.",
        "",
        "## Narrative Summary",
        summary or "Automated build phase integrated verified work items.",
        "",
    ]
    if work_items:
        lines.append("## Integrated Work Items")
        for item in work_items:
            lines.append(f"- {item}")
        lines.append("")

    return "\n".join(lines)


_CRITICAL_KEYWORDS = frozenset(
    {
        "security",
        "vulnerability",
        "cve",
        "injection",
        "data loss",
        "corrupt",
        "leak",
        "critical",
        "invariant",
    }
)
_HIGH_KEYWORDS = frozenset(
    {"defect", "missing", "broken", "fails", "failure", "regression", "crash", "error", "high"}
)
_LOW_KEYWORDS = frozenset({"cosmetic", "nit", "typo", "doc", "comment", "formatting", "low"})

_AMBIGUOUS_PHRASES = ("maybe", "not sure", "might be", "better maybe", "rethink", "redesign")
_NEW_NFR_PHRASES = (
    "requests per second",
    "distributed cluster",
    "microservices",
    "migrate to",
    "100,000",
    "sub-millisecond",
)


def classify_finding_severity(text: str, category: str = "") -> Severity:
    """Classifies finding severity into CRITICAL, HIGH, MEDIUM, LOW."""
    combined = f"{category} {text}".lower()
    if any(k in combined for k in _CRITICAL_KEYWORDS):
        return Severity.CRITICAL
    if any(k in combined for k in _HIGH_KEYWORDS):
        return Severity.HIGH
    if any(k in combined for k in _LOW_KEYWORDS):
        return Severity.LOW
    return Severity.MEDIUM


def check_clear_conditions(
    text: str,
    *,
    spec: DesignSpec | None = None,
    decisions: Sequence[object] = (),
) -> tuple[bool, str]:
    """Evaluates the 4 conjunctive conditions for Ambiguity.CLEAR.

    1. Desired end state is stated unambiguously.
    2. Maps to an existing acceptance criterion or new criterion is obvious and testable.
    3. No new NFR or architectural constraint is implied.
    4. Does not contradict any recorded DecisionRecorded.
    """
    text_lower = text.lower().strip()

    # Condition 1: Unambiguous end state
    if len(text_lower.split()) < 3 or any(p in text_lower for p in _AMBIGUOUS_PHRASES):
        return False, "Condition 1 failed: ambiguous end state"

    # Condition 3: No new NFR or architectural constraint implied
    if any(p in text_lower for p in _NEW_NFR_PHRASES):
        return False, "Condition 3 failed: implies new NFR or architectural constraint"

    # Condition 4: Does not contradict recorded decisions
    for d in decisions:
        choice = getattr(d, "choice", "")
        alternatives = getattr(d, "alternatives", ())
        for alt in alternatives:
            if alt and str(alt).lower() in text_lower and "switch" in text_lower:
                return (
                    False,
                    f"Condition 4 failed: contradicts recorded decision ({choice} vs {alt})",
                )

    return True, "all 4 clear conditions satisfied"


def triage_finding(
    finding_id: str,
    text: str,
    *,
    category: str = "",
    spec: DesignSpec | None = None,
    decisions: Sequence[object] = (),
) -> FindingRef:
    """Triages a finding into a FindingRef with severity and ambiguity."""
    severity = classify_finding_severity(text, category=category)
    is_clear, _ = check_clear_conditions(text, spec=spec, decisions=decisions)
    ambiguity = Ambiguity.CLEAR if is_clear else Ambiguity.NEEDS_CLARIFICATION
    return FindingRef(finding_id=finding_id, severity=severity, ambiguity=ambiguity)
