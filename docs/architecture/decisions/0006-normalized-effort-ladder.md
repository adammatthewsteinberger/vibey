# 0006 — A normalized effort ladder with saturating per-engine projection

**Status:** accepted · **Date:** 2026-08-14

## Context

The requirement is that Phase 1 and 3 use high-effort models and Phase 2 uses
low-effort ones. But the four engines do not share an effort vocabulary. Verified
from their sources:

| Engine | Effort model |
|---|---|
| `claudeloop` | `Literal["low","medium","high","xhigh","max"]` + `low/medium/high` presets |
| `codexloop` | `StrEnum{LOW, MEDIUM, HIGH}` — three levels, no presets |
| `cursorloop` | **no effort concept at all** — a ladder of model ids (`composer-fast → composer → grok-4.5 → grok → grok-xhigh`) |
| `agyloop` | `Literal["low",…,"max"]` + presets, Gemini aliases |

A design that passes `--effort high` through uniformly breaks the first time the
rotator picks `cursorloop`.

## Decision

**Vibey's domain speaks its own five-level ladder and nothing else:**

```python
class Effort(IntEnum):
    TRIVIAL = 0; LOW = 1; STANDARD = 2; HIGH = 3; MAX = 4
```

Each `EngineDescriptor` provides an `effort_projection: Mapping[Effort,
EngineInvocation]` mapping vibey effort to native argv, and each `EngineInvocation`
declares the effort it **actually achieves** — which may be lower than requested.

```python
# codexloop
Effort.MAX: EngineInvocation(("--effort","high"), achieved=Effort.HIGH,
                             notes="saturates: no tier above high")
# cursorloop
Effort.MAX: EngineInvocation(("--model","grok-xhigh"), achieved=Effort.MAX)
```

## Rationale

Saturation is **surfaced, not hidden**. An engine that cannot deliver `MAX` is
still eligible — refusing to use it when it is the only one with capacity would be
worse — but it carries a `fidelity_factor` of 0.7 or 0.5, which lowers its
rotation weight. So vibey *prefers* an engine that can genuinely do the work while
still *using* one that can't when that is the only option.

`vibey status` reports the effort achieved, not the effort requested. Reporting
the request would be a lie that compounds: a developer debugging a bad design
session needs to know it ran at `HIGH` on an engine that saturates, not that
`MAX` was asked for.

## Phase policy

| Phase | Base effort |
|---|---|
| DESIGN | `HIGH` |
| BUILD | `LOW` |
| REVIEW | `HIGH` |

Phase 2's flat `LOW` would strand the one genuinely hard work item, so effort
escalates **per item** on verification failure: `LOW, LOW, STANDARD, STANDARD,
HIGH, HIGH`, then a human gate. Each escalation also forces a rotation, so the
ladder tries *different engines at higher effort* rather than the same engine
trying harder. Escalation is checked against the budget cap *before* it happens,
because the ladder is the mechanism most likely to cause a cost snowball.

## Consequences

**Good.** Adding a fifth engine with a sixth vocabulary is one descriptor. The
domain never learns what `--preset` means. Golden-file tests (4 engines × 5
efforts = 20 argv fixtures) catch a runner changing its flags.

**Bad.** The mapping is a judgment call — is `grok-4.5` really "STANDARD"? — and
it will need tuning as models change. It is data in a descriptor, so tuning is a
one-line change, not a refactor.
