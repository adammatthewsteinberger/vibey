---
name: auto-reference
description: "Use when checking an automotive software anti-pattern, looking up a bus rate, timing or standard number, asking what actually moved in regulation and architecture (verified August 2026), finding the books and standards, or needing a picker and a design review checklist. Companion to the other automotive-software skills."
---

# Automotive Software: Anti-Patterns, Numbers, What Moved, and Canon

> **Part 5 of 5** of the *Automotive Software* reference (plugin `automotive-software`), covering §15–§20. Sibling skills: `auto-architecture-buses-and-autosar` (§0–§4), `auto-real-time-safety-and-cybersecurity` (§5–§7), `auto-diagnostics-ota-and-adas` (§8–§10), `auto-process-testing-domains-and-supply-chain` (§11–§14). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** CAN, UDS, ASIL and the V-model are stable and decades old; the regulatory layer and the shift to zonal and central compute moved materially. See §17 below for both, dated.

> **Scope.** Complements an embedded-IoT reference (MCUs, RTOS, buses at the generic
> level), a flight-software reference (the closest sibling discipline — much of §6 → `auto-real-time-safety-and-cybersecurity`'s
> reasoning is shared), and a robotics-software reference (§14 there, and the autonomy
> stack). **This is the vehicle-specific layer.**
>
> **⚠️ GOTCHA** boxes mark what kills people, fails an audit, or bricks a fleet.
>
> **The three facts that make automotive software its own discipline:**
> 1. **⚠️ Software can kill, and the system knows it.** Steering, braking and propulsion
>    are safety-critical in the formal sense — ISO 26262 assigns them an ASIL, and that
>    rating dictates your architecture, your process, and your evidence (§6 → `auto-real-time-safety-and-cybersecurity`).
> 2. **⚠️ The vehicle is a distributed real-time system built by a supply chain, not a
>    team.** An OEM integrates software from dozens of Tier-1s who integrate from Tier-2s.
>    **AUTOSAR exists because of this org chart, not because it's elegant** (§4 → `auto-architecture-buses-and-autosar`, §16).
> 3. **⚠️ It ships for 15 years and you cannot recall it cheaply.** OTA changed the
>    economics but not the liability — **and now an update itself requires regulatory
>    approval** (§9 → `auto-diagnostics-ota-and-adas`, §17.1).

---

## §15. Anti-Patterns

