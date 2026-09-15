# Capacity Is Hardware: The Local Session Runner as the Fleet's Sovereign Fallback

**Abstract.** Four of the five runners in this family meter against vendor billing;
qwenloop meters against **physics**. Running Qwen 2.5 Coder locally (llama.cpp
Q5_K_M by default; BF16 via vLLM above 40 GiB of VRAM) replaces the window/credit
dichotomy with a hardware capacity model — VRAM, thermals, and throughput are the
quota, and nobody refills them by adding a payment method. We present the local
instantiation of the family core and its distinct role: because its capacity is
sovereign — no vendor can cap it — qwenloop is the substrate of the fleet's entire
degraded-mode doctrine: the local review fallback, the local-authority period, and
the agent-failover seat all run on it. Model acquisition is always explicit: the
package, tests, doctor, and orchestrator integration never download weights, because
a surprise 9 GB download is a capacity event on exactly the constrained hardware
this runner exists to respect.

## Introduction

The transplant thesis (the claudeloop paper) predicts vendor variance lands in
lexicons and transports. qwenloop is its boundary case: there is no vendor. The
"failure text" is the operating system's — out-of-memory, backend timeouts, a model
file absent — and the capacity verdict reads resources, not prose:

$$\kappa \in \{\mathsf{available},\ \mathsf{saturated},\ \mathsf{unprovisioned}\}$$

$\mathsf{saturated}$ (contended VRAM/CPU, thermal throttle) is the analogue of a
window — waitable, deadline-bounded, because load passes. $\mathsf{unprovisioned}$
(weights absent, backend missing, VRAM below the profile's floor) is the analogue of
credits — never waitable, and the doctor names the exact provisioning step instead.

```latex
\begin{invariant}[Explicit provisioning]
No component acquires model weights implicitly. Install is a human act the doctor
verifies; the package, tests, and orchestrator integration operate fully with
weights absent, degrading to honest \textsf{unprovisioned} verdicts.
\end{invariant}
```

## Profiles as capacity contracts

A profile binds a quantization to a hardware floor — the default is a portable
llama.cpp Q5_K_M profile; BF16 through vLLM is admitted only on Linux/NVIDIA systems
with $\geq 40$ GiB usable VRAM. Profiles make the capacity model checkable BEFORE a
run: doctor proves the floor, and a run admitted under a profile inherits an honest
$\kappa$.

## The sovereign-fallback role

```latex
\begin{theorem}[Sovereignty]
No external party can revoke qwenloop's capacity: it is bounded by owned hardware
alone. Consequently the fleet's availability floor equals the local lane's, and
every credit-exhaustion doctrine reduces to a handoff onto this runner.
\end{theorem}
```

This is not hypothetical: the family's degraded-mode stack — the constrained-decoding
review fallback, the local-authority sync period, and the opencode agent-failover
seat — runs on this substrate, and carried an entire release train (vibey-gh 1.56.0,
vibey 0.3.0) through a live vendor-credit outage on 2026-08-29. The complementary
doctrine holds too: the laptop hosting this sovereignty is itself never a guarantee,
so cloud schedules remain the recovery engine when the local machine sleeps.

## The shared core

Unchanged: bounded runs under the explicit bound vector; never blocking on stdin;
resumption from the append-only ledger alone; completion only by agreeing evidence
under capacity-outranks-completion — a starved local model confabulates completion
exactly as a starved hosted one does.

## References

- claudeloop, *The Transplantable Session Runner*, companion paper, 2026.
- vibey-gh issues #206–#210: the degraded-mode and no-guarantees doctrines this runner anchors, 2026.
- This repository: the capability matrix and doctor documentation, 2026.
