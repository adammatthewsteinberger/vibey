---
name: auto-real-time-safety-and-cybersecurity
description: "Use when safety or security requirements drive the design: real-time scheduling and timing analysis, functional safety under ISO 26262 including how ASIL is determined, ASIL decomposition, the safety lifecycle, the software mechanisms you will actually implement, and SOTIF (ISO 21448); plus cybersecurity under ISO/SAE 21434 and the UN R155 and R156 regulations that gate market access, with the technical measures they imply."
---

# Automotive Software: Real-Time Scheduling, ISO 26262 Functional Safety, and Cybersecurity

> **Part 2 of 5** of the *Automotive Software* reference (plugin `automotive-software`), covering §5–§7. Sibling skills: `auto-architecture-buses-and-autosar` (§0–§4), `auto-diagnostics-ota-and-adas` (§8–§10), `auto-process-testing-domains-and-supply-chain` (§11–§14), `auto-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** CAN, UDS, ASIL and the V-model are stable and decades old; the regulatory layer and the shift to zonal and central compute moved materially. See §17 → `auto-reference` for both, dated.

> **Scope.** Complements an embedded-IoT reference (MCUs, RTOS, buses at the generic
> level), a flight-software reference (the closest sibling discipline — much of §6's
> reasoning is shared), and a robotics-software reference (§14 there, and the autonomy
> stack). **This is the vehicle-specific layer.**
>
> **⚠️ GOTCHA** boxes mark what kills people, fails an audit, or bricks a fleet.
>
> **The three facts that make automotive software its own discipline:**
> 1. **⚠️ Software can kill, and the system knows it.** Steering, braking and propulsion
>    are safety-critical in the formal sense — ISO 26262 assigns them an ASIL, and that
>    rating dictates your architecture, your process, and your evidence (§6).
> 2. **⚠️ The vehicle is a distributed real-time system built by a supply chain, not a
>    team.** An OEM integrates software from dozens of Tier-1s who integrate from Tier-2s.
>    **AUTOSAR exists because of this org chart, not because it's elegant** (§4 → `auto-architecture-buses-and-autosar`, §16 → `auto-reference`).
> 3. **⚠️ It ships for 15 years and you cannot recall it cheaply.** OTA changed the
>    economics but not the liability — **and now an update itself requires regulatory
>    approval** (§9 → `auto-diagnostics-ota-and-adas`, §17.1 → `auto-reference`).

---

## §5. Real-Time and Scheduling

**⚠️ Deadlines are physical.** Engine control is crank-angle-synchronous; a stability-
control loop that misses its period has failed regardless of the answer.

**OSEK/AUTOSAR OS**: **statically configured tasks**, fixed priorities, **basic
(run-to-completion) vs extended (can wait)** tasks, **ISRs category 1 and 2**,
**resources with priority ceiling** (⚠️ **priority inversion is handled by the ceiling
protocol — see a flight-software reference §16.1 for what happens when it isn't**),
**alarms and counters**, **schedule tables** for time-triggered activation.

**⚠️ Analysis, not measurement, is what qualifies a design**: **rate-monotonic
schedulability**, **WCET** (⚠️ **bounded, and therefore caches and speculation are a
problem, not a benefit**), and **CAN worst-case response time analysis** — which combines
queuing delay, arbitration delay from higher-priority messages, and transmission time.

**⚠️ The multicore complication**: partitioning functions across cores, avoiding shared-
resource contention, and **memory protection between partitions of different ASIL.**
**Lockstep cores** for ASIL-D (§6.4).

---

## §6. Functional Safety — ISO 26262

**⚠️ The governing standard, and it structures everything about how automotive software
is built.**

### 6.1 ASIL — and how it's determined
**Hazard Analysis and Risk Assessment (HARA)** rates each hazardous event on three axes:
```
S  Severity     S0 none → S3 life-threatening
E  Exposure     E0 improbable → E4 high probability of the operating situation
C  Controllability  C0 controllable in general → C3 difficult/uncontrollable
                ⚠️ C is about whether the DRIVER can avert the harm
    ↓
ASIL A (lowest) → B → C → D (highest)     plus QM = "quality management only,
                                          no ISO 26262 requirements"
```
**⚠️ The three-axis structure is the part people miss**: a severe hazard that occurs rarely
*and* is easily controlled may still come out QM. **Exposure and controllability genuinely
reduce the rating** — which is why the same failure means different things in different
vehicles.

**Typical ratings**: ⚠️ **steering and braking ASIL D; airbag deployment ASIL D; engine
management typically C or D; adaptive cruise B–C; instrument cluster warnings B;
infotainment QM.**

### 6.2 ASIL decomposition
**⚠️ A powerful and frequently-abused mechanism.** You may decompose an ASIL-D requirement
into two ASIL-B(D) elements — **but only if they are genuinely independent.**
> **⚠️ GOTCHA — decomposition requires demonstrated freedom from interference.**
> Shared power supply, shared clock, shared memory, shared bus, common design error,
> common tooling — ⚠️ **any of these is a common-cause failure that invalidates the
> decomposition.** **A dependent-failure analysis is mandatory, and "we put them on
> different cores of the same chip" is usually not sufficient on its own.**

### 6.3 The safety lifecycle
```
Item definition → HARA → Safety goals (each with an ASIL)
  → Functional Safety Concept → Technical Safety Concept
    → Hardware and Software development (⚠️ V-model, §11)
      → Integration and verification → Safety validation
        → Production, operation, ⚠️ and field monitoring
