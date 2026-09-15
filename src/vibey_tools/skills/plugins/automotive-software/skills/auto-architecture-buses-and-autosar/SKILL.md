---
name: auto-architecture-buses-and-autosar
description: "Use when orienting in a vehicle software stack or working below the application layer: what makes automotive software different, E/E architecture and its evolution toward zonal and central compute, mixed criticality on shared compute, power and E/E realities, the buses — CAN and the details that actually matter, Automotive Ethernet and service-oriented communication — and AUTOSAR Classic and Adaptive Platform. Includes the router for the whole automotive-software reference."
---

# Automotive Software: E/E Architecture, Buses and Networking, and AUTOSAR

> **Part 1 of 5** of the *Automotive Software* reference (plugin `automotive-software`), covering §0–§4. Sibling skills: `auto-real-time-safety-and-cybersecurity` (§5–§7), `auto-diagnostics-ota-and-adas` (§8–§10), `auto-process-testing-domains-and-supply-chain` (§11–§14), `auto-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    **AUTOSAR exists because of this org chart, not because it's elegant** (§4, §16 → `auto-reference`).
> 3. **⚠️ It ships for 15 years and you cannot recall it cheaply.** OTA changed the
>    economics but not the liability — **and now an update itself requires regulatory
>    approval** (§9 → `auto-diagnostics-ota-and-adas`, §17.1 → `auto-reference`).

---

## §0. Routing

| You want... | Go to |
|---|---|
| **What makes automotive different** | **§1** |
| E/E architecture and the zonal shift | §2 |
| **Buses and networking** | **§3** |
| AUTOSAR | §4 |
| Real-time and scheduling | §5 → `auto-real-time-safety-and-cybersecurity` |
| **Functional safety (ISO 26262)** | **§6 → `auto-real-time-safety-and-cybersecurity`** |
| SOTIF | §6.5 → `auto-real-time-safety-and-cybersecurity` |
| **Cybersecurity and regulation** | **§7 → `auto-real-time-safety-and-cybersecurity`** |
| Diagnostics (UDS, OBD, DoIP) | §8 → `auto-diagnostics-ota-and-adas` |
| **Flashing and OTA** | **§9 → `auto-diagnostics-ota-and-adas`** |
| ADAS and autonomy | §10 → `auto-diagnostics-ota-and-adas` |
| Development process and toolchain | §11 → `auto-process-testing-domains-and-supply-chain` |
| Testing: MIL/SIL/HIL | §12 → `auto-process-testing-domains-and-supply-chain` |
| The domains: powertrain, chassis, body, infotainment | §13 → `auto-process-testing-domains-and-supply-chain` |
| Supply chain reality | §14 → `auto-process-testing-domains-and-supply-chain` |
| Anti-patterns | §15 → `auto-reference` |
| Numbers | §16 → `auto-reference` |
| **What actually moved** | **§17 → `auto-reference`** |
| Books and resources | §18 → `auto-reference` |
| Quick reference | §19 → `auto-reference` |

---

## §1. What Makes It Different

| Constraint | Consequence |
|---|---|
| **Safety-critical** | ⚠️ **ASIL drives architecture, not the other way round** (§6 → `auto-real-time-safety-and-cybersecurity`) |
| **Hard real-time** | Deadlines are physical — a late airbag decision is a failure (§5 → `auto-real-time-safety-and-cybersecurity`) |
| **15+ year lifetime** | ⚠️ **Toolchain, parts and people all outlive the project** |
| **Extreme cost pressure** | ⚠️ **Cents matter at 500k units. This is why 8-bit MCUs persist** |
| **Harsh environment** | −40 to +125 °C, vibration, EMI, 12 V transients (§16 → `auto-reference`) |
| **Supply chain built** | ⚠️ **You integrate binaries you cannot inspect** (§14 → `auto-process-testing-domains-and-supply-chain`) |
| **Regulated type approval** | ⚠️ **You cannot sell without it, and now that includes software** (§7 → `auto-real-time-safety-and-cybersecurity`) |
| **Recalls are catastrophic** | Millions of units, physical service, reputational damage |

**⚠️ The cultural inversion for someone from web or cloud**: **there is no "roll forward."**
Historically there was no rolling anything — the software shipped in the car and stayed.
**OTA changed that, but conservatively**: a staged, signed, approved, rollback-capable
campaign (§9 → `auto-diagnostics-ota-and-adas`), not a continuous deployment pipeline.

**⚠️ And the honest tension in the industry right now**: Tesla demonstrated that a vehicle
could be treated as a software platform with frequent updates and centralized compute, and
the rest of the industry is restructuring to match — **while carrying legacy architecture,
a supply chain built around distributed ECUs, and type-approval obligations that a
software-first company also has to meet** (§17.2 → `auto-reference`).

---

## §2. E/E Architecture

### 2.1 The evolution
```
DISTRIBUTED     one ECU per function. ⚠️ 100+ ECUs, kilometres of harness,
                a CAN bus per domain, no central compute
      ↓
