# 0006 — A normalized effort ladder with saturating per-engine projection

**Status:** accepted · **Date:** 2026-08-14

**Owes:** nothing — mechanism (ADR-0020)

## Context

The requirement is that Phase 1 and 3 use high-effort models and Phase 2 uses
low-effort ones. But the engines do not share an effort vocabulary. Verified from
their sources and, since 2026-08-18, against each installed binary's `run --help`
by the conformance suite's `flags` check:

| Engine | Effort model |
|---|---|
| `claudeloop` | `Literal["low","medium","high","xhigh","max"]` + `low/medium/high` presets |
| `codexloop` | internal `Effort.MEDIUM` default and **no launch-time effort flag** — `run` accepts only `--run-id/--transport/--model/--max-turns/--max-wait/--stream-ui`; effort changes only through a mid-run `SetEffort` event |
| `cursorloop` | **no effort concept at all** — a ladder of model ids (`composer-fast → composer → grok-4.5 → grok → grok-xhigh`) |
| `agyloop` | `Literal["low",…,"max"]` + presets, Gemini aliases |
| `qwenloop` (opt-in, [ADR-0015](0015-qwenloop-standby.md)) | **no effort concept** — projected onto a turn budget, `--max-turns` 8 → 16 → 40 → 64 → 96 |

A design that passes `--effort high` through uniformly breaks the first time the
rotator picks `cursorloop`. The first version of this record itself assumed
codexloop took `--effort`; it does not, and every real codexloop invocation would
have failed at argument parsing until conformance caught it.

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
# codexloop — no CLI-level effort control; every level achieves STANDARD
Effort.MAX: EngineInvocation((), achieved=Effort.STANDARD,
                             notes="codexloop has no CLI-level effort control")
# cursorloop
Effort.MAX: EngineInvocation(("--model","grok-xhigh"), achieved=Effort.MAX)
# qwenloop
Effort.MAX: EngineInvocation(("--max-turns","96"), achieved=Effort.MAX)
```

The projections are data in `infrastructure/engines/descriptors.py`; the only code
that turns one into a command line is `infrastructure/engines/argv.py`.

## Rationale

Saturation is **surfaced, not hidden**. An engine that cannot deliver `MAX` is
still eligible — refusing to use it when it is the only one with capacity would be
worse — but it carries a `fidelity_factor` of 0.7 or 0.5, which lowers its
rotation weight. So vibey *prefers* an engine that can genuinely do the work while
still *using* one that can't when that is the only option.

Operator surfaces should report the effort achieved, not the effort requested. This
is not yet surfaced: `vibey status` shows neither, although the `achieved` value is
on every `EngineInvocation`. Reporting the request would be a lie that compounds: a developer debugging a bad design
session needs to know it ran at `HIGH` on an engine that saturates, not that
`MAX` was asked for.

## Phase policy

| Phase | Base effort |
|---|---|
| DESIGN | `HIGH` |
| VISUAL_DESIGN (optional, ADR-0014) | `HIGH` |
| BUILD | `LOW` |
| REVIEW | `HIGH` |
| DEPLOY_DESIGN | `HIGH` |
| DEPLOY_EXECUTE | `LOW` |
| DEPLOY_REVIEW | `HIGH` |

The table is `domain/effort.py::PHASE_BASE_EFFORT`, which also keeps `LOW` for the
legacy single-phase `DEPLOY` bridge.

Phase 2's flat `LOW` would strand the one genuinely hard work item, so effort
escalates **per item** on verification failure: `LOW, LOW, STANDARD, STANDARD,
HIGH, HIGH` (`BUILD_LADDER`), then an `escalation_exhausted` human gate whose
answer can grant more attempts at the ladder's top effort
([ADR-0024](0024-every-bounded-ladder-parks-with-a-grant.md)). Each step up in
effort (attempts 3 and 5) also forces a rotation, so the
ladder tries *different engines at higher effort* rather than the same engine
trying harder. Escalation is checked against the budget cap *before* it happens,
because the ladder is the mechanism most likely to cause a cost snowball.

## Consequences

**Good.** Adding qwenloop — a fifth engine with yet another vocabulary
(`--max-turns`) — was one descriptor. The domain never learns what `--preset`
means. Golden-file tests (5 engines × 5 efforts = 25 argv fixtures in
`tests/infrastructure/engines/golden/`) catch a projection changing, and the
conformance `flags` check catches a runner changing its flags.

**Bad.** The mapping is a judgment call — is `grok-4.5` really "STANDARD"? — and
it will need tuning as models change. It is data in a descriptor, so tuning is a
one-line change, not a refactor.

**Bad.** An engine with no effort control, such as codexloop, is requested at
`MAX` and runs at its default. Its `fidelity_factor` (0.7 at `HIGH`, 0.5 at `MAX`)
makes the rotator prefer other engines for design and review work, but vibey
cannot make it try harder.

## Alternatives rejected

- **Pass `--effort` through uniformly.** Breaks the first time the rotator picks an
  engine with no effort flag — cursorloop, codexloop, or qwenloop.
- **Per-engine effort vocabularies in the domain.** The domain would learn every
  runner's flags and change every time one did, and `domain/` would stop being the
  stable core the layer map requires.
- **Refuse engines that saturate.** Leaves capacity idle exactly when it is
  scarcest. The fidelity factor prefers a capable engine without refusing the only
  available one.
