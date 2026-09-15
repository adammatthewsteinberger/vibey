# 0015 — qwenloop is an opt-in local engine: a standby tier for BUILD, the sovereign provider for DESIGN

**Status:** accepted · **Date:** 2026-08-23 (PR #83) · **Rewritten:** 2026-09-15 · **Extended by:** PR #117 (doctor visibility, 2026-08-30) and ADR-0027 (the sovereign DESIGN provider, PR #120, 2026-08-30) · **In tension with:** sub-doctrine 8.a (ratified 2026-08-30) — see Consequences

## Context

Vibey's default engine pool is the four paid session runners — `claudeloop`, `codexloop`, `cursorloop`, `agyloop` (`domain/config.py::DEFAULT_ENGINES`, `infrastructure/engines/descriptors.py::DEFAULT_DESCRIPTORS`). BUILD jobs pick an engine per job by smooth weighted round-robin (ADR-0005) at job boundaries only (ADR-0007), over engines with a populated health record.

`qwenloop` is a fifth runner: an autonomous local Qwen2.5-Coder-14B agent, llama.cpp Q5_K_M by default and vLLM BF16 on Linux NVIDIA hosts with 40 GiB of free VRAM (its own ADR-0001, *dual local inference behind one port*; its ADR-0002 treats every model tool call as untrusted). It costs nothing per token, has no credits and no auth environment, runs a 32K context, and needs roughly ten gigabytes of weights that are never bundled with the package. On 2026-08-23 it was a separate repository; since 2026-09-10 (f958e2ca) it is a uv workspace member at `src/vibey_runners/qwen`, published on PyPI as `qwenloop`.

Four problems the decision had to solve:

1. **Parity in SWRR is not neutrality.** A fifth descriptor at `base_weight=1` takes one fifth of BUILD jobs by construction, and the selector's cost factor is disabled (`engine_selector.py:142`, `c_factor = 1.0`), so nothing would discount it. A 14B model at 32K context is not the equal of the paid engines at HIGH and MAX effort.
2. **Its failures are local.** Busy hardware, a missing model, a misconfigured backend. None is a provider credit event, and `CreditsExhausted` must never acquire a `resets_at` (CLAUDE.md non-negotiable).
3. **Weights are a download, not a check.** A health check that fetched them would turn `vibey doctor` into an outage-shaped surprise.
4. **Nobody had asked for it yet.** A default install should not carry a dormant engine whose preflight fails on every machine without the weights.

One week after this decision the operator ratified sub-doctrine **8.a — the sovereign path is the preference, not the fallback** (ad23469c, 2026-08-30). Doctrine 8 alone reads as an outage posture — local takes over *when the credits run out* — and 8.a says outright that this reading is wrong: sovereign is the ordinary posture and paid the exception that must be justified, the only justification being the doctrine-10 floor ("preferred until it provably cannot carry the work", declared loudly to a human). The same evening two PRs moved toward 8.a: #117 made `vibey doctor` show the engine whenever it is switched on ("a preferred path you cannot inspect is not a preferred path"), and #120 gave DESIGN — phase one — a sovereign provider, because until then a project could not be *started* without paid credit.

## Decision

**1. Off by default; one switch with two spellings.** `FeaturesConfig.qwenloop = False` (`domain/config.py:85-86`). `VIBEY_FEATURE_QWENLOOP` — `1`, `true`, `yes`, `on` — wins whenever it is set at all; otherwise `[features] qwenloop` decides (`bootstrap.py:234-239`; mirrored by `cli/main.py::_qwenloop_feature_enabled`, 240-257). Config validation refuses `qwenloop` in `[engines].enabled` or any `[phases.*].engines` until the feature is on, and when it is on and `[engines].enabled` is omitted, qwenloop is appended to the pool (`domain/config.py:280-283`).

**2. The same contract as every other engine.** `EngineDescriptor` `QWENLOOP` (`descriptors.py:240-264`): binary `qwenloop`, `min_version` 0.1.0, `state_dir` `.qwenloop` (runs live under `.qwenloop/runs/<run-id>/`), `done_marker` `QWENLOOP_TASK_FULLY_COMPLETE`, `auth_env=()`, every capability, effort projected to `--max-turns` 8/16/40/64/96, cost 0.0/0.0, context 32 768, `base_weight` 1. Graceful wind-down is the family-wide exit code 75 (`domain/engine.py::EXIT_CODE_WIND_DOWN`; `qwenloop/domain/model.py:8`). Loop events map `run.started`/`text_delta`/`tool_result`/`completed`/`failed` (`loop_events.py:165-171`). It is absent from `DEFAULT_DESCRIPTORS` and present in `ALL_DESCRIPTORS` and `BY_ENGINE_ID`.

**3. BUILD selection: a standby tier, not a pool member.** When enabled, the composition root adds `LoopProcessAdapter(descriptor=QWENLOOP)` and passes `standby_engine=EngineId.QWENLOOP` to `SelectingEngineProvider` (`bootstrap.py:266-268, 283`). On every selection the standby is preflighted (`qwenloop --version`, `qwenloop doctor`) and its health record refreshed with `conformance_ok = installed and auth_ok` (`engine_selection.py:124-133`). `EngineSelector` then keeps only paid runtimes among the eligible set, and qwenloop enters SWRR only when that set is empty (`engine_selector.py:107-111`). `vibey worker --engines qwenloop` narrows the allow-list to it and is the one way to force it today.

**4. Local failures are local.** `_classify_qwenloop` (`classify.py:119-132`): `busy` → `WindowExhausted(rate_limit_type="local")`, `configuration_error` → `AuthenticationFailed`, anything else → `Available`. The `credits_exhausted` shape exists only so the shared conformance fixtures can exercise it; the runtime never emits it.

**5. Nothing downloads weights except `qwenloop model install`.** Preflight and `doctor` run `--version` and `doctor` (`loop_process_adapter.py:186-215`); qwenloop's own `doctor` prints that it never downloads (`qwenloop/cli/app.py:265`).

**6. (PR #117) `vibey doctor` lists qwenloop whenever the feature is on**, using the same precedence as the worker, so the health check and the dispatcher can never disagree about which engines exist; a malformed `vibey.toml` reads as off (`cli/main.py:1079-1084`).

**7. (PR #120) DESIGN has a sovereign provider, chosen explicitly.** `--provider qwenloop` on `vibey work` and `vibey worker` selects `QwenloopDesignProvider` (`cli/main.py:371-380, 1370-1377`): Ollama's chat API at `127.0.0.1:11434`, model `qwen2.5-coder:14b`, schema-constrained decoding so malformed JSON is unreachable; `research()` raises `SovereignResearchUnavailable` rather than mint a citation unless `VIBEY_EVIDENCE_DIR` holds `<topic>.md` whose first line is `source: …`. This is not gated by the feature flag and is never selected automatically — a DESIGN provider is a CLI choice, default `scripted`. It is summarised here for completeness; its own decisions (Ollama-direct instead of the family binary, refuse rather than fabricate a source) are recorded in ADR-0027.

## Consequences

**What is standby-only today: BUILD.** The paid-first filter at `engine_selector.py:107-111` is doctrine 8's posture, written a week before 8.a inverted the burden of proof. Under 8.a, reaching for a paid engine is the move that must be justified; the only justification the canon allows is the doctrine-10 floor — the sovereign path *provably* cannot carry the work, and a human is told so at the moment it is known. The code declares nothing; it prefers paid silently. This ADR records that as an **open tension, not a settled decision**. Closing it is one of: (a) invert the filter — qwenloop first, a paid engine when a job's requirement exceeds the local floor (effort tier, context window, a measured local failure), with the reason written to the ledger; (b) keep the standby rule and file a sub-doctrine under doctrine 8 that names BUILD as a floor exception, because ADR-0020 says a standing rule lives in the canon or is not a rule; (c) make the posture a per-phase setting — `[phases.*].engines` already parses, and nothing reads it. Whichever it is, the parent doctrine and the wording are the operator's to ratify.

**What is preferred today: DESIGN, by the operator's explicit choice.** `--provider qwenloop` lets phase one run without paid credit, and the research floor is declared (`SovereignResearchUnavailable`) rather than worked around.

**The TOML switch does not reach the worker.** `bootstrap._qwenloop_enabled` reads `project.config` — the project record in Postgres — and `vibey new` writes only `project`, `max_cycle_dollars`, `max_cycle_turns`, `skills_context` into it (`cli/main.py:201-210`). `doctor` reads `./vibey.toml` directly (`cli/main.py:251-253`). `VIBEY_FEATURE_QWENLOOP` is the only switch that works in both places. Either `vibey new` learns to carry `[features]` into the record, or the reference documents say the env var is the switch.

**Every BUILD selection spawns `qwenloop doctor` when the feature is on**, bounded by the adapter's `doctor_timeout`. That is the price of a health record that is always current for an engine no cron populates.

**"A phase may allow only qwenloop" is not implemented.** `[phases.*].engines` is validated and ignored; `vibey worker --engines qwenloop` is what exists.

**Pricing plays no part.** With the cost factor disabled, the protection against crowding is the filter, not the descriptor's zero cost.

## Alternatives rejected

- **A fifth equal-weight pool member.** One fifth of BUILD jobs to a 14B/32K model, on a machine that may not even hold the weights. Rejected in #83.
- **Discounting instead of filtering** (`base_weight` 0, or a live cost factor). `base_weight` is an integer weight SWRR still cycles through, and the cost factor is off; a hard filter is deterministic and testable.
- **Always on.** Weights are not bundled; a preflight that fails on every fresh install would open a circuit and add noise to every rotation decision. Opt-in keeps the default install honest.
- **Mapping local failures onto credit exhaustion.** A busy GPU would trigger a handoff brief and the no-loss gate, and `CreditsExhausted` must never carry a `resets_at`.
- **Downloading weights from `doctor` or preflight.** A health check must not change the machine. `qwenloop model install` is the explicit, resumable, digest-verified path.
- **For DESIGN (#120): shelling to the `qwenloop` binary.** `qwenloop run` needs a plan file and `qwenloop prompt` needs a run id; neither is one-shot prompt-to-JSON, and Ollama's grammar-constrained decoding is the property that makes the weaker model the more reliable one on output shape. That choice sits uneasily with ADR-0017 (the family does it here); ADR-0027 argues it.