| Anti-pattern | Why |
|---|---|
| Treating ASIL as a label applied late | ⚠️ **It determines architecture. HARA comes first** (§6.1 → `auto-real-time-safety-and-cybersecurity`) |
| ASIL decomposition without dependent-failure analysis | ⚠️ **Shared clock/power/bus invalidates it** (§6.2 → `auto-real-time-safety-and-cybersecurity`) |
| "Safe state = shut down" | ⚠️ **Losing steering assist at speed is itself a hazard** (§6.4 → `auto-real-time-safety-and-cybersecurity`) |
| Watchdog that only checks aliveness | ⚠️ **Alive-but-wrong is the failure it misses. Use program flow monitoring** (§6.4 → `auto-real-time-safety-and-cybersecurity`) |
| Trusting UDS 0x27 security access | ⚠️ **Fixed algorithm, extractable from tester software** (§8 → `auto-diagnostics-ota-and-adas`) |
| Putting a fresh ECU on the powertrain bus unsegmented | CAN has no authentication (§3.1 → `auto-architecture-buses-and-autosar`, §7.3 → `auto-real-time-safety-and-cybersecurity`) |
| Skipping E2E protection on safety-relevant messages | ⚠️ **Corruption, repetition, loss and masquerade all go undetected** (§6.4 → `auto-real-time-safety-and-cybersecurity`) |
| Assuming Adaptive AUTOSAR replaces Classic | ⚠️ **They coexist by design** (§4.2 → `auto-architecture-buses-and-autosar`) |
| Zonal architecture as a pure hardware cost play | ⚠️ **Complexity moves to software governance** (§2.1 → `auto-architecture-buses-and-autosar`) |
| Ethernet for control traffic without TSN | No bounded latency (§3.2 → `auto-architecture-buses-and-autosar`) |
| Wrong CAN termination | ⚠️ **Two 120 Ω, at the ends. Classic intermittent fault** (§3.1 → `auto-architecture-buses-and-autosar`) |
| Bus load above ~50% | No latency headroom (§3.1 → `auto-architecture-buses-and-autosar`) |
| Autocoded model assumed exempt from WCET/MISRA checks | ⚠️ **It isn't** (§11 → `auto-process-testing-domains-and-supply-chain`) |
| Undocumented MISRA deviations | Documented is fine; silent is a finding (§11 → `auto-process-testing-domains-and-supply-chain`) |
| Mutable bootloader, single bank | ⚠️ **An unrecoverable brick** (§9 → `auto-diagnostics-ota-and-adas`) |
| OTA without power-loss safety at every step | The customer will unplug it (§9 → `auto-diagnostics-ota-and-adas`) |
| OTA without per-vehicle software provenance records | ⚠️ **R156 requires it** (§7.2 → `auto-real-time-safety-and-cybersecurity`, §9 → `auto-diagnostics-ota-and-adas`) |
| Marketing an L2 system in L3+ language | ⚠️ **A liability and regulatory problem, not a wording one** (§10.1 → `auto-diagnostics-ota-and-adas`) |
| Driver monitoring by steering torque alone | Trivially defeated (§10.3 → `auto-diagnostics-ota-and-adas`) |
| Claiming validation by disengagement rate | ⚠️ **Gameable and not comparable** (§10.4 → `auto-diagnostics-ota-and-adas`) |
| Claiming autonomy is validated at all | ⚠️ **No accepted sufficient methodology exists** (§10.4 → `auto-diagnostics-ota-and-adas`) |
| Ignoring quiescent current in sleep design | Flat battery in the airport car park (§2.3 → `auto-architecture-buses-and-autosar`) |
| Variant handling by preprocessor sprawl | Unmaintainable combinatorics (§13 → `auto-process-testing-domains-and-supply-chain`) |
| Treating security as a feature rather than type approval | ⚠️ **No CSMS certificate, no sale** (§7.2 → `auto-real-time-safety-and-cybersecurity`) |

---

## §16. Numbers

```
BUSES
LIN 20 kbit/s · CAN 1 Mbit/s · CAN FD ~8 Mbit/s · FlexRay 10 Mbit/s
Automotive Ethernet 100 Mbit/s – multi-gig · ⚠️ CAN termination 2 × 120 Ω
CAN ID 11-bit standard / 29-bit extended · ⚠️ lower ID = higher priority
CAN payload 8 bytes · CAN FD 64 bytes · CAN XL 2048 bytes
⚠️ Target bus load <40–50%

SAFETY
ASIL A/B/C/D + QM · S0–S3 × E0–E4 × C0–C3 → ASIL
⚠️ ASIL D: SPFM ≥99%, LFM ≥90%, PMHF <10⁻⁸/h (10 FIT)
⚠️ ASIL B: SPFM ≥90%, LFM ≥60%, PMHF <10⁻⁷/h
MC/DC coverage required at ASIL D

REGULATION
⚠️ R155 Annex 5: 69 attack vectors · CSMS/SUMS certificates valid 3 years
54+ UNECE contracting parties

ENVIRONMENT
Operating −40 to +125 °C (⚠️ underhood higher) · 12 V nominal (⚠️ 9–16 V range)
48 V mild hybrid · 400/800 V traction
⚠️ Load dump transients to ~100 V+ · Design life 15 years / 240,000 km

SCALE
Legacy vehicle 70–150 ECUs · ⚠️ 100M+ lines of code cited for premium vehicles
Zonal target: >50% ECU reduction, ~40% wiring reduction
Harness: among the heaviest and costliest components, hand-assembled
```

---

## §17. What Actually Moved

