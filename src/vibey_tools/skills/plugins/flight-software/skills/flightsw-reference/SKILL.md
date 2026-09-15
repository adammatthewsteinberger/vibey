---
name: flightsw-reference
description: "Use when checking whether a flight processor or framework claim is still current (verified August 2026), weighing a contested question in flight software practice, finding the books and the standards, or needing the rules that map to dead vehicles, a framework picker, and a code review checklist. Companion to the other flight-software skills."
---

# Flight Software: Currency, Contested Questions, Standards, and Canon

> **Part 5 of 5** of the *Flight Software* reference (plugin `flight-software`), covering §17–§20. Sibling skills: `flightsw-architecture-languages-and-standards` (§0–§3), `flightsw-processors-radiation-and-real-time` (§4–§7), `flightsw-fdir-time-telemetry-and-updates` (§8–§11), `flightsw-gnc-verification-ground-and-autonomy` (§12–§16). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The discipline and standards are stable; flight processors and framework releases moved materially in 2025-26. See §17 below for what is dated and what is genuinely contested.

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

## §17. Currency and Contested

### 17.1 Contested

**⚠️ Rust versus C.** §3.2 → `flightsw-architecture-languages-and-standards`. **Neither position is silly.** The memory-safety argument is
strong precisely because the domain is unforgiving; the heritage-and-toolchain argument is
strong for the same reason. **Current honest position: partial adoption, non-critical
paths first, and watch the qualification story.**

**⚠️ cFS versus F Prime versus roll-your-own.** §2.2 → `flightsw-architecture-languages-and-standards`. Rolling your own is almost always
wrong now, ⚠️ **and "almost" is doing real work — very small, very short missions with
unusual constraints sometimes justify it.**

**⚠️ COTS versus rad-hard.** §4 → `flightsw-processors-radiation-and-real-time`. **Genuinely mission-dependent**: LEO smallsat versus
outer-planet flagship are different problems with different right answers.

**⚠️ How much autonomy.** §15 → `flightsw-gnc-verification-ground-and-autonomy`. More capability at distance, harder verification, and
fault protection that can itself cause failures (§8 → `flightsw-fdir-time-telemetry-and-updates`).

**⚠️ Linux in flight-critical roles.** Increasingly common for payload processing;
⚠️ **still contested for hard real-time control paths without partitioning.**

### 17.2 Verified August 2026

| Thing | Status | Decay risk |
|---|---|---|
| **cFS** | **v7.0.0 "Draco" (January 2026) added QNX** to OSAL alongside Linux, VxWorks, RTEMS. **Gov Alpha planned April 2026** — security, AI/ML, robotics, autonomy. **40+ NASA missions**, including Roman; **primary architecture for Lunar Gateway.** 2026 Symposium drew ~150 in person with cross-sector participation | Medium |
| **F Prime** | JPL, open source, component/typed-port/topology with autocoding. Flown on **Lunar Flashlight, NEA Scout, Ingenuity** | Low |
| **⚠️ HPSC** | Microchip **PIC64-HPSC**, rad-hard 64-bit **RISC-V** SoC, ~**2 TOPS INT8**, **240 Gbps TSN Ethernet switch**, supports **Linux, RTEMS, Xen**. **First "Hello Universe" and start of JPL functional/radiation/thermal/shock testing February 2026**; **May 2026 reports indicate ~500× current rad-hard processors** against a **100×** program goal. ⚠️ **Not spaceflight-qualified; no first mission named; samples to early-access partners** | **High** |
| **Incumbent processors** | **RAD750** remains the two-decade workhorse; **RAD5545** the quad-core successor; **GR740** the European counterpart | Low |
| **Rust** | ⚠️ **Adoption in safety-critical space still lacking**; research direction is **partial C-to-Rust rewrites**, not replacement. Teams adopting it train on the job. Described in a 2026 assessment as the highest-leverage new language to learn for the domain | Medium |

---

## §18. Books and Standards

| Source | Why |
|---|---|
| **Holzmann, "The Power of Ten"** (IEEE Computer, 2006) | ⚠️ **Ten pages. Read it today** |
| **JPL Institutional Coding Standard for C** | Power of 10 plus specifics, by risk level |
| **MISRA C:2012** (+ amendments) | The safety-critical C ruleset |
| **NPR 7150.2** | ⚠️ **NASA software engineering requirements and the A–E classification** |
| **NASA-STD-8739.8** | Software assurance and safety |
| **NASA-GB-8719.13** | NASA Software Safety Guidebook |
| **DO-178C** + DO-330/331/333 | Airborne certification; tool qualification, MBD, formal methods |
| **ECSS-E-ST-40C / Q-ST-80C** | ⚠️ **The European equivalents — binding if you work with ESA** |
| **CCSDS Blue Books** | ⚠️ **Free. Space packets, TM/TC, CFDP, SDLS** (§10 → `flightsw-fdir-time-telemetry-and-updates`, §11 → `flightsw-fdir-time-telemetry-and-updates`) |
| **Liu & Layland (1973)** | The rate-monotonic paper. Still the foundation (§6 → `flightsw-processors-radiation-and-real-time`) |
| **Kopetz, *Real-Time Systems*** | The standard text on distributed real-time |
| **Leveson, *Engineering a Safer World*** | ⚠️ **STAMP/STPA, and the Therac-25 analysis. The best systems-safety thinking available** |
| **Holzmann, *The SPIN Model Checker*** | Formal verification of concurrency, from the source (§13 → `flightsw-gnc-verification-ground-and-autonomy`) |
| **Eickhoff, *Onboard Computers, Onboard Software and Satellite Operations*** | The dedicated textbook for this exact subject |
| **NASA cFS and F Prime documentation** | ⚠️ **Both open source; read the actual code** |
| **NASA NTRS** | ⚠️ **Decades of lessons-learned and anomaly reports, free** |

