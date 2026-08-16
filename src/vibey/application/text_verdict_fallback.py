"""TRIVIAL-effort extraction fallback (handoff-protocol.md §3.3): for
engines that cannot produce structured output, a cheap extraction pass
parses the free-text turn into the same verdict schema structured engines
return natively, so extract_events() never needs to know which path a
turn came from.

No live model access was available while building this, so this is a
deterministic heuristic parser rather than the real TRIVIAL-effort model
call the design calls for -- it recognizes a small set of line-prefix
conventions (`Question:`, `Decision:`, `Assumption:`, `Remaining:`,
`Done.`) rather than genuinely understanding prose. It is the seam a real
cheap-model extraction call would replace without touching
extract_events() or anything downstream of it.
"""

import re
from collections.abc import Mapping

_PREFIXES: tuple[tuple[str, str], ...] = (
    (r"^\s*question:\s*", "question"),
    (r"^\s*decision:\s*", "decision"),
    (r"^\s*assumption:\s*", "assumption"),
    (r"^\s*remaining:\s*", "remaining"),
    (r"^\s*blocked:\s*", "blocked"),
)


def extract_verdict_from_text(text: str) -> dict[str, object]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    questions: list[Mapping[str, object]] = []
    decisions: list[Mapping[str, object]] = []
    assumptions: list[Mapping[str, object]] = []
    remaining_work: list[str] = []
    blocked_on: str | None = None
    summary_lines: list[str] = []
    complete = "done." in text.lower() or "task complete" in text.lower()

    for line in lines:
        matched = False
        for pattern, label in _PREFIXES:
            match = re.match(pattern, line, re.IGNORECASE)
            if not match:
                continue
            body = line[match.end() :].strip()
            matched = True
            if label == "question":
                blocking = "?" in body and body.lower().startswith(("must", "need", "required"))
                questions.append({"text": body, "blocking": blocking})
            elif label == "decision":
                title, _, rationale = body.partition(" because ")
                decisions.append(
                    {
                        "title": title.strip(),
                        "choice": title.strip(),
                        "rationale": rationale.strip(),
                        "alternatives": [],
                    }
                )
            elif label == "assumption":
                assumptions.append({"text": body, "confidence": "medium"})
            elif label == "remaining":
                remaining_work.append(body)
            else:
                blocked_on = body
            break
        if not matched:
            summary_lines.append(line)

    return {
        "complete": complete,
        "remaining_work": remaining_work,
        "blocked_on": blocked_on,
        "summary": " ".join(summary_lines).strip(),
        "questions": questions,
        "decisions": decisions,
        "assumptions": assumptions,
        "artifacts": [],
    }