### 17.1 Regulation — verified August 2026
**⚠️ This is the layer that changed the industry most, and it is not optional.**
- **UN R155 (cybersecurity/CSMS) and R156 (software updates/SUMS)** were **adopted June
  2020**, came **into force January 2021**, and applied **to all new vehicles produced for
  UNECE countries from July 2024.** ⚠️ **Sources vary on phrasing of the intermediate
  dates — the practically important point is that they are fully in effect now.**
- **⚠️ Both require certification by an audited management system**, valid **three years**,
  as a **condition of type approval** across **54+ contracting parties** (EU, UK, Japan,
  South Korea, Australia and others).
- **R155 Annex 5 enumerates 69 attack vectors** that a threat analysis must address.
- **⚠️ Scope is expanding**: reported extension to **Category L (motorcycles, scooters)
  from December 2027.**
- **⚠️ Parallel national frameworks exist** — **China's GB 44495:2024**, described as one
  of the most technically demanding, **effective for new vehicle types from January
  2026** — and India and others are following the UNECE blueprint. **This is no longer a
  European concern.**
- **ISO/SAE 21434 is the engineering standard R155 references**, and ⚠️ **conformance to it
  does not by itself guarantee approval.**

### 17.2 The architectural shift
**⚠️ Zonal is past the decision point and into execution.** Reported 2026 survey data:
**more than 90% of automotive OEMs committed to zonal architecture, with ~80% already
migrating and ~11% with firm plans**; **45% of surveyed OEMs and suppliers rank the SDV
transition as their number one strategic priority.** Named platforms include **VW's SSP**,
**GM Ultifi**, **Mercedes MB.OS**, **BMW's Neue Klasse**, and **Tesla and Rivian** as
existing zonal-principle implementations.

**⚠️ The driver is bandwidth as much as cost**: **CAN FD capped around 8 Mbit/s is
inadequate** for ADAS, high-resolution infotainment and AI cabin features, **accelerating
adoption of 100 Mbit/s to gigabit automotive Ethernet with TSN** (§3.2 → `auto-architecture-buses-and-autosar`).

**AUTOSAR Adaptive** is the middleware answer for HPC nodes — ⚠️ **reported Adaptive
Platform membership growth of 22% in a year, and the Eclipse SDV working group at 50+
members.** **Classic and Adaptive coexist** (§4.2 → `auto-architecture-buses-and-autosar`), with vendor platforms unifying them.

> **⚠️ GOTCHA — treat the market figures above with care.** Adoption percentages, revenue
> forecasts and membership growth come from **analyst reports and vendor-adjacent
> sources**, several of which sell services into this transition. ⚠️ **The direction is
> unambiguous and corroborated across many independent sources; the specific percentages
> are not measurements.** **The engineering content of §2 → `auto-architecture-buses-and-autosar` and §3 → `auto-architecture-buses-and-autosar` does not depend on
> them.**

---

## §18. Books and Resources

| Source | Why |
|---|---|
| **ISO 26262** (all parts) | ⚠️ **The standard itself. Part 6 is software. Expensive and unavoidable** |
| **ISO 21448 (SOTIF)** | §6.5 → `auto-real-time-safety-and-cybersecurity` |
| **ISO/SAE 21434** | §7.1 → `auto-real-time-safety-and-cybersecurity` |
| **ISO 14229 (UDS)**, ISO 15765, ISO 13400 | §8 → `auto-diagnostics-ota-and-adas` |
| **MISRA C:2012** and **MISRA C++:2023** | §11 → `auto-process-testing-domains-and-supply-chain` |
| **AUTOSAR specifications** | ⚠️ **Free from autosar.org, and enormous. Start with the layered architecture doc** |
| **Ross, *Functional Safety for Road Vehicles*** | ⚠️ **The best readable treatment of ISO 26262** |
| **Smith & Simpson, *Safety Critical Systems Handbook*** | Cross-industry safety engineering |
| **Koopman, *Better Embedded System Software*** | ⚠️ **Practical, and Koopman's automotive safety writing and UA testimony are essential context** |
| **Zimmermann & Schmidgall, *Bussysteme in der Fahrzeugtechnik*** | The bus reference (German) |
| **Corrigan (TI), CAN application notes** | Free, clear, canonical on CAN physical layer |
| **Charette, "This Car Runs on Code"** (IEEE Spectrum) | The scale problem, well told |