```
**Work products**: the **safety case** (⚠️ **the argued, evidenced claim that the item is
acceptably safe — this is the deliverable**), FMEA, **FTA**, **FMEDA** for hardware metrics,
and confirmation measures (review, audit, assessment).

**Hardware metrics** for ASIL D: **SPFM ≥ 99%**, **LFM ≥ 90%**, and a **PMHF target of
<10⁻⁸ failures/hour** (⚠️ **10 FIT**). **ASIL B: SPFM ≥ 90%, LFM ≥ 60%, <10⁻⁷/h.**

### 6.4 Software mechanisms you'll actually implement
**Memory protection between partitions**, **program flow monitoring** (⚠️ **a watchdog
that checks the *sequence* of checkpoints, not just aliveness — an alive-but-wrong task is
the failure mode a simple watchdog misses**), **end-to-end (E2E) protection** on
communicated data (⚠️ **CRC + alive counter + data ID, so a receiver detects corruption,
repetition, loss or masquerade regardless of what the network did**), **dual-storage and
inverse-storage of critical variables**, **plausibility checks**, **lockstep cores with
comparator**, and **the safe state** — ⚠️ **every safety concept must define what safe
looks like, and "shut down" is not always safe: losing power steering assist at speed is
itself a hazard.**

**Tool confidence**: ⚠️ **your compiler and code generator need a TCL/TD classification
and qualification evidence.** You cannot silently upgrade a toolchain.

### 6.5 SOTIF — ISO 21448
**⚠️ ISO 26262 covers malfunction. SOTIF covers the case where everything works as
designed and the behaviour is still unsafe** — insufficient specification, or performance
limitations in the intended function.

**⚠️ This is the standard that matters for ADAS and autonomy**, because a perception system
that correctly executes its algorithm and still fails to detect a pedestrian in unusual
lighting has no *malfunction*. The framework works in four areas:
```
Area 1  known, safe          Area 2  ⚠️ known, UNSAFE  → mitigate
Area 3  ⚠️ unknown, unsafe    → the real problem: find them and move them to Area 2
Area 4  unknown, safe
```
**⚠️ The engineering task is shrinking Area 3**, via scenario catalogues, field data, and
enormous validation mileage — **and it does not have a clean termination criterion, which
is the honest difficulty at the centre of autonomous-vehicle validation** (§10.4 → `auto-diagnostics-ota-and-adas`).

---

## §7. Cybersecurity and Regulation

### 7.1 ISO/SAE 21434 — the engineering standard
**Covers the full lifecycle**: cybersecurity governance, **TARA (Threat Analysis and Risk
Assessment)** producing **CAL** ratings, secure development, production, **operations and
incident response**, and decommissioning.
⚠️ **The structural parallel to ISO 26262 is deliberate — TARA is to security what HARA is
to safety.**

### 7.2 ⚠️ UN R155 and R156 — the regulations that gate market access

**[VERSIONED — §17.1 → `auto-reference`.]** **These are not guidance. They are type-approval conditions.**
- **⚠️ R155 requires a certified Cyber Security Management System (CSMS)**; **R156 requires
  a certified Software Update Management System (SUMS).** **Both must be audited and
  certified by a designated technical service** — ⚠️ **without them, the vehicle is not
  granted type approval.**
- ⚠️ **R155 defines what must be achieved; ISO/SAE 21434 defines how**, and the regulation
  explicitly references it as a suitable framework. **But 21434 conformance alone does not
  guarantee R155 approval** — the regulation has its own requirements.
- **⚠️ Annex 5 of R155 enumerates 69 attack vectors that every threat analysis must
  address.** This is a checklist you will be audited against.
- **Certificates are valid for three years** and the OEM must **continuously monitor its
  own fleet and backend** and act on threats.

**⚠️ The consequence for engineering practice**: **security is now a market-access
requirement with an audit trail, applied across the supply chain.** You will be asked for
evidence by your customer because their type approval depends on it (§14 → `auto-process-testing-domains-and-supply-chain`).

### 7.3 Technical measures
**Secure boot** and chain of trust from an **HSM** (hardware security module — a
dedicated core in modern automotive MCUs), **SecOC** for authenticated in-vehicle
messages (§3.1 → `auto-architecture-buses-and-autosar`), **key management and provisioning at production**, **network segmentation
and a gateway** between the external-facing domain and the powertrain/chassis buses,
**intrusion detection (IDPS)**, and **secure diagnostics** — ⚠️ **UDS security access is
notoriously weak in legacy implementations (§8 → `auto-diagnostics-ota-and-adas`) and is a common attack path.**

**⚠️ The attack surface to reason about**: telematics unit and cellular, Bluetooth and
Wi-Fi, infotainment and its media parsers, key fob and passive entry (⚠️ **relay attacks**),
TPMS, charging (⚠️ **the EV charging interface is a new and under-hardened path**), OBD-II
port, and the supply chain itself.
