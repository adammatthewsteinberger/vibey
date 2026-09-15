---
name: flightsw-architecture-languages-and-standards
description: "Use when structuring a flight software project or choosing its language: what makes flight software different from ordinary embedded work, the layered architecture pattern, the two frameworks worth knowing (cFS and F Prime) and the reusable applications around them, the language landscape, Rust's actual status in flight projects, and the coding standards (MISRA, JPL, NASA rules) and what they are really for. Includes the router for the whole flight-software reference."
---

# Flight Software: What Makes It Different, Architecture, Languages, and Coding Standards

> **Part 1 of 5** of the *Flight Software* reference (plugin `flight-software`), covering §0–§3. Sibling skills: `flightsw-processors-radiation-and-real-time` (§4–§7), `flightsw-fdir-time-telemetry-and-updates` (§8–§11), `flightsw-gnc-verification-ground-and-autonomy` (§12–§16), `flightsw-reference` (§17–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    corrupting underneath it** (§4 → `flightsw-processors-radiation-and-real-time`, §5 → `flightsw-processors-radiation-and-real-time`).
> 3. **⚠️ Correct-but-late is wrong.** A control loop that misses its deadline has failed
>    regardless of the answer it eventually produces. **Determinism outranks throughput,
>    and this inverts almost every instinct from server-side engineering** (§6 → `flightsw-processors-radiation-and-real-time`).

---

## §0. Routing

| You want... | Go to |
|---|---|
| **What makes flight software different** | **§1** |
| Architecture and frameworks (cFS, F Prime) | §2 |
| Languages and coding standards | §3 |
| **Flight processors and the hardware** | **§4 → `flightsw-processors-radiation-and-real-time`** |
| Radiation effects in software | §5 → `flightsw-processors-radiation-and-real-time` |
| **Real-time discipline** | **§6 → `flightsw-processors-radiation-and-real-time`** |
| RTOS selection | §7 → `flightsw-processors-radiation-and-real-time` |
| **FDIR and fault protection** | **§8 → `flightsw-fdir-time-telemetry-and-updates`** |
| Time, clocks, and correlation | §9 → `flightsw-fdir-time-telemetry-and-updates` |
| Command and telemetry (CCSDS) | §10 → `flightsw-fdir-time-telemetry-and-updates` |
| Data handling and in-flight update | §11 → `flightsw-fdir-time-telemetry-and-updates` |
| GNC software | §12 → `flightsw-gnc-verification-ground-and-autonomy` |
| Verification and validation | §13 → `flightsw-gnc-verification-ground-and-autonomy` |
| Ground segment | §14 → `flightsw-gnc-verification-ground-and-autonomy` |
| Autonomy and onboard AI | §15 → `flightsw-gnc-verification-ground-and-autonomy` |
| **Failure case studies** | **§16 → `flightsw-gnc-verification-ground-and-autonomy`** |
| Contested | §17.1 → `flightsw-reference` |
| What's actually current | §17 → `flightsw-reference` |
| Books and standards | §18 → `flightsw-reference` |
| Quick reference | §19 → `flightsw-reference` |

---

## §1. What Makes It Different

**[DURABLE] The constraints, and why each inverts normal practice:**

| Constraint | Consequence |
|---|---|
| **No physical access, ever** | ⚠️ **Every failure must be diagnosable and recoverable remotely** |
| **Uplink is scarce and slow** | Patches are measured in kilobytes; §11 → `flightsw-fdir-time-telemetry-and-updates` |
| **Radiation corrupts memory** | ⚠️ **Assume your own state is wrong; scrub and check** (§5 → `flightsw-processors-radiation-and-real-time`) |
| **Hard real-time deadlines** | Determinism over throughput (§6 → `flightsw-processors-radiation-and-real-time`) |
| **Extreme reliability requirement** | Formal process, exhaustive review (§13 → `flightsw-gnc-verification-ground-and-autonomy`) |
| **Severely constrained compute** | ⚠️ **Flight CPUs are generations behind commercial** (§4 → `flightsw-processors-radiation-and-real-time`) |
| **Long lifetimes** | ⚠️ **20+ year missions on a toolchain that no longer exists** |
| **Test-as-you-fly is impossible** | You cannot put 1 g of gravity in orbit; §13.3 → `flightsw-gnc-verification-ground-and-autonomy` |

**⚠️ The cultural point that matters more than any technique**: flight software is written
under the assumption that **the reviewer, not the compiler, is the last line of defence**.
NASA's software classification (⚠️ **Class A "human-rated" through Class E**) drives the
required rigour, and **Class A software routinely costs $500–$1,000 per line** delivered.
That number sounds absurd until you price the alternative.

**⚠️ And the inversion worth internalizing**: in most software, you optimize for the
expected case and handle errors. **In flight software you design for the fault case, and
nominal operation is what happens when no fault fires.** §8 → `flightsw-fdir-time-telemetry-and-updates` is not a subsystem — it is the
organizing principle.

---

## §2. Architecture

### 2.1 The layered pattern

**[DURABLE] Essentially every serious flight software stack looks like this:**
```
   Mission-specific applications  (science, payload ops, mission logic)
   ─────────────────────────────
   Reusable applications          (housekeeping, limit checking, stored commands,
                                   file management, telemetry output, scheduler)
   ─────────────────────────────
   Framework / executive          (message bus, event services, time services,
                                   table services, software bus)
   ─────────────────────────────
   OS abstraction layer           ⚠️ the portability seam
   ─────────────────────────────
   RTOS  (§7)
   ─────────────────────────────
   BSP / drivers / hardware       (§4)
```

**⚠️ The OS abstraction layer is the single highest-value architectural decision**, because
it lets you develop and test on Linux and deploy on an RTOS — which changes the economics
of testing completely (§13 → `flightsw-gnc-verification-ground-and-autonomy`).

**Message-passing over shared state**: components communicate via a **publish-subscribe
software bus** rather than shared memory. ⚠️ **This is not stylistic — it makes components
independently testable, makes the data flow inspectable in telemetry, and confines the
concurrency reasoning to the bus implementation** rather than spreading it across every
module.

### 2.2 The two frameworks worth knowing

**[VERSIONED in release detail, DURABLE in design.]**

**NASA cFS (core Flight System)** — ⚠️ **the de facto architectural standard, written in C**,
originally from Goddard. Structure: **OSAL** (OS abstraction), **PSP** (platform support
package), and **cFE** (core Flight Executive) providing event, time, table, file and
**software bus** services. It has flown **40+ NASA missions** from smallsats to flagships
including **Roman Space Telescope**, and is **the primary software architecture for Lunar
Gateway.**

⚠️ **v7.0.0 "Draco" (January 2026) added QNX** to the supported OS list alongside **Linux,
VxWorks and RTEMS.** A **cFS Gov Alpha release was planned for April 2026** adding security
capabilities, AI/ML integration, expanded robotics support and deeper autonomy.

**⚠️ Goddard's tagline is the whole argument: "Never build Flight Software from scratch
again."** The institutional pain being addressed is that every mission otherwise
reinvents command dispatching, telemetry, fault protection and housekeeping, **and gets it
wrong differently each time, with the lessons staying siloed per project.**

**JPL F Prime (F´)** — component-based with **typed ports** connected into a **topology**,
plus **autocoding tools** that generate components and topologies from model definitions.
Open source, C++. ⚠️ **Deployed on CubeSats, SmallSats, instruments and deployables** —
including **Lunar Flashlight and NEA Scout**, and **Ingenuity, the Mars helicopter.**

> **⚠️ GOTCHA — choosing between them is a real decision, not a preference.**
> A published comparison (built by implementing the same reference mission in both)
> found **they differ in design and in their assumptions about how a user extends them.**
> Broadly: **cFS is the mature, configuration-controlled choice with the deeper mission
> heritage and an active NASA CCB; F Prime is lighter, more modern in its
> model-driven autocoding, and better suited to small teams and instrument-scale
> deployments.** ⚠️ **Neither is wrong. Picking on vibes rather than on your mission class
> and team size is.**

### 2.3 The reusable applications
The set that recurs across every mission, and that the frameworks exist to stop you
rewriting: **command ingest and dispatch**, **telemetry output**, **stored command
sequencer** (⚠️ **absolute and relative time sequences — the backbone of deep space
operations**), **housekeeping**, **limit checker**, **memory manager and dwell**,
**file manager and CFDP** (§11 → `flightsw-fdir-time-telemetry-and-updates`), **checksum**, **health and safety**, and
**data storage/recorder management**.

---

## §3. Languages and Coding Standards

### 3.1 The language landscape

**[DURABLE] C dominates, and the reason is heritage plus tooling, not affection.**
C shipped on **Voyager, the Shuttle GPCs (alongside HAL/S), essentially every JPL deep
space mission of the last three decades, the ISS command and data handling system, and the
overwhelming majority of cubesats flying in 2026.** ⚠️ **cFS is written in C, and that one
fact explains most of C's persistence** — when a new team designs a C&DH stack, the default
isn't "which language," it's "which framework," and the answer pulls C along with it.

| Language | Position |
|---|---|
| **C** | ⚠️ **The substrate. MISRA-constrained, qualified compilers, universal heritage** |
| **C++** | F Prime; ⚠️ **restricted subsets — no exceptions, no RTTI, no dynamic allocation after init** |
| **Ada / SPARK** | ⚠️ **Ariane, and much of ESA. Strong typing, contracts; SPARK gives provable absence of runtime errors** |
| **Rust** | §3.2 |
| **Python** | ⚠️ **Ground segment, test, and analysis — not flight-critical paths** |
| **MATLAB/Simulink** | ⚠️ **GNC algorithm development with autocoding to C** (§12 → `flightsw-gnc-verification-ground-and-autonomy`) |

### 3.2 ⚠️ Rust's actual status

**[CONTESTED, and worth stating carefully because both the hype and the dismissal are
wrong.]**

**The case is real**: C makes it trivial to introduce memory-safety issues producing
undefined behaviour or security vulnerabilities, and **Rust substantially eliminates that
class.** For a domain where a single memory bug is unrecoverable, that matters more than
almost anywhere else.

**⚠️ The obstacles are also real**: **industry adoption in safety-critical environments is
still lacking**, driven by Rust's relatively short lifespan — which translates concretely
into **immature qualified toolchains, thin certification precedent, and no heritage.**
The published research direction is **partial rewrites of C-based systems rather than
wholesale replacement**, which is the pragmatic path.

**Where it stands in 2026**: **programmes adopting Rust are training their teams on the
job**, and one 2026 assessment calls it **the highest-leverage new language to learn for
space and adjacent safety-critical work.** ⚠️ **Take that as a career signal, not as
evidence that Rust is the default. It isn't, and won't be for years.**

### 3.3 Coding standards

**[DURABLE] These are not style guides. They exist because each rule maps to a class of
in-flight failure.**

**⚠️ NASA/JPL's "Power of 10" (Holzmann)** — the most quotable set:
1. **Restrict to simple control flow** — no goto, setjmp/longjmp, recursion.
   ⚠️ **Recursion makes stack bounds unprovable.**
2. **All loops must have a fixed upper bound**, statically provable.
   ⚠️ **This makes runaway loops impossible by construction.**
3. **No dynamic memory allocation after initialization.**
   ⚠️ **Kills fragmentation, exhaustion, and use-after-free in one rule.**
4. **No function longer than ~60 lines** — one printed page.
5. **≥2 assertions per function**, checking anomalous conditions.
6. **Declare data objects at the smallest possible scope.**
7. **Check every non-void return value; validate every parameter.**
8. **Limit the preprocessor** to includes and simple conditional compilation.
9. **Restrict pointer use** to one level of dereferencing; no function pointers.
10. **⚠️ Compile with all warnings enabled, zero warnings, and analyse daily with
    multiple static analysers.**

**MISRA C** (2012, amended) — ~150 rules for C in safety-critical systems, with
**mandatory / required / advisory** categories and a **formal deviation process**.
⚠️ **Deviations are permitted but must be documented and justified — that discipline is
the actual value, more than any individual rule.**

**JPL Institutional Coding Standard for C** — Power of 10 plus JPL specifics, organized by
**risk level.**

**Process standards**: **NPR 7150.2** (NASA software engineering requirements, with the
Class A–E classification), **DO-178C** (airborne, ⚠️ **DAL A–E; with DO-333 for formal
methods and DO-331 for model-based development**), **ECSS-Q-ST-80C** and **ECSS-E-ST-40C**
(⚠️ **the European equivalents, criticality A–D — and if you work with ESA these are the
ones that bind**).

**⚠️ MC/DC coverage** (modified condition/decision coverage) is required at DO-178C DAL A —
**every condition in every decision must be shown to independently affect the outcome.**
It is expensive, and it is why avionics testing costs what it does.