DOMAIN          controllers per functional domain (powertrain, chassis, body,
                infotainment, ADAS), gateway between them
      ↓
ZONAL           ⚠️ ECUs grouped by PHYSICAL LOCATION (front-left, rear-right...),
                each zone controller aggregates local I/O and power,
                Ethernet backbone to central compute
      ↓
CENTRAL COMPUTE one or few HPC nodes running most functions; zones become
                smart I/O and power distribution
```
**⚠️ Why zonal wins on cost, and it isn't primarily about compute**: **the wiring harness
is among the heaviest and most expensive components in a car**, and it's assembled by
hand. **Grouping by location instead of function collapses harness length dramatically** —
one reported platform target is **>50% ECU reduction and ~40% wiring reduction.**

> **⚠️ GOTCHA — zonal does not remove complexity, it relocates it.** Experience from the
> first large-scale deployments is explicit: **the hardware simplifies and the software
> governance, system architecture and operational maturity demands go up.** ⚠️ **You have
> traded a wiring problem for a distributed-systems problem** — service discovery,
> timing across a network, resource contention on shared compute, and the need for
> hypervisor-level isolation between mixed-criticality functions.

### 2.2 Mixed criticality on shared compute
**⚠️ The central problem of central compute**: an ASIL-D braking function and an
infotainment app on the same SoC must not interfere. **Mechanisms**:
- **Hypervisor partitioning** (⚠️ **spatial and temporal isolation — the standard answer;
  QNX Hypervisor, PikeOS, Xen-based, vendor-specific**).
- **Separate MCU alongside the HPC** for the hard-real-time safety island —
  ⚠️ **very common: a big applications processor plus a lockstep safety MCU.**
- **Lockstep cores** (§6.4 → `auto-real-time-safety-and-cybersecurity`).

### 2.3 Power and E/E realities
**12 V** legacy, **48 V** increasingly for mild hybrid and high-current loads,
**400/800 V** traction. ⚠️ **Load dump, cold crank, and reverse polarity are the
transients every ECU must survive** — see an electrical-engineering reference §8.
**Quiescent current is a hard budget**: ⚠️ **a parked car must not flatten its battery in
weeks, so total sleep current across all ECUs is allocated in milliamps.**

---

## §3. Buses and Networking

| Bus | Rate | Use | ⚠️ Notes |
|---|---|---|---|
| **LIN** | 20 kbit/s | Cheap sensors, mirrors, seats | Single wire, master-slave, ⚠️ **very cheap** |
| **CAN** | 1 Mbit/s | ⚠️ **The workhorse for 30 years** | Broadcast, arbitrated, robust |
| **CAN FD** | ⚠️ **~8 Mbit/s** payload | Modern powertrain/chassis | 64-byte payload vs CAN's 8 |
| **CAN XL** | ~10+ Mbit/s | Emerging | 2048-byte payload |
| **FlexRay** | 10 Mbit/s | ⚠️ **Time-triggered, deterministic** | X-by-wire; largely superseded by Ethernet |
| **MOST** | — | Legacy infotainment | ⚠️ **Effectively dead** |
| **Automotive Ethernet** | 100 Mbit/s – multi-gig | ⚠️ **The backbone** | 100BASE-T1, 1000BASE-T1, 10BASE-T1S |
| **SENT / PSI5** | — | Sensor interfaces | Point-to-point |
| **A2B / I2S** | — | Audio | |

### 3.1 CAN — the details that matter
**⚠️ CAN is a broadcast bus with content-based addressing.** There is no destination
address; **the 11-bit (standard) or 29-bit (extended) identifier names the *message*, not
a node.** Every node sees every frame and filters.

**⚠️ Arbitration is non-destructive and priority is the ID**: nodes transmit
simultaneously; dominant (0) beats recessive (1); **the lower ID wins and continues
without corruption.** **Consequences**: **lower ID = higher priority** and
⚠️ **a flood of high-priority traffic can starve low-priority messages** — worst-case
response time analysis is a real design activity (§5 → `auto-real-time-safety-and-cybersecurity`).

**⚠️ CAN has no authentication and no encryption.** Any node on the bus can transmit any
ID. **This is the root of most vehicle attack research**, and the reason for gateways,
network segmentation, and **SecOC** (Secure Onboard Communication — MAC-authenticated
frames with freshness counters, §7 → `auto-real-time-safety-and-cybersecurity`).

**Higher layers**: **J1939** (commercial vehicles — ⚠️ **standardized PGNs and SPNs, unlike
passenger cars where the mapping is proprietary**), **CANopen** (industrial),
**UDS on CAN via ISO-TP** (§8 → `auto-diagnostics-ota-and-adas`).

**⚠️ Bus load** should stay under ~40–50% for latency headroom. **Termination is 120 Ω at
each end of the bus, and exactly two of them** — ⚠️ **wrong termination is a classic
intermittent-failure cause.**

### 3.2 Automotive Ethernet and service-oriented communication
**⚠️ Single twisted pair** (100BASE-T1 / 1000BASE-T1) rather than the four pairs of office
Ethernet — chosen for weight, cost and EMC. **10BASE-T1S** brings a multidrop segment for
low-speed edge devices.

**⚠️ TSN (Time-Sensitive Networking) is what makes Ethernet acceptable for control
traffic**: time synchronization (802.1AS/gPTP), **traffic shaping and scheduled traffic**
(802.1Qbv), frame preemption (802.1Qbu), and redundancy (802.1CB). **Without TSN,
Ethernet is best-effort and you cannot bound latency.**

**⚠️ The paradigm shift is signal-based → service-based.** Classic CAN broadcasts signals
on a fixed schedule defined in a DBC file. **SOME/IP** (and **DDS** in some stacks) offers
**service discovery, request/response, and publish/subscribe** — ⚠️ **which is what lets
you add or change a function without touching every other ECU's communication matrix.**
**This is the enabling change for OTA-updatable features**, and it brings all the
distributed-systems concerns that come with it.

---

## §4. AUTOSAR

**⚠️ AUTOSAR exists to let an OEM integrate software from many suppliers.** Understand it
as an interface standard for an org chart, and its design choices stop looking arbitrary.

### 4.1 Classic Platform
**For deeply embedded, hard-real-time, safety-critical ECUs on microcontrollers.**
```
Application Layer      Software Components (SWCs) — portable, hardware-agnostic
─────────────────────
RTE (Runtime Env.)     ⚠️ generated glue; SWCs talk only through this
─────────────────────
BSW (Basic Software)   Services / ECU Abstraction / MCAL
─────────────────────
Microcontroller
```
**⚠️ The point of the RTE**: an SWC declares ports and interfaces; the RTE generates the
plumbing. **Whether the partner SWC is on the same core, another core, or another ECU
across CAN is a configuration decision, not a code change.** That relocatability is the
whole value proposition.
**MCAL** is the vendor-supplied hardware abstraction. **OS is OSEK/VDX-derived** —
⚠️ **statically configured, priority-based, no dynamic task creation** (§5 → `auto-real-time-safety-and-cybersecurity`).
**⚠️ Configuration is enormous and tool-driven** (ARXML), which is why AUTOSAR work is so
tooling-dependent.

### 4.2 Adaptive Platform
**For high-performance ECUs: POSIX-based (typically Linux or QNX), C++14+, dynamic.**
- **⚠️ Service-oriented via ara::com over SOME/IP or DDS** — dynamic discovery.
- **Dynamic deployment**: applications can be installed, updated and started at runtime.
- **⚠️ Designed for ADAS, infotainment, and central compute — where compute is plentiful
  and requirements change over the vehicle's life.**

> **⚠️ GOTCHA — Classic and Adaptive coexist, and will for a long time.** They are not
> a migration path where one replaces the other. **Classic remains correct for hard
> real-time, low-power, ASIL-D control on a microcontroller; Adaptive is correct for
> high-compute, updatable, service-oriented functions.** **A modern vehicle runs both**,
> often with a vendor platform unifying them, and **anyone telling you Adaptive replaces
> Classic is selling something.**

**⚠️ AUTOSAR's genuine criticisms are worth knowing**: configuration complexity is
enormous, tooling is expensive and vendor-locked, the generated code is hard to debug,
and iteration is slow. **Some SDV-focused players — Tesla most visibly — largely
bypassed it**, which is only possible if you control the whole stack rather than
integrating a supply chain (§14 → `auto-process-testing-domains-and-supply-chain`).