**Practical**: **Vector's knowledge base and CAN/AUTOSAR primers** (⚠️ **genuinely good and
free**), **AUTOSAR.org**, **UNECE WP.29 documents** (⚠️ **the regulations themselves are
public — read R155 Annex 5 directly**), **Eclipse SDV**, **COVESA**, **SOAFEE**,
**Automotive SPICE process reference model**, **NHTSA and Euro NCAP** for the
consumer-facing safety regime, and **openpilot / comma.ai** as a reverse-engineered window
into real vehicle bus behaviour.

---

## §19. Quick Reference

### 19.1 Picker
| Need | Use |
|---|---|
| Cheap sensor/actuator link | **LIN** (§3 → `auto-architecture-buses-and-autosar`) |
| Robust real-time control bus | **CAN / CAN FD** (§3.1 → `auto-architecture-buses-and-autosar`) |
| High bandwidth backbone | **Automotive Ethernet + TSN** (§3.2 → `auto-architecture-buses-and-autosar`) |
| Deterministic legacy x-by-wire | FlexRay (⚠️ legacy — use Ethernet+TSN now) (§3 → `auto-architecture-buses-and-autosar`) |
| Deeply embedded ASIL-D control | ⚠️ **AUTOSAR Classic on an MCU** (§4.1 → `auto-architecture-buses-and-autosar`) |
| Updatable high-compute function | ⚠️ **AUTOSAR Adaptive on POSIX** (§4.2 → `auto-architecture-buses-and-autosar`) |
| Service discovery in-vehicle | **SOME/IP** or DDS (§3.2 → `auto-architecture-buses-and-autosar`) |
| Mixed criticality on one SoC | ⚠️ **Hypervisor partitioning, or a separate safety MCU** (§2.2 → `auto-architecture-buses-and-autosar`) |
| Detect corrupted/lost/replayed safety data | ⚠️ **E2E protection (CRC + counter + data ID)** (§6.4 → `auto-real-time-safety-and-cybersecurity`) |
| Authenticate in-vehicle messages | **SecOC** (§7.3 → `auto-real-time-safety-and-cybersecurity`) |
| Diagnostic access | **UDS over ISO-TP (CAN) or DoIP (Ethernet)** (§8 → `auto-diagnostics-ota-and-adas`) |
| Flash an ECU | **UDS 0x34/36/37 + signature verify + A/B banks** (§9 → `auto-diagnostics-ota-and-adas`) |
| Test an ECU in isolation | ⚠️ **HIL with restbus simulation** (§12 → `auto-process-testing-domains-and-supply-chain`) |
| Validate a safety mechanism | **Fault injection** (§12 → `auto-process-testing-domains-and-supply-chain`) |
| Argue safety for an ML component | ⚠️ **Verifiable safety monitor around it** (§10.3 → `auto-diagnostics-ota-and-adas`) |

