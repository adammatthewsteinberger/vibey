---
name: flightsw-fdir-time-telemetry-and-updates
description: "Use when designing the operational behaviour of a spacecraft: fault detection, isolation and recovery including safe modes and the escalation ladder, time and clocks (onboard time, correlation, leap seconds, drift), command and telemetry design with CCSDS packets, and data handling, onboard storage and the in-flight software update path with its rollback requirements."
---

# Flight Software: FDIR, Time and Clocks, Command and Telemetry, and In-Flight Update

> **Part 3 of 5** of the *Flight Software* reference (plugin `flight-software`), covering §8–§11. Sibling skills: `flightsw-architecture-languages-and-standards` (§0–§3), `flightsw-processors-radiation-and-real-time` (§4–§7), `flightsw-gnc-verification-ground-and-autonomy` (§12–§16), `flightsw-reference` (§17–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The discipline and standards are stable; flight processors and framework releases moved materially in 2025-26. See §17 → `flightsw-reference` for what is dated and what is genuinely contested.

> **How to read this.** This is the deep treatment of flight software. It supersedes the
> compressed flight-software section in a robotics-software reference; **spacecraft systems
> engineering is in a space-exploration reference, and launch physics in a rocket-science
> reference.**
>
> Two markers:
> - **[DURABLE]** — the discipline, architecture, and standards. Most of this.
> - **[CONTESTED]** — genuine disagreement.
>
> **⚠️ GOTCHA** boxes mark what has actually destroyed vehicles.
>
> **The three properties that make this domain different from all other software:**
> 1. **⚠️ You cannot patch your way out.** Uplink is bandwidth-limited, latency-bound, and
>    sometimes impossible. **A bug that bricks the receiver ends the mission** — which is
>    why §11's update mechanism is designed before the software it updates.
> 2. **⚠️ The hardware is actively hostile.** Radiation flips bits in RAM and registers
>    with no warning and no error signal. **Software must assume its own memory is
>    corrupting underneath it** (§4 → `flightsw-processors-radiation-and-real-time`, §5 → `flightsw-processors-radiation-and-real-time`).
> 3. **⚠️ Correct-but-late is wrong.** A control loop that misses its deadline has failed
>    regardless of the answer it eventually produces. **Determinism outranks throughput,
>    and this inverts almost every instinct from server-side engineering** (§6 → `flightsw-processors-radiation-and-real-time`).

---

## §8. FDIR

**[DURABLE] Fault Detection, Isolation and Recovery — the organizing principle of flight
software, not a feature of it.**

```
DETECT     limit checks, watchdogs, consistency checks, checksums,
           heartbeat monitors, plausibility tests
   ↓
ISOLATE    determine which component; ⚠️ avoid misattribution — the hardest step
   ↓
RECOVER    retry → reconfigure to redundant unit → reset component
           → reset processor → ⚠️ SAFE MODE
```

**⚠️ Safe mode is the design that saves missions.** Power-positive, thermally stable,
Sun- or Earth-pointed, minimal software, **and survivable indefinitely awaiting ground
instruction.** **Every deep-space mission enters safe mode. The design question is not
whether, but whether it can sit there for a month without degrading.**

**Command loss timer**: ⚠️ **if no valid command is received for N days, assume something
is wrong with the receive chain and autonomously reconfigure** — swap receivers, swap
antennas, reset. **This has recovered missions whose primary receiver failed**, and it is
a mandatory feature, not a nicety.

**⚠️ The hard-won lessons of FDIR design:**
- **⚠️ Fault protection that misfires is itself a hazard.** A spurious safe-mode entry
  during orbit insertion or EDL can lose the mission. **Critical sequences therefore
  inhibit selected fault responses** — and choosing which is a genuinely difficult
  engineering judgement.
- **Don't recover into the fault.** Repeated automatic resets that re-trigger the same
  condition burn power and can exhaust a resource. **Escalate, and count.**
- **⚠️ Log everything before acting.** The telemetry that explains a fault is often lost in
  the recovery that follows it. **Persist diagnostics first.**
- **Distinguish transient from persistent.** A single SEU-induced anomaly should not
  trigger the same response as a failed component.

---

## §9. Time and Clocks

**[DURABLE] Getting time wrong is a classic and expensive failure mode.**

**Time scales**: **TAI** (atomic, continuous — ⚠️ **what you want onboard**), **UTC**
(⚠️ **has leap seconds; do not use it as an onboard timebase**), **GPS time** (continuous,
offset from TAI by 19 s), **spacecraft elapsed time (SCET/MET)** — ⚠️ **a free-running
onboard counter, which is the actual reference for onboard operations.**

**⚠️ Clock correlation** is the operational task: relating the onboard counter to ground
time using radiometric measurements, and tracking **drift and drift rate**. Every
science observation timestamp depends on it.

**⚠️ The specific hazards:**
- **Leap seconds** — ⚠️ **a repeated or skipped second breaks naive monotonic
  assumptions.** Multiple terrestrial outages have been caused by this; **don't inherit
  the problem onboard.**
- **Counter rollover** — ⚠️ **a 32-bit millisecond counter wraps in 49.7 days.** The
  Patriot missile timing failure and several spacecraft anomalies trace to accumulated or
  wrapped counters. **Compute the wrap interval explicitly and handle it.**
- **Light-time correction** — a command's execution time and an observation's timestamp
  are in different frames; ⚠️ **one-way light time to Mars is 3–22 minutes.**
- **Relativistic corrections** — ⚠️ **GPS requires them (about 38 μs/day net); for precision
  deep-space navigation they are not optional.**

---

## §10. Command and Telemetry

**[DURABLE] CCSDS is the international standard set, and it is genuinely worth following
rather than inventing.**

**The stack:**
```
Application:  ⚠️ Space Packet Protocol (CCSDS 133.0-B) — APID identifies the destination
Transfer:     TM/TC Space Data Link, or AOS for higher rates
Coding:       Reed-Solomon, convolutional, ⚠️ turbo/LDPC (near-Shannon)
Physical:     RF, per a space-exploration reference §5
```

**Telecommand**: **CLTU** framing, ⚠️ **COP-1 (Communications Operations Procedure)
providing sequence-controlled, guaranteed-delivery command transfer** — with a **FARM/FOP
state machine** that is a genuine source of operational subtlety.

**⚠️ Command design principles that matter operationally:**
- **Idempotent where possible** — ⚠️ **a retransmitted command should not do the thing
  twice.**
- **Two-stage arm/fire for hazardous commands** (deployments, pyros, engine starts).
- **Validate before execute**: checksum, authenticate (⚠️ **command authentication is now
  standard, and CCSDS SDLS provides it — an unauthenticated uplink is a hijack risk**),
  and range-check every parameter.
- **⚠️ Reject, don't clamp.** Silently clamping an out-of-range parameter hides the ground
  error that produced it.
- **Absolute and relative time-tagged sequences** — the backbone of deep space ops.

**Telemetry**: **housekeeping** (periodic state), **event/EVR messages** (⚠️ **the
spacecraft's log, and your only debugger**), **science**, **diagnostic dwell** (⚠️ **read
arbitrary memory addresses — indispensable for in-flight debugging**).

**⚠️ Design telemetry for the anomaly you haven't had yet.** The recurring operational
regret is insufficient telemetry to diagnose a fault after it occurs. **Budget bandwidth
for diagnostics, include mode and state transitions, and make everything you'd want during
a 3 a.m. anomaly call reachable without a patch.**

---

## §11. Data Handling and In-Flight Update

**Onboard storage**: ⚠️ **flash wear-levelling and radiation-induced corruption both
apply**; use **journaling or log-structured** approaches, checksum everything at rest, and
plan for **data prioritization** — when downlink is scarce, what gets dropped is a mission
decision that must be encoded.

**⚠️ CFDP (CCSDS File Delivery Protocol)** — reliable file transfer across a link with
**huge latency, intermittent connectivity, and asymmetric rates.** **Class 1
(unacknowledged) and Class 2 (acknowledged with retransmission).** It is the right answer
and it is worth using rather than rolling your own.

**⚠️ In-flight software update is the highest-stakes operation in the discipline.**
```
Design rules, each written in blood:
  1. ⚠️ The bootloader must be immutable, or dual-redundant with a golden image
  2. Uplink to inactive memory, verify checksum, THEN switch
  3. ⚠️ Automatic rollback on failure to check in after N minutes
  4. Never patch the receive chain and the patch mechanism at once
  5. ⚠️ Test the exact uplink product on the exact testbed configuration (§13.3)
  6. Patch granularity small enough to fit the uplink budget
```
**⚠️ A failed update that bricks the command receiver is unrecoverable and has ended
missions.** This is why rule 1 exists.

**⚠️ The counterexample worth knowing**: Voyager received a software patch in 2023–24 to
work around degraded memory **46 years after launch**, on a system whose original
engineers had retired or died. **That is only possible because the update path was
designed conservatively from the start.**
