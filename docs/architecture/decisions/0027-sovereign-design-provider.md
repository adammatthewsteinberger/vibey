# 0027 — A sovereign DESIGN provider: phase one runs without paid credit

**Status:** accepted · **Date:** 2026-08-30 (PR #120; operator-supplied evidence 51778876, the same day) · **Extends:** ADR-0015 · **Cites:** sub-doctrine 8.a

## Context

ADR-0015 admitted `qwenloop` as an opt-in standby: selected only when no eligible paid engine exists, so a zero-dollar descriptor does not crowd paid engines out of rotation. Doctrine 8.a, ratified afterwards, inverts the burden: the 100% sovereign path is *always* the preferred way to run, and paid is the move that must be justified.

Under that rule the tree had a contradiction. `EngineId.QWENLOOP` was wired as a BUILD executor, but DESIGN is phase one and its only live provider was `ClaudeLoopDesignProvider`. A project could not be started without paid credit; the "preferred" path was the one that could not go first. And `vibey doctor` could not even see the engine when the feature flag was on (#117) — a preferred path you cannot inspect is not a preferred path.

## Decision

**DESIGN has a sovereign provider, chosen explicitly: `--provider qwenloop` on `vibey work` and `vibey worker`.** `QwenloopDesignProvider` runs the interview batch and the spec synthesis against a local model.

- **It talks to Ollama's chat API directly, not to the `qwenloop` binary.** `qwenloop run` takes a plan file and `qwenloop prompt` needs an existing run id; neither is one-shot prompt-to-JSON. Going direct also buys **constrained decoding**: Ollama compiles the JSON schema to a grammar and zeroes any token that would break it, so malformed output is unreachable. The paid provider has to hunt for fences and strip prose; on output shape alone the weaker model is the more reliable of the two.
- **Decoders are shared, not imported from the paid path.** `design_json.py` holds them so the sovereign provider never depends on the paid one.
- **The floor is declared rather than worked around.** A local model has no web access, so `research()` never answers from recollection: returning a recollection with a `source` field would put a fabricated citation into a design spec, and a wrong answer that looks sourced survives review where a missing one does not. That is doctrine 10's floor, declared at the moment it is known. Because synthesis will not run until every research job succeeds, a provider that could only refuse would block the whole phase (measured on a live run), so the operator supplies the reading: `<topic>.md` in the directory named by `VIBEY_EVIDENCE_DIR`, whose first line must be `source: <where it came from>`. The model summarises that; the `source` is taken from the file, never minted; missing evidence, or evidence with no provenance line, raises `SovereignResearchUnavailable`. A sovereign fetcher remains an open option.
- **`doctor` and the worker share one notion of "enabled"** (environment first, then `[features] qwenloop`), so the health check and the dispatcher can never disagree about which engines exist.

## Consequences

**Good.** A project can be started, interviewed and specified with no counterparty who can raise a price or refuse service — 8.a made real for phase one. Verified against the live model, and the live run caught a real defect (constraints and NFRs folded into acceptance criteria) that the prompt now forbids.

**Bad.** Two DESIGN providers to keep at parity; the sovereign one researches only what the operator supplies; and ADR-0015's rotation posture (qwenloop only when nothing paid is eligible) now applies to BUILD rotation but not to the explicit DESIGN choice, which this record makes explicit rather than leaving implicit.

**Rule status.** The rule is 8.a and is already law; this ADR is the argument for how phase one satisfies it. The narrower clause — never emit a citation the model did not fetch — is conduct and may deserve its own sub-doctrine under doctrine 10.

## Alternatives rejected

- **Shell out to the `qwenloop` binary** for parity with BUILD. No one-shot JSON mode; loses constrained decoding; would need a plan file for what is a single exchange.
- **Let `research()` answer from the model's memory.** A fabricated citation in a spec is worse than a gap.
- **Make qwenloop the default DESIGN provider.** Not yet: research depends on operator-supplied evidence and the ledger-driven acceptance path has one live validation. Explicit selection keeps the choice a decision.
- **Leave DESIGN paid-only and call 8.a satisfied by BUILD.** Phase one is where a project begins; a preferred path that cannot go first is not preferred.
