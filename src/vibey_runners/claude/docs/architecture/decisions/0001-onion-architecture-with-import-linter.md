# ADR 0001: Onion architecture, enforced by import-linter

## Status

Accepted. Implemented in M1.

## Context

The legacy `claude_autoresume.py` is a single 674-line file mixing regex
parsing, subprocess I/O, CLI argument handling, and the actual limit/retry
decision logic in one flat namespace. That's fine for a script one person
runs, but it makes the hardest-to-get-right logic — is this limit waitable?
how long do we wait? — untestable except by mocking `subprocess.Popen` and
inspecting captured stdout.

## Decision

Adopt a four-layer onion (`domain` → `application` → `infrastructure` →
`cli`, with `bootstrap.py` as the single composition root), and enforce the
dependency direction in CI with `import-linter` rather than relying on code
review to catch violations.

## Consequences

- Every decision with real consequences (capacity classification, wait
  scheduling, completion evaluation, budget tracking, the run-loop state
  machine) is a pure function in `domain/`, testable with plain dataclass
  literals and no I/O.
- A new contributor who imports `anthropic` inside `domain/` gets a specific,
  named CI failure ("Onion layering" or "Infrastructure only reachable from
  bootstrap") instead of a review comment days later.
- The cost is indirection: `cli/` never talks to `infrastructure/` directly,
  even when it would be one line shorter to do so. This is worth it
  specifically because the project's core value proposition — correctly
  distinguishing a waitable rate limit from a terminal credits exhaustion,
  and never blocking on a human — depends on that logic being exhaustively
  tested, and pure functions are the cheapest thing in Python to exhaustively
  test.

See [`../overview.md`](../overview.md) for the layer table and the enforced
contracts.
