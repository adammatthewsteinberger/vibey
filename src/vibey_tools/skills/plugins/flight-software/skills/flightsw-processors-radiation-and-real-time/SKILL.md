---
name: flightsw-processors-radiation-and-real-time
description: "Use when reasoning about the hardware the software runs on and its timing: flight processors and their performance and heritage trade-offs, radiation effects expressed in software terms (single-event upsets, latch-up, scrubbing, EDAC, watchdogs), real-time discipline including determinism, priority inversion and worst-case execution time, and RTOS choice and configuration."
---

# Flight Software: Flight Processors, Radiation Effects, Real-Time Discipline, and RTOS

> **Part 2 of 5** of the *Flight Software* reference (plugin `flight-software`), covering §4–§7. Sibling skills: `flightsw-architecture-languages-and-standards` (§0–§3), `flightsw-fdir-time-telemetry-and-updates` (§8–§11), `flightsw-gnc-verification-ground-and-autonomy` (§12–§16), `flightsw-reference` (§17–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    why §11 → `flightsw-fdir-time-telemetry-and-updates`'s update mechanism is designed before the software it updates.
> 2. **⚠️ The hardware is actively hostile.** Radiation flips bits in RAM and registers
>    with no warning and no error signal. **Software must assume its own memory is
>    corrupting underneath it** (§4, §5).
> 3. **⚠️ Correct-but-late is wrong.** A control loop that misses its deadline has failed
>    regardless of the answer it eventually produces. **Determinism outranks throughput,
>    and this inverts almost every instinct from server-side engineering** (§6).

---

## §4. Flight Processors

**[VERSIONED — this is the area that moved most, and it changes what software is
possible.]**

**⚠️ The historical situation**: flight computers are generations behind commercial silicon
because radiation-hardening and qualification take years. **The BAE RAD750 — a PowerPC
derivative at ~200 MHz — has been the enduring workhorse for nearly two decades** and flies
on Curiosity, Perseverance, JWST and dozens more. **RAD5545** is the quad-core successor.
**GR740** (LEON4, SPARC) is the European counterpart.

**⚠️ HPSC changes the ceiling.** NASA's **High Performance Spaceflight Computing** program,
built by **Microchip** and productized as **PIC64-HPSC**, is a **radiation-hardened 64-bit
RISC-V SoC** with vector pipelines, a built-in **TSN Ethernet switch**, memory, and I/O.
Reported figures: **~2 TOPS INT8**, and it **supports Linux and RTEMS plus hypervisors
including Xen.**

**Status as of August 2026** — ⚠️ **and read this precisely, because coverage overstates
it**: the processor **sent its first "Hello Universe" message and began functional,
radiation, thermal and shock testing at JPL in February 2026.** JPL reported in May 2026
that testing is showing **indications of 500× the performance of current rad-hard flight
processors** — ⚠️ **against a program goal of 100×.**

> **⚠️ GOTCHA — the 500× figure is an early indication from an active test programme, not
> a flight result.** **HPSC has not completed spaceflight qualification, NASA has not named
> a first mission, and the programme page still places it in test and qualification.**
> Samples have gone to early-access partners. **Design against RAD750/RAD5545-class
> capability today; plan for HPSC as a future option.**

**⚠️ The architectural consequence if it qualifies**: onboard AI inference becomes
practical, which changes §15 → `flightsw-gnc-verification-ground-and-autonomy` from aspiration to engineering. **It also means Linux and
hypervisors on flight hardware become mainstream**, with all the mixed-criticality
questions that raises.

**The COTS trade**: commercial parts are vastly faster and cheaper but **radiation-soft**.
⚠️ **The smallsat approach — fly COTS, accept upsets, recover in software with watchdogs
and redundancy — is legitimate for LEO short-duration missions and dangerous for deep
space**, where total dose and no-repair change the calculus entirely.

---

## §5. Radiation Effects, in Software Terms

**[DURABLE] Physics is in a space-exploration reference §11. Here's what the software must
do about it.**

| Effect | Software response |
|---|---|
| **SEU** — bit flip in memory or register | **EDAC + scrubbing** (§5.1) |
| **SEFI** — functional interrupt, device hangs | Watchdog, power-cycle, reconfigure |
| **SEL** — latchup, potentially destructive | ⚠️ **Current-limit detection and rapid power cycling — this is a hardware/software co-design** |
| **TID** — cumulative degradation | Margin, and end-of-life parameter drift |
| **MBU** — multiple bits in one word | ⚠️ **Defeats simple SECDED — needs interleaving** |

**5.1 EDAC and scrubbing.** **SECDED** (single error correct, double error detect) Hamming
codes on memory, plus ⚠️ **a background scrubber task that walks all of memory
periodically, reading and rewriting to correct single-bit errors before a second flip
makes them uncorrectable.** **The scrub period must be short relative to the expected
double-error accumulation time** — that's the actual design calculation, and it depends on
orbit.

**5.2 Redundancy in software**: **TMR** (triple modular redundancy with voting — in
hardware, or in software for critical variables), **checksummed critical data structures**,
**periodic recomputation and comparison**, and **⚠️ "self-checking pairs"** where two
dissimilar computations must agree.

**5.3 ⚠️ Defensive coding that is specific to this domain:**
- **Validate state variables on read**, not just on write — ⚠️ **the value may have changed
  since you wrote it, with no code executing.**
- **Enumerations with wide separation** in bit patterns, so a single flip doesn't turn one
  valid state into another valid state. **Never use 0/1/2/3 for a mode variable in
  radiation.**
- **Checksum code segments and compare periodically** — ⚠️ **instruction memory corrupts
  too.**
- **Bound every loop** (Power of 10 rule 2) so a corrupted counter cannot hang the system.
- **⚠️ Assume any single reading is suspect**; require consistency across time or sensors.

---

## §6. Real-Time Discipline

**[DURABLE] "Real-time" means bounded latency, not fast.**

**Hard** (missing a deadline is failure — attitude control, engine control),
**firm** (a missed deadline makes the result useless), **soft** (degradation).
⚠️ **Most flight software is hard real-time, and the deadlines are set by control-loop
stability margins** (§12 → `flightsw-gnc-verification-ground-and-autonomy`), not by preference.

**Scheduling**: **rate-monotonic** (⚠️ **static priorities by period; the RM bound is
`U ≤ n(2^(1/n) − 1)` → ~69% for large n, and schedulability is provable**), **EDF**
(dynamic, higher utilization, ⚠️ **but unpredictable overload behaviour**), **cyclic
executive** (⚠️ **a fixed time-sliced major/minor frame table — completely deterministic
and still widely used in launch vehicles for exactly that reason**), and **time-partitioned
(ARINC 653)** for mixed criticality.

**⚠️ Priority inversion is the canonical real-time bug, and it has flown.** A high-priority
task blocks on a mutex held by a low-priority task, which is preempted by a medium-priority
task. **Fix: priority inheritance or priority ceiling protocol.** See §16.1 → `flightsw-gnc-verification-ground-and-autonomy` — **this is what
happened to Mars Pathfinder on the surface of Mars.**

**WCET (worst-case execution time)** must be **bounded and analysed**, which is why
⚠️ **caches, branch prediction and speculative execution are a problem, not a benefit** —
they make timing statistical rather than bounded. **Some flight systems disable caches on
critical paths.**

**⚠️ Practices that follow**: no dynamic allocation (Power of 10 rule 3), **statically
allocated pools** if you need variable data, **bounded queues with defined overflow
behaviour**, **stack depth analysis with margin**, and **jitter measurement**, not just
average latency.

---

## §7. RTOS

| RTOS | Position |
|---|---|
| **VxWorks** | ⚠️ **The heritage commercial choice — Mars rovers, JWST. DO-178C certifiable, expensive** |
| **RTEMS** | ⚠️ **Open source, strong ESA and NASA heritage, no licence cost** |
| **FreeRTOS** | Small, simple, ubiquitous in cubesats and MCUs |
| **Zephyr** | Modern, growing, good driver ecosystem |
| **QNX** | Microkernel; ⚠️ **added to cFS OSAL in Draco (Jan 2026)** |
| **PikeOS / LynxOS-178** | Time-and-space partitioned, ARINC 653 |
| **Embedded Linux** | ⚠️ **Not hard real-time without PREEMPT_RT; increasingly used for payload and non-critical processing** |
| **Bare metal** | Small controllers, engine sequencers |

**⚠️ The selection criteria that actually matter**: certification evidence available,
**determinism and documented WCET behaviour**, driver and BSP support for your processor,
**licence cost and source availability** (⚠️ **you will need to read the scheduler**), and
heritage on comparable missions.

**⚠️ The mixed-criticality pattern** now common: an RTOS partition running the critical
control loops, and a Linux partition for payload processing, **separated by a hypervisor or
by ARINC 653 time-and-space partitioning.** HPSC's Xen support (§4) is aimed squarely at
this.
