# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Structured-verdict extraction: a turn's JSON verdict (handoff-protocol.md
§3.3) becomes closable ledger events with vibey-minted ids, deduplicated
against currently-open items by normalized text so an agent restating an
existing question across turns does not mint a second id."""

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import uuid4


class OpenItemKind(StrEnum):
    QUESTION = "question"
    DECISION = "decision"
    ASSUMPTION = "assumption"
    FINDING = "finding"


_ID_PREFIX = {
    OpenItemKind.QUESTION: "q",
    OpenItemKind.DECISION: "d",
    OpenItemKind.ASSUMPTION: "a",
    OpenItemKind.FINDING: "f",
}


@dataclass(frozen=True, slots=True)
class OpenItemRef:
    """The dedup surface: enough of an already-open item to match a new
    turn's restatement against, without needing the full ledger event."""

    item_id: str
    kind: OpenItemKind
    normalized: str


@dataclass(frozen=True, slots=True)
class ExtractedEvent:
    kind: str  # matches domain.ledger.EventKind values
    at: datetime
    payload: dict[str, object]


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    events: tuple[ExtractedEvent, ...]
    reused_ids: Mapping[str, str] = field(default_factory=dict)
    """text (as given by the agent) -> the existing item_id it deduped to."""


def normalize_text(text: str) -> str:
    """Lowercased, punctuation-stripped, whitespace-collapsed -- enough to
    catch an agent rewording the same question, not so aggressive that two
    different questions collide."""
    words = re.findall(r"\w+", text.lower())
    return " ".join(words)


def _mint_id(kind: OpenItemKind) -> str:
    return f"{_ID_PREFIX[kind]}_{uuid4().hex[:8]}"


def _find_open_match(
    text: str, kind: OpenItemKind, open_items: Sequence[OpenItemRef]
) -> OpenItemRef | None:
    target = normalize_text(text)
    for item in open_items:
        if item.kind is kind and item.normalized == target:
            return item
    return None


def extract_events(
    verdict: Mapping[str, object],
    *,
    open_items: Sequence[OpenItemRef],
    now: datetime,
) -> ExtractionResult:
    events: list[ExtractedEvent] = []
    reused: dict[str, str] = {}

    for question in _list_of_mappings(verdict.get("questions")):
        text = str(question.get("text", ""))
        existing = _find_open_match(text, OpenItemKind.QUESTION, open_items)
        if existing is not None:
            reused[text] = existing.item_id
            continue
        item_id = _mint_id(OpenItemKind.QUESTION)
        events.append(
            ExtractedEvent(
                kind="QuestionAsked",
                at=now,
                payload={
                    "question_id": item_id,
                    "text": text,
                    "blocking": bool(question.get("blocking", False)),
                    "asked_of": question.get("asked_of", "user"),
                },
            )
        )

    for decision in _list_of_mappings(verdict.get("decisions")):
        title = str(decision.get("title", ""))
        existing = _find_open_match(title, OpenItemKind.DECISION, open_items)
        if existing is not None:
            reused[title] = existing.item_id
            continue
        item_id = _mint_id(OpenItemKind.DECISION)
        events.append(
            ExtractedEvent(
                kind="DecisionRecorded",
                at=now,
                payload={
                    "decision_id": item_id,
                    "title": title,
                    "choice": decision.get("choice", ""),
                    "rationale": decision.get("rationale", ""),
                    "alternatives": _as_list(decision.get("alternatives", [])),
                },
            )
        )

    for assumption in _list_of_mappings(verdict.get("assumptions")):
        text = str(assumption.get("text", ""))
        existing = _find_open_match(text, OpenItemKind.ASSUMPTION, open_items)
        if existing is not None:
            reused[text] = existing.item_id
            continue
        item_id = _mint_id(OpenItemKind.ASSUMPTION)
        events.append(
            ExtractedEvent(
                kind="AssumptionStated",
                at=now,
                payload={
                    "assumption_id": item_id,
                    "text": text,
                    "confidence": assumption.get("confidence", "medium"),
                },
            )
        )

    for artifact in _list_of_mappings(verdict.get("artifacts")):
        events.append(
            ExtractedEvent(
                kind="ArtifactProduced",
                at=now,
                payload={
                    "artifact_id": f"art_{uuid4().hex[:8]}",
                    "kind": artifact.get("kind", ""),
                    "path": artifact.get("path", ""),
                },
            )
        )

    events.append(
        ExtractedEvent(
            kind="VerdictRendered",
            at=now,
            payload={
                "complete": bool(verdict.get("complete", False)),
                "remaining_work": _as_list(verdict.get("remaining_work", [])),
                "blocked_on": verdict.get("blocked_on"),
                "summary": str(verdict.get("summary", "")),
            },
        )
    )

    return ExtractionResult(events=tuple(events), reused_ids=reused)


def _list_of_mappings(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _as_list(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []
