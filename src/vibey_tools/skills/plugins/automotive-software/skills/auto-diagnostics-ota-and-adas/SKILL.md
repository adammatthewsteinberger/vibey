---
name: auto-diagnostics-ota-and-adas
description: "Use when working on serviceability, updates, or driver assistance: diagnostics including UDS and DTC handling, flashing and over-the-air update with its safety and rollback constraints, and ADAS and autonomy — the SAE levels stated precisely, the perception-planning-control stack, safety architecture for autonomy, and the validation problem that makes it hard."
---

# Automotive Software: Diagnostics, Flashing and OTA, and ADAS and Autonomy

> **Part 3 of 5** of the *Automotive Software* reference (plugin `automotive-software`), covering §8–§10. Sibling skills: `auto-architecture-buses-and-autosar` (§0–§4), `auto-real-time-safety-and-cybersecurity` (§5–§7), `auto-process-testing-domains-and-supply-chain` (§11–§14), `auto-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    approval** (§9, §17.1 → `auto-reference`).

---

## §8. Diagnostics

**⚠️ Diagnostics is a huge fraction of real automotive software work and it's invisible
from outside.**

**OBD-II** — legally mandated emissions diagnostics, standardized PIDs and DTCs, the
connector every scan tool uses.
**UDS (ISO 14229)** — the manufacturer diagnostic protocol, and the one you'll implement:
```
0x10  Diagnostic Session Control     ⚠️ default / programming / extended sessions
0x11  ECU Reset
0x14  Clear Diagnostic Information
0x19  Read DTC Information
0x22  Read Data By Identifier        ⚠️ the workhorse — DIDs
0x2E  Write Data By Identifier
0x27  Security Access                ⚠️ seed/key challenge — see the gotcha
0x28  Communication Control
0x2F  Input Output Control By Identifier   ⚠️ actuator tests
0x31  Routine Control
0x34/36/37  Request Download / Transfer Data / Transfer Exit   ⚠️ flashing (§9)
0x3E  Tester Present                 ⚠️ keeps the session alive
```
**Transport**: **ISO-TP (ISO 15765-2)** segments UDS over CAN; **DoIP (ISO 13400)** carries
it over Ethernet/IP — ⚠️ **which is what makes remote and high-speed diagnostics and
flashing practical.**

> **⚠️ GOTCHA — UDS Security Access (0x27) is not security.** The classic implementation is
> a seed/key exchange with a **fixed algorithm shared across a whole vehicle line**, often
> a simple transformation, and **the key material ends up in tester software that gets
> reverse-engineered.** ⚠️ **Treat legacy 0x27 as an interlock against accidents, not as a
> control against an adversary.** Modern practice moves to certificate-based
> authentication and per-ECU credentials — and R155 (§7.2 → `auto-real-time-safety-and-cybersecurity`) is pushing this.

**DTCs**: a code plus **status bits** (test failed, confirmed, pending, ⚠️ **and the
"confirmed" vs "pending" distinction is what stops a single transient setting a warning
lamp**), **freeze frame** data captured at the time of the fault, and **aging/healing**
counters. **⚠️ Debouncing and maturation logic is where diagnostic bugs live** — a fault
that sets too eagerly produces warranty returns for no-fault-found.

---

## §9. Flashing and OTA

**Reprogramming sequence** (typically UDS-based):
```
Enter programming session → security access → erase → 0x34 request download
  → 0x36 transfer data (blocks) → 0x37 exit → ⚠️ verify checksum/signature
  → reset → verify version
```
**⚠️ The bootloader is the most safety-critical software in the ECU**, because a failure
there is unrecoverable without physical access. **Design rules mirror flight software:**
- **⚠️ The bootloader must be immutable, or A/B redundant with a golden image.**
- **⚠️ A/B (dual-bank) partitions: write to the inactive bank, verify, then switch.**
- **Anti-rollback protection** and **signature verification before activation.**
- **⚠️ Power-loss safety at every step** — the customer will unplug it mid-update.

**OTA adds**: campaign management and staged rollout, **preconditions** (⚠️ **vehicle
parked, in Park, sufficient battery state of charge, not in a tunnel**), driver consent,
bandwidth and cost management, and **fleet-wide rollback.**

**⚠️ And OTA is now regulated (§7.2 → `auto-real-time-safety-and-cybersecurity`).** R156's SUMS requires: a documented **secure update
chain** with authenticity, integrity, **anti-rollback and eligibility checks**; **campaign
planning and approval**; and **post-update validation with records.** ⚠️ **You must be able
to prove, per vehicle, what software it is running and that the update was authorized —
and for updates that affect type-approved functions, the approval itself may need
revisiting.**

**⚠️ The cultural point**: OTA does not make automotive software agile in the web sense.
It makes it **recallable without a service visit**, which is enormous — but the approval,
validation and evidence burden per release is unchanged.

---

## §10. ADAS and Autonomy

### 10.1 The SAE levels — precisely
```
L0  no automation                    L1  ⚠️ ONE of steering OR speed (ACC, or lane keep)
L2  ⚠️ BOTH steering AND speed — but the DRIVER MONITORS AND IS RESPONSIBLE
L3  ⚠️ conditional — the SYSTEM monitors; driver may disengage but must take over
    on request, within a defined ODD