### 19.2 Design review checklist
- [ ] HARA done, ASIL assigned per safety goal, before architecture froze? (§6.1 → `auto-real-time-safety-and-cybersecurity`)
- [ ] Any ASIL decomposition backed by dependent-failure analysis? (§6.2 → `auto-real-time-safety-and-cybersecurity`)
- [ ] Safe state defined — and is it actually safe in every operating condition? (§6.4 → `auto-real-time-safety-and-cybersecurity`)
- [ ] E2E protection on every safety-relevant signal path? (§6.4 → `auto-real-time-safety-and-cybersecurity`)
- [ ] Program flow monitoring, not just an alive watchdog? (§6.4 → `auto-real-time-safety-and-cybersecurity`)
- [ ] WCET bounded and schedulability analysed, including CAN response times? (§5 → `auto-real-time-safety-and-cybersecurity`)
- [ ] Bus load within budget, termination correct? (§3.1 → `auto-architecture-buses-and-autosar`)
- [ ] TARA done; CSMS/SUMS evidence produced for the customer? (§7 → `auto-real-time-safety-and-cybersecurity`)
- [ ] Network segmented between external-facing and control domains? (§7.3 → `auto-real-time-safety-and-cybersecurity`)
- [ ] Bootloader immutable or A/B, signature-verified, power-loss safe? (§9 → `auto-diagnostics-ota-and-adas`)
- [ ] Per-vehicle software provenance recorded for R156? (§7.2 → `auto-real-time-safety-and-cybersecurity`, §9 → `auto-diagnostics-ota-and-adas`)
- [ ] Autocoded code checked for WCET, stack and MISRA? (§11 → `auto-process-testing-domains-and-supply-chain`)
- [ ] MISRA deviations documented and justified? (§11 → `auto-process-testing-domains-and-supply-chain`)
- [ ] Quiescent current budget allocated and measured? (§2.3 → `auto-architecture-buses-and-autosar`)
- [ ] ODD stated explicitly, and behaviour outside it defined? (§10.1 → `auto-diagnostics-ota-and-adas`)

---

## §20. Method

**§1–§6 → `auto-architecture-buses-and-autosar`, `auto-real-time-safety-and-cybersecurity`, §8 → `auto-diagnostics-ota-and-adas`, §9 → `auto-diagnostics-ota-and-adas`, §11–§16 → `auto-process-testing-domains-and-supply-chain` rest on standards and long-stable practice** — **ISO 26262,
ISO 21448, ISO 14229, MISRA, the AUTOSAR specifications, OSEK/VDX, and the CAN
specification** — plus the reference works in §18. ⚠️ **CAN is from 1986, UDS and the ASIL
framework have been stable for over a decade, and the V-model predates all of it. None of
that needed web verification.**

**Scoped to complement**: generic MCU/RTOS/bus material sits in an embedded-IoT reference;
the closest sibling is a flight-software reference, and ⚠️ **§6.4 → `auto-real-time-safety-and-cybersecurity`, §9 → `auto-diagnostics-ota-and-adas` and §12 → `auto-process-testing-domains-and-supply-chain` share
reasoning with it deliberately — safety-critical embedded practice converges across
industries, and the case studies transfer.**

**Two searches were run in August 2026**, confined to the two things that moved:
**the UNECE regulatory layer** and **the zonal/SDV architectural transition.**

**Confidence.** **High** in §1–§6 → `auto-architecture-buses-and-autosar`, `auto-real-time-safety-and-cybersecurity`, §8–§9 → `auto-diagnostics-ota-and-adas` and §11–§14 → `auto-process-testing-domains-and-supply-chain` — standards-based and stable, with the
numbers stated as the standards state them. **High** in §7.2 → `auto-real-time-safety-and-cybersecurity` and §17.1's regulatory
structure: CSMS/SUMS as type-approval conditions, three-year certificate validity, the
69 attack vectors in Annex 5, and R155's relationship to ISO/SAE 21434 are **consistent
across many independent sources including a national approval authority (KBA) and
certification bodies.**

⚠️ **Two deliberate hedges.** **The R155/R156 date sequence is stated inconsistently across
sources** — adoption June 2020, force January 2021, "in force since summer 2022," and
application to all new vehicles from July 2024 all appear. **I have given the sequence with
that caveat rather than asserting one clean timeline; the operationally important fact —
that they are fully in effect and gate type approval — is not in dispute.** ⚠️ **Verify
specific applicability dates for your vehicle category against the UNECE text or your
approval authority.**

**And §17.2's market figures are flagged in place**: adoption percentages, revenue
forecasts and membership growth come from **analyst reports and vendor-adjacent sources
that sell into this transition.** ⚠️ **The direction is corroborated everywhere; the
specific numbers are estimates, not measurements, and none of the engineering content
depends on them.** **§10.4 → `auto-diagnostics-ota-and-adas`'s position — that no accepted sufficient validation methodology
exists for full autonomy — is my assessment, and it is one the industry's own SOTIF
framework implicitly concedes.**
