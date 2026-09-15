---
name: auto-process-testing-domains-and-supply-chain
description: "Use when dealing with how automotive software actually gets built and shipped: process and toolchain including ASPICE and the V-model, testing from unit through hardware-in-the-loop and vehicle-level validation, the vehicle domains (powertrain, chassis, body, infotainment, ADAS) and their differing constraints, and the supply chain reality of OEMs, tier-one suppliers and who actually writes the code."
---

# Automotive Software: Process and Toolchain, Testing, the Domains, and Supply Chain

> **Part 4 of 5** of the *Automotive Software* reference (plugin `automotive-software`), covering §11–§14. Sibling skills: `auto-architecture-buses-and-autosar` (§0–§4), `auto-real-time-safety-and-cybersecurity` (§5–§7), `auto-diagnostics-ota-and-adas` (§8–§10), `auto-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** CAN, UDS, ASIL and the V-model are stable and decades old; the regulatory layer and the shift to zonal and central compute moved materially. See §17 → `auto-reference` for both, dated.

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
>    **AUTOSAR exists because of this org chart, not because it's elegant** (§4 → `auto-architecture-buses-and-autosar`, §16 → `auto-reference`).
> 3. **⚠️ It ships for 15 years and you cannot recall it cheaply.** OTA changed the
>    economics but not the liability — **and now an update itself requires regulatory
>    approval** (§9 → `auto-diagnostics-ota-and-adas`, §17.1 → `auto-reference`).

---

## §11. Process and Toolchain

**⚠️ The V-model dominates because ISO 26262 requires traceable verification at every
level** — and it is more compatible with iteration than its reputation suggests.
```
Requirements ─────────────────────────────────► Validation
  Architecture ───────────────────────────► System test
    Design ──────────────────────────► Integration test
      Implementation ──────────► Unit test
```
**Each left-side activity has a corresponding right-side verification, and traceability
runs both ways.** ⚠️ **Traceability is what auditors check.**

**Automotive SPICE (ASPICE)** — the process assessment model. ⚠️ **OEMs routinely require
Tier-1s to demonstrate ASPICE Level 2 or 3**, which makes it a commercial requirement, not
just a quality aspiration.

**Model-based development**: **Simulink/Stateflow** or **ASCET**, with **autocoding**
(⚠️ **Embedded Coder and TargetLink are qualified for safety-critical use — the
qualification is why they're used**). **The model is the specification and it's
executable.** ⚠️ **But generated code's WCET, stack usage and MISRA conformance still need
checking — autocoding does not exempt you** (§5 → `auto-real-time-safety-and-cybersecurity`).

**Coding standards**: **MISRA C:2012** (⚠️ **the automotive standard, with a formal
deviation process — documented deviations are acceptable, undocumented ones are a
finding**), **MISRA C++** and **AUTOSAR C++14** (⚠️ **now merged into MISRA C++:2023**).
**Static analysis** (Polyspace, Coverity, QAC, Astrée) is expected, not optional.

**Tooling reality**: **Vector** (CANoe, CANalyzer, DaVinci — ⚠️ **near-ubiquitous**),
**dSPACE** and **ETAS** (HIL, calibration, INCA), **Lauterbach TRACE32** (debug),
**Elektrobit**, **Green Hills** and **QNX** (RTOS/hypervisor), **PTC/Polarion/DOORS**
(requirements). ⚠️ **This toolchain is expensive and vendor-locked, and it is a real
barrier to entry for the industry — which is part of why the SDV movement has an
open-source counter-current** (Eclipse SDV, COVESA, SOAFEE).

---

## §12. Testing

```
MIL   Model in the loop        the model against a plant model
SIL   Software in the loop     ⚠️ generated code on a host — catches codegen issues
PIL   Processor in the loop    on the target processor, ⚠️ catches WCET/numeric issues
HIL   Hardware in the loop     ⚠️ real ECU, simulated vehicle in real time
                               THE workhorse of automotive validation
VIL / test bench / proving ground / fleet
```
**⚠️ HIL is where automotive testing actually happens**: the real ECU with real I/O, driven
by a real-time plant model, with **fault injection** — open circuits, shorts to battery and
ground, sensor drift, bus errors. **You can test failure modes that would be dangerous or
destructive on a real vehicle.**

**Other essentials**: **restbus simulation** (⚠️ **simulate every other ECU so you can test
one in isolation — indispensable in a supply chain**), **CAN/Ethernet trace analysis**,
**coverage** (⚠️ **MC/DC required at ASIL D**), **fault injection for safety-mechanism
validation**, **EMC and environmental qualification**, and **durability**.

---

## §13. The Domains

| Domain | Typical ASIL | Character |
|---|---|---|
| **Powertrain/propulsion** | C–D | ⚠️ **Hard real-time, crank-synchronous, heavy calibration** |
| **Chassis** (ABS/ESC/steering) | ⚠️ **D** | Fast control loops, fail-operational for by-wire |
| **Body** (lights, doors, HVAC) | QM–B | ⚠️ **Enormous variant complexity, LIN-heavy** |
| **Infotainment** | QM | ⚠️ **Android Automotive / Linux; consumer expectations, automotive lifetime** |
| **ADAS** | B–D | §10 → `auto-diagnostics-ota-and-adas` |
| **Telematics** | QM–B | ⚠️ **The internet-facing attack surface** (§7.3 → `auto-real-time-safety-and-cybersecurity`) |
| **Battery management (EV)** | ⚠️ **C–D** | Cell balancing, SOC/SOH estimation, thermal, contactor control |

**⚠️ Calibration is an automotive-specific concept worth understanding**: powertrain
software ships with thousands of tunable parameters (maps, curves, thresholds) that are
**calibrated per engine/vehicle variant** and stored separately from code. **Calibration
engineers are a distinct discipline**, and ⚠️ **the calibration dataset is often larger and
more valuable than the code.**

**⚠️ Variant handling is a hidden monster**: one platform, dozens of markets, trim levels,
engine options, and regulatory variants. **Preprocessor-driven variant explosion is a real
maintainability crisis**, and feature-model-based configuration is the mitigation.

---

## §14. Supply Chain Reality

```
OEM        (VW, Toyota, Ford, GM, Tesla...)  — integrates, owns type approval
Tier 1     (Bosch, Continental, ZF, Denso, Aptiv) — delivers ECUs and systems
Tier 2     silicon, software stacks, tools (NXP, Infineon, Renesas, TI, Vector, EB)
```
**⚠️ The consequences for how you work:**
- **You integrate binaries and configurations you cannot inspect**, with an interface
  contract and a test suite. **Debugging across an organizational boundary is slow.**
- ⚠️ **Requirements flow down and evidence flows up.** Your customer's type approval (§7.2 → `auto-real-time-safety-and-cybersecurity`)
  and ASPICE rating depend on artifacts you produce, which is why documentation demands
  feel disproportionate from inside a supplier.
- **⚠️ The OEM historically owned the architecture and integration, and the Tier-1 owned
  the software.** **The SDV shift is OEMs in-sourcing software** to control the platform —
  which is restructuring the industry and is genuinely contested commercially.
- **New entrants** — NVIDIA, Qualcomm — ⚠️ **supply central compute directly to OEMs,
  bypassing the traditional Tier-1 relationship.**

**⚠️ And the Tesla contrast worth understanding properly**: vertical integration removes
the coordination problem that AUTOSAR exists to solve, which is why a company controlling
its own silicon, architecture and software can move faster. ⚠️ **It does not exempt them
from ISO 26262, R155/R156, or type approval** — the regulatory floor is the same. **The
speed advantage is organizational, not regulatory.**