L4  high — no driver takeover needed WITHIN the ODD
L5  full — any condition a human could manage
```
> **⚠️ GOTCHA — the L2/L3 boundary is a liability boundary, not a capability one.**
> **At L2 the human is legally the driver and is monitoring.** At L3, **the system is
> driving and the manufacturer's exposure changes fundamentally.** ⚠️ **This is why
> systems that feel very capable are still marketed and certified as L2** — and why
> marketing language ("Autopilot", "Full Self-Driving (Supervised)") has attracted
> regulatory attention. **The number is about who is responsible when it fails.**
>
> **⚠️ And L3's hand-back problem is genuinely hard**: a driver who has been out of the
> loop needs seconds to regain situational awareness, so the system must detect its own
> impending limit far enough ahead to give a safe transition — **and must have a fallback
> if the driver doesn't respond.**

**ODD (Operational Design Domain)** — ⚠️ **the explicit statement of where the system is
valid**: road types, speeds, weather, lighting, geography. **The ODD is the safety
argument's foundation; a system outside its ODD has no claim at all.**

### 10.2 The stack
```
SENSE     camera, radar (⚠️ robust in weather, poor resolution), lidar (⚠️ precise
          geometry, cost and weather-limited), ultrasonic, IMU, GNSS, HD map
   ↓
PERCEIVE  detection, classification, tracking, ⚠️ SENSOR FUSION
   ↓
LOCALIZE  where am I, to sub-metre — GNSS + map matching + odometry
   ↓
PREDICT   ⚠️ what will other agents do — the hardest part, and the one that
          separates competent systems from dangerous ones
   ↓
PLAN      route → behaviour → trajectory
   ↓
CONTROL   lateral and longitudinal actuation
```
**⚠️ The camera-vs-lidar argument is a genuine engineering disagreement**, not settled:
cameras are cheap and information-rich but must *infer* depth; lidar measures it directly
but costs more and degrades in weather. **Radar is the underrated one — it works when the
others don't, and it directly measures velocity via Doppler.** **Most manufacturers use
fusion; at least one prominent one bet on vision-only.** ⚠️ **The outcome is not yet
decided by evidence available to outsiders.**

### 10.3 Safety architecture for autonomy
**⚠️ The pattern that works, and it mirrors robotics and flight software**: a learned,
high-capability nominal path **inside a classical, verifiable safety envelope.**
- **Redundancy and diversity** — independent sensing paths, so a common failure mode
  doesn't take out perception entirely.
- **Fail-operational, not just fail-safe** — ⚠️ **at L3+ you cannot simply shut down;
  the vehicle must reach a minimal risk condition under its own control**, which means
  redundant power, steering and braking paths.
- **⚠️ A safety monitor / doer-checker**: a simpler, verifiable supervisor that can veto
  the complex planner. **This is how you get an ASIL claim out of a system containing a
  neural network you cannot formally verify.**
- **Driver monitoring** at L2 — ⚠️ **camera-based gaze tracking is now the expected
  implementation, because torque-sensing steering-wheel checks are trivially defeated.**

### 10.4 ⚠️ The validation problem
**You cannot drive your way to a safety claim.** Demonstrating a fatality rate better than
human by brute-force road miles requires **billions of miles** — statistically prohibitive
and impossible to repeat per software revision.

**⚠️ So the industry uses a combination, and none of it is fully satisfying**: scenario-
based testing against catalogues, **simulation at enormous scale** (with the sim-to-real
gap as the standing objection), **shadow mode** (run the system without acting and compare
to the human), disengagement metrics (⚠️ **easily gamed and not comparable across
companies**), and the SOTIF framework (§6.5 → `auto-real-time-safety-and-cybersecurity`) for reasoning about unknowns.
**⚠️ There is no accepted, sufficient validation methodology for full autonomy. Anyone
claiming otherwise is overstating.**