---

## §19. Quick Reference

### 19.1 The rules that map to dead vehicles
```
Bound every loop statically                     §3.3 / runaway
No dynamic allocation after init                §3.3 / fragmentation, exhaustion
Enable priority inheritance                     §16.1 / Mars Pathfinder
Re-validate inherited code for the new envelope §16.2 / Ariane 501
Specify units at every interface                §16.3 / Mars Climate Orbiter
Plausibility-check sensors against state        §16.4 / Mars Polar Lander
Don't remove hardware interlocks                §16.5 / Therac-25
Test the integrated end-to-end sequence         §16.6 / Starliner OFT-1
Immutable or dual-redundant bootloader          §11 / unrecoverable bricking
Scrub memory faster than double-error accrual   §5.1 / uncorrectable SEU
Widely-separated enum bit patterns              §5.3 / single-flip state change
Compute your counter rollover interval          §9 / 32-bit ms wraps at 49.7 days
```

### 19.2 Picker
| Need | Choice |
|---|---|
| Framework, mature + heritage + CCB | **cFS** (§2.2 → `flightsw-architecture-languages-and-standards`) |
| Framework, small team, instrument scale | **F Prime** (§2.2 → `flightsw-architecture-languages-and-standards`) |
| Language, default | **C** + MISRA + Power of 10 (§3 → `flightsw-architecture-languages-and-standards`) |
| Language, provable absence of runtime errors | **SPARK/Ada** (§3.1 → `flightsw-architecture-languages-and-standards`) |
| Language, new memory-safe work | ⚠️ **Rust, non-critical path first** (§3.2 → `flightsw-architecture-languages-and-standards`) |
| RTOS, certification evidence | **VxWorks**, LynxOS-178, PikeOS (§7 → `flightsw-processors-radiation-and-real-time`) |
| RTOS, no licence cost, heritage | **RTEMS** (§7 → `flightsw-processors-radiation-and-real-time`) |
| RTOS, cubesat | **FreeRTOS** or Zephyr (§7 → `flightsw-processors-radiation-and-real-time`) |
| Deterministic launch-vehicle sequencing | **Cyclic executive** (§6 → `flightsw-processors-radiation-and-real-time`) |
| Mixed criticality | ARINC 653 partitioning or hypervisor (§7 → `flightsw-processors-radiation-and-real-time`) |
| Memory protection | **SECDED + background scrubber** (§5.1 → `flightsw-processors-radiation-and-real-time`) |
| File transfer over a bad link | **CFDP** (§11 → `flightsw-fdir-time-telemetry-and-updates`) |
| Command/telemetry | **CCSDS**, + **SDLS** for authentication (§10 → `flightsw-fdir-time-telemetry-and-updates`) |
| Concurrency verification | **SPIN** model checking (§13 → `flightsw-gnc-verification-ground-and-autonomy`) |
| Ground visualization | **OpenMCT**, OpenC3, Yamcs (§14 → `flightsw-gnc-verification-ground-and-autonomy`) |

### 19.3 Review checklist
- [ ] Every loop statically bounded? (§3.3 → `flightsw-architecture-languages-and-standards`)
- [ ] Zero dynamic allocation after init? (§3.3 → `flightsw-architecture-languages-and-standards`)
- [ ] Stack depth analysed with margin? (§6 → `flightsw-processors-radiation-and-real-time`)
- [ ] WCET bounded for every hard-real-time path? (§6 → `flightsw-processors-radiation-and-real-time`)
- [ ] Priority inheritance on every shared mutex? (§16.1 → `flightsw-gnc-verification-ground-and-autonomy`)
- [ ] All interfaces unit-specified? (§16.3 → `flightsw-gnc-verification-ground-and-autonomy`)
- [ ] Sensor inputs plausibility-checked against state? (§16.4 → `flightsw-gnc-verification-ground-and-autonomy`)
- [ ] Enum values widely separated in bit pattern? (§5.3 → `flightsw-processors-radiation-and-real-time`)
- [ ] Critical structures checksummed and periodically verified? (§5.3 → `flightsw-processors-radiation-and-real-time`)
- [ ] Every counter's rollover interval computed and handled? (§9 → `flightsw-fdir-time-telemetry-and-updates`)
- [ ] Safe mode survivable indefinitely, Earth/Sun-pointed? (§8 → `flightsw-fdir-time-telemetry-and-updates`)
- [ ] Command loss timer implemented and tested? (§8 → `flightsw-fdir-time-telemetry-and-updates`)
- [ ] Fault responses inhibited during critical sequences? (§8 → `flightsw-fdir-time-telemetry-and-updates`)
- [ ] Diagnostics persisted *before* recovery action? (§8 → `flightsw-fdir-time-telemetry-and-updates`)
- [ ] Bootloader immutable or dual-redundant? (§11 → `flightsw-fdir-time-telemetry-and-updates`)
- [ ] Update path has automatic rollback? (§11 → `flightsw-fdir-time-telemetry-and-updates`)
- [ ] Hazardous commands two-stage arm/fire? (§10 → `flightsw-fdir-time-telemetry-and-updates`)
- [ ] Out-of-range parameters rejected, not clamped? (§10 → `flightsw-fdir-time-telemetry-and-updates`)
- [ ] Telemetry sufficient to diagnose an unanticipated fault? (§10 → `flightsw-fdir-time-telemetry-and-updates`)
- [ ] Static analysis clean, multiple tools, zero warnings? (§3.3 → `flightsw-architecture-languages-and-standards`)
- [ ] Fault injection campaign run? (§13 → `flightsw-gnc-verification-ground-and-autonomy`)
- [ ] Testbed configuration under control and matching flight? (§13.3 → `flightsw-gnc-verification-ground-and-autonomy`)

---

## §20. Method

**This is engineering practice, not reporting.** §1–§3 → `flightsw-architecture-languages-and-standards`, §5–§16 → `flightsw-processors-radiation-and-real-time`, `flightsw-fdir-time-telemetry-and-updates`, `flightsw-gnc-verification-ground-and-autonomy` and §19 rest on the
standard sources — **Holzmann's Power of 10 and the JPL coding standard, MISRA C:2012,
NPR 7150.2, DO-178C, the ECSS software standards, the CCSDS Blue Books, Liu & Layland,
Leveson, and the published NASA anomaly and lessons-learned literature.** None of that has
a currency dependency and none was web-verified; the standards are the authority and they
change on multi-year cycles.

**Deliberately scoped to complement**: this supersedes and expands the compressed
flight-software material in a robotics-software reference; spacecraft systems engineering
(power, thermal, link budgets, EDL) is in a space-exploration reference; launch and orbital
physics in a rocket-science reference.

**Two searches were run in August 2026**, confined to the two things that genuinely moved:
**framework releases** (§2.2 → `flightsw-architecture-languages-and-standards`) and **flight processors** (§4 → `flightsw-processors-radiation-and-real-time`).

**Sources for those**: **NASA Goddard's cFS pages and the 2026 cFS Symposium reporting**,
plus **SpaceNews** coverage of the Symposium, for the Draco/QNX and Gov Alpha details and
the mission-count and Gateway claims; **NASA's own "Hello Universe" release**, the
**Microchip PIC64-HPSC product documentation**, and **JPL reporting via SpaceDaily** for
HPSC's specifications and test status; the **JPL/NASA F Prime documentation** and
**SmallSat Conference papers** for F Prime heritage and the published cFS/F Prime
comparison; and a **2024 arXiv paper (Seidel & Beier)** plus a 2026 industry assessment for
the Rust position.

**Confidence.** **High** in §1–§3 → `flightsw-architecture-languages-and-standards`, §5–§16 → `flightsw-processors-radiation-and-real-time`, `flightsw-fdir-time-telemetry-and-updates`, `flightsw-gnc-verification-ground-and-autonomy` — established practice, and the case studies in
§16 → `flightsw-gnc-verification-ground-and-autonomy` are among the most thoroughly documented failures in engineering. **High** in §2.2 → `flightsw-architecture-languages-and-standards`'s
cFS description and §4 → `flightsw-processors-radiation-and-real-time`'s HPSC specifications, which come from NASA and Microchip directly.

⚠️ **Deliberately hedged in two places.** **The HPSC "500×" figure**: I have stated
explicitly that it is **an early indication from an active test programme against a 100×
program goal, that qualification is incomplete, and that no first mission is named** —
because the secondary coverage repeatedly presents it as a delivered capability, and
⚠️ **several of the sources reporting it are aggregators rather than primary.** **Design
against RAD750/RAD5545-class hardware today.** And **§3.2 → `flightsw-architecture-languages-and-standards`'s Rust position**: ⚠️ **the "highest-leverage
language to learn" characterization comes from a training-industry source with an obvious
incentive to say so** — I have kept the claim but attributed its character. **The
underlying adoption picture — real interest, immature qualification, partial-rewrite
strategy — is corroborated by the peer-reviewed work.**

**§17.1 is engineering judgement**, and the Rust/C and COTS/rad-hard questions in
particular are live disagreements among people with more flight heritage than I have
synthesized here.
