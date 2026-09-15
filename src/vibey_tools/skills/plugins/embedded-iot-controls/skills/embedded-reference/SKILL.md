---
name: embedded-reference
description: "Use when weighing contested embedded questions (HAL vs bare registers, C vs C++ vs Rust, RTOS vs superloop, vendor lock-in vs portability, OPC UA vs MQTT/Sparkplug, certification burden vs agility, test on hardware vs host, Zephyr vs FreeRTOS), finding the books and primary documentation practitioners actually cite, learning from the case-study failures everyone should know (Therac-25, Toyota unintended acceleration, 737 MAX, Mars Pathfinder, Mirai), checking whether a vendor or regulatory claim is still current (snapshot verified August 2026), or needing the diagnostic cards — 'why doesn't my peripheral work', 'why does it crash randomly', 'why is battery life bad', numbers worth memorizing, and the firmware review checklist. Companion to the other embedded-iot-controls skills."
---

# Embedded & IoT: Contested Questions, Canon, Case Studies, Currency, and Quick Reference

> **Part 5 of 5** of the *Embedded Systems & IoT Controls — Deep Technical Reference* reference (plugin `embedded-iot-controls`), covering §14–§19. Sibling skills: `embedded-silicon-and-firmware-models` (§0–§2), `embedded-languages-realtime-and-patterns` (§3–§5), `embedded-industrial-control-connectivity-and-cloud` (§6–§9), `embedded-security-safety-and-testing` (§10–§13). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 below for the currency snapshot and what goes stale first.

> **How to read this.** This is a reference, not a tutorial. Sections are independent.
> Three markers appear throughout:
> - **[UNIVERSAL]** — physics, math, or architecture. True regardless of vendor. Trust it.
> - **[VENDOR]** — specific to a chip, SDK, or toolchain. Verify against the datasheet/errata.
> - **[CONTESTED]** — competent engineers disagree. Both cases are presented. Do not pick a side on the reader's behalf.
>
> **⚠️ GOTCHA** boxes mark the failure modes that actually burn people. They are the
> highest-value content in this document.

---

## §14. Contested Questions — present both cases, don't adjudicate

These are the arguments where competent, experienced engineers genuinely disagree. When
asked, give the strongest version of each side and the conditions that favour it. Do not
present one as settled.

### 14.1 HAL vs bare registers
Covered in §2.1 → `embedded-silicon-and-firmware-models`. Favouring factors: HAL when time-to-market, peripheral complexity, and
errata coverage dominate; registers when footprint, worst-case timing, and auditability
dominate. Most shipping products use both, at different layers.

### 14.2 C vs C++ vs Rust
Covered in §3.4 → `embedded-languages-realtime-and-patterns`. The honest summary: **the memory-safety argument for Rust is
technically strong and the ecosystem argument for C is practically strong**, and which
wins depends entirely on your silicon, your team, and whether your product's threat model
or certification path makes memory safety a first-order requirement.

### 14.3 RTOS vs superloop
- *For an RTOS*: independent activities with different rates and blocking I/O become
  tractable; you get standard primitives instead of hand-rolled ones; the ecosystem
  (network stacks, MCUboot, shells) assumes one.
- *For a superloop / time-triggered design*: no context-switch overhead, no per-task
  stacks, no priority inversion, no deadlock, no mutex bugs, and **the timing is
  analyzable by inspection**. A large fraction of shipped embedded products are superloops
  and are more reliable for it. Adding an RTOS to a system that didn't need one adds
  a whole class of concurrency bugs in exchange for nothing.
- The dividing line most people converge on: **an RTOS earns its keep when you have
  genuinely blocking operations at different priorities**, not merely "several things to
  do."

### 14.4 Vendor lock-in vs portability
- *For going all-in on a vendor SDK* (ESP-IDF, nRF Connect SDK, STM32Cube): the
  integration is deep and tested, connectivity stacks come pre-certified, support is real,
  and you ship faster.
- *For a portable core*: silicon shortages happen (2020–23 taught everyone this), pricing
  changes, parts go EOL, and a product line that can't second-source a MCU is a business
  risk. Portability lives in the layered architecture (§5.1 → `embedded-languages-realtime-and-patterns`), not in avoiding the SDK.

### 14.5 OPC UA vs MQTT/Sparkplug for IIoT
Covered in §6.4 → `embedded-industrial-control-connectivity-and-cloud`. Note especially the disputed claim about **OPC UA PubSub adoption** —
proponents describe it as the convergence point; practitioners report limited
production-grade broker implementations and continued dominance of client/server mode as
of 2026. Both observations can be true; be precise about which one you're relying on.

### 14.6 Certification burden vs agility
- *For heavy process*: in safety and regulated domains the artefacts **are** the product;
  retrofitting them is more expensive than producing them (§11.3 → `embedded-security-safety-and-testing`).
- *Against*: process without engineering judgment produces compliant, unsafe systems —
  the Therac-25 and 737 MAX lessons are about organizational and requirements failure, not
  missing paperwork. Certification is necessary and nowhere near sufficient.

### 14.7 Test on hardware vs test on host
- *For hardware-only*: "the only test that counts is on the real thing"; host tests can
  pass while the product fails because your fakes lie.
- *For host-first*: a 10-second feedback loop finds 10× more bugs than a 5-minute one, and
  sanitizers find classes of bug that on-target testing cannot. The synthesis is
  **both**: host tests gate every commit; hardware tests run nightly on a farm.

### 14.8 Zephyr vs FreeRTOS
Covered in §2.3 → `embedded-silicon-and-firmware-models`. Add: for CRA-era products the maintained-security-process argument
favours Zephyr or FreeRTOS-LTS-with-EMP over any unmaintained or in-house kernel — the
"we wrote our own scheduler" option now carries a regulatory cost it didn't in 2015.

---

## §15. The Canon — who and what to cite

### 15.1 Books that practitioners actually reference

| Author | Work | Why it matters |
|---|---|---|
| **Michael Barr** | *Programming Embedded Systems in C and C++*; **Barr Group Embedded C Coding Standard** | The coding standard is a genuinely usable, rule-by-rule document designed to prevent specific bugs |
| **Jack Ganssle** | *The Art of Designing Embedded Systems*; *The Embedded Muse* newsletter | Decades of hard-won engineering-management and firmware-quality wisdom; the standards/discipline advocate |
| **Miro Samek** | *Practical UML Statecharts in C/C++* (QP framework) | The definitive treatment of hierarchical state machines and the active-object model in firmware |
| **Elecia White** | *Making Embedded Systems* (2nd ed.) | The best modern on-ramp; strong on architecture and the engineer's mindset |
| **Joseph Yiu** | *The Definitive Guide to Arm Cortex-M0/M3/M4/M23/M33* | The authoritative Cortex-M architecture reference outside Arm's own TRMs |
| **Philip Koopman** | *Better Embedded System Software*; *Understanding Checksums and CRCs*; the Toyota UA analysis | The safety/reliability authority; his CRC selection work and his expert testimony on Toyota are both foundational |
| **James Grenning** | *Test-Driven Development for Embedded C* | The book that made host-based TDD for firmware a mainstream practice |
| **Bruce Powel Douglass** | *Design Patterns for Embedded Systems in C*; *Real-Time Agility* | Catalogue of RT patterns with concrete trade-off analysis |
| **Christopher Kormanyos** | *Real-Time C++* | The reference for using modern C++ properly on microcontrollers |
| **Jean Labrosse** | *MicroC/OS-II / µC/OS-III* books | Written by the kernel author; the classic "how an RTOS actually works" text |
| **Jonathan Valvano** | *Embedded Systems* series | Rigorous academic treatment with real hardware |
| **Colin Walls** | *Embedded Software: The Works* | Broad practitioner survey |
| **Rust Embedded WG** | *The Embedded Rust Book*, *Discovery*, *The Embedonomicon* | The canonical embedded Rust texts |

### 15.2 Primary documentation (always prefer over blogs)
- **Arm**: Architecture Reference Manuals (ARMv7-M ARM, ARMv8-M ARM), core Technical
  Reference Manuals, CMSIS documentation, and Arm's application notes.
- **Zephyr**: `docs.zephyrproject.org` — release notes, migration guides, devicetree
  bindings index.
- **FreeRTOS**: `freertos.org` — the API docs and the "FreeRTOS on Cortex-M" pages,
  especially the interrupt-priority section.
- **Espressif**: ESP-IDF Programming Guide (versioned per chip), plus the technical
  reference manuals and **errata**.
- **Silicon vendors**: reference manual + datasheet + **errata sheet** (read the errata;
  the bug you're chasing is often in there) + app notes.
- **IETF RFCs** worth knowing by number: **7228** (terminology for constrained-node
  networks — defines Class 0/1/2 devices), **7252** (CoAP), **8323** (CoAP over TCP/TLS),
  **8949** (CBOR), **9019**/**9124** (SUIT firmware update), **9147** (DTLS 1.3),
  **8554** (LMS), **8391** (XMSS).
- **Standards bodies**: MISRA (`misra.org.uk`), IEC/ISO, IEEE 802.1/802.3, Bluetooth SIG,
  CSA (`csa-iot.org`), OPC Foundation, LoRa Alliance, 3GPP.

### 15.3 Ongoing sources worth following
**Interrupt** (Memfault's engineering blog — consistently the best deep firmware writing
being published), **Embedded Artistry** (Phillip Johnston — architecture and process),
**Jack Ganssle's Embedded Muse**, **Beningo Embedded Group** (Jacob Beningo),
**Ferrous Systems** blog (Rust safety-critical), **embedded.fm** podcast (Elecia White),
**The Amp Hour**, **Phil's Lab** (hardware/firmware crossover), **CNX Software** (news),
**/r/embedded** (surprisingly high signal for tooling and part-selection questions),
and the **Rust Blog's** safety-critical series.

---

## §16. Case Studies — the failures everyone should know

| Case | What happened | The transferable lesson |
|---|---|---|
| **Therac-25** (1985–87) | Radiation therapy machine gave massive overdoses; a race condition between the UI task and the setup task, plus a one-byte counter overflow, reachable only when an operator typed quickly. Hardware interlocks had been *removed* in favour of software. | Removing hardware protection because "software will handle it" is the original sin. Also: concurrency bugs are reachable by timing you didn't imagine, and a vendor who dismisses reports as impossible is a systemic failure. |
| **Ariane 5 Flight 501** (1996) | Reused Ariane 4 inertial reference software; a 64-bit float horizontal-velocity value converted to a 16-bit signed int overflowed on a trajectory it was never designed for. The exception handler shut the unit down; the redundant unit ran identical code and failed identically. | **Reuse without re-validating the operating envelope is not reuse.** Identical redundancy protects against random faults, not systematic ones. |
| **Mars Pathfinder** (1997) | Repeated system resets on Mars. A low-priority meteorological task held a mutex on the information bus; a high-priority bus-management task blocked on it; a medium-priority comms task preempted the low-priority one. Classic **priority inversion**; the watchdog reset the system. | Fixed remotely by enabling **priority inheritance** on that mutex. The reason every RTOS mutex now offers PI, and the reason you should ship a debug/trace capability you can enable in the field. |
| **Toyota unintended acceleration** (analysed 2013) | Koopman's expert analysis found ~10,000 global variables, deeply nested logic, stack overflow risk, a single-point-of-failure task, inadequate watchdog design, and recursion — in software controlling throttle. | The watchdog architecture matters as much as the code (§5.9 → `embedded-languages-realtime-and-patterns`). Complexity metrics and global-state count are safety-relevant. Firmware quality is legally discoverable. |
| **Boeing 737 MAX / MCAS** (2018–19) | A flight-control function authorized to command large nose-down trim, driven by a **single** angle-of-attack sensor, with a disagreement alert sold as an option, and inadequate pilot documentation. | Single-sensor authority over a safety-critical actuator is a requirements/architecture failure, not a coding failure. Certification did not catch it. |
| **Stuxnet** (2010) | Targeted Siemens S7 PLCs, altered centrifuge speeds while replaying recorded normal values to the HMI. | Air gaps are a myth; OT is a target; **the HMI can lie**. Drove the creation of the modern ICS security discipline and much of IEC 62443's urgency. |
| **Mirai** (2016) | Botnet built by scanning for IoT devices with **default telnet credentials**; used to launch record DDoS. | Why every regulation since (ETSI 303 645, PSTI, EN 18031, CRA) bans universal default passwords. The simplest possible attack, at enormous scale. |
| **Jeep Cherokee remote hack** (Miller/Valasek, 2015) | Remote compromise via the cellular-connected head unit, then pivot onto the CAN bus to control steering and brakes. 1.4 M vehicle recall. | **Flat internal networks turn one compromised component into total compromise.** The direct ancestor of automotive gateway/domain-controller architectures and UNECE R155. |
| **Ukraine grid attacks** (2015, 2016 Industroyer) | Coordinated intrusion opened breakers; 2016's Industroyer/CrashOverride spoke IEC 60870-5-101/104, IEC 61850, and OPC DA natively. | Attackers learn your protocols. Protocol-aware malware is the norm, not the exception. |
| **Triton / Trisis** (2017) | Malware targeting Triconex **Safety Instrumented Systems** — an attempt to disable the last line of defence against a physical catastrophe. | The safety system is itself a target. Safety and security cannot be separate programmes. |
| **Ripple20 / URGENT-11** (2019–20) | Vulnerabilities in the Treck and VxWorks TCP/IP stacks propagated into hundreds of millions of devices across every industry — most vendors could not tell whether they were affected. | The birth of the SBOM mandate. **You cannot patch what you cannot inventory.** |
| **Colonial Pipeline** (2021) | Ransomware hit IT/billing; operations were shut down precautionarily because the OT/IT boundary couldn't be trusted. | Business continuity, not just technical compromise. The Purdue boundary must be *designed and testable*, not assumed. |
| **Log4Shell** (2021) | A logging library vulnerability with unbounded blast radius across the software supply chain. | Accelerated SBOM/VEX adoption and directly informs the CRA's supply-chain provisions. |

---

## §17. Currency Snapshot — verified August 2026

Everything in this section decays. Re-verify against the primary source before relying on
a date or version number.

| Thing | Status as of Aug 2026 | Decay risk |
|---|---|---|
| **Zephyr** | 4.4 (Apr 2026) stable; **v3.7 is current LTS**; v4.5 due Oct 2026; **v4.6 planned LTS Apr 2027**; 6-month Apr/Oct cadence | High — releases every 6 months |
| **FreeRTOS** | **202604 LTS**, kernel **v11.3.0**; coreMQTT **v5.0.2 adds MQTT v5**; SMP in mainline since v11.0; EMP offers up to 10 extra years of patches | Medium |
| **Linux / PREEMPT_RT** | PREEMPT_RT **mainlined in 6.12** (Sept 2024, x86/arm64/RISC-V); 6.18 is the current LTS; 7.0 released May 2026 | Medium |
| **Yocto** | **6.0 "Wrynose" LTS** (May 2026), Linux 6.18, GCC 15.2, glibc 2.43, supported to **Apr 2030**; explicit SBOM/CVE work for CRA. 5.3 Whinlatter EOL June 2026 | Low (LTS) |
| **ESP-IDF** | **v6.0** (Mar 2026): full support for ESP32-C5/C61, preview H21/H4; picolibc; PSA Crypto replacing legacy mbedTLS APIs; **recovery bootloader on C5/C61**; warnings-as-errors default; legacy ADC/DAC/I2S drivers removed. v6.1 in beta | High |
| **Rust embedded** | **embedded-hal 1.0 stable**; Embassy is the de facto async runtime, compiles on stable since Rust 1.75; probe-rs has largely displaced OpenOCD in Rust workflows; esp-rs is Espressif-official | Medium |
| **Ferrocene** | TÜV SÜD-qualified: ISO 26262 **ASIL D**, IEC 61508 **SIL 3** (supporting SIL 4), IEC 62304 **Class C**; **certified `core` subset at SIL 2 / ASIL B** (25.11.0, extended in 26.02.0); targets incl. Armv7E-M, Armv8-A, QNX | Medium |
| **MISRA** | **MISRA C:2025** (Mar 2025) current, ~225 guidelines, C90–C18; **MISRA C++:2023** current (C++17, ~179 rules, absorbed AUTOSAR C++14); new MISRA C++ in development, no date | Low |
| **EU CRA** | ⚠️ **Reporting obligations start 11 Sept 2026** (24 h / 72 h / 14 d); full application **11 Dec 2027**; Commission guidance published 27 Jul 2026 | **Imminent** |
| **EU RED cyber** | Mandatory since **1 Aug 2025**; EN 18031-1/2/3 harmonised **with restrictions** (Decision 2025/138) — restricted clauses still need a Notified Body | Low |
| **Bluetooth** | Core **6.3** (May 2026); 6.2 (Nov 2025) cut min connection interval to **375 µs**; 6.0 introduced Channel Sounding; twice-yearly cadence | Medium |
| **Matter** | 1.5 (Nov 2025) added cameras/closures/soil sensors; 1.5.1 (Mar 2026) camera refinements; **1.6 reported as current** mid-2026 | High |
| **Cellular IoT** | 2G/3G sunset in most markets; **AT&T shut down NB-IoT**; LTE-M leads roaming; Cat-1/Cat-1bis is the safe global default; RedCap live with **~30 operators in 21 countries** (early 2026), broader 2027–28; **SGP.32 eSIM** accelerating | Medium |
| **Edge AI** | LiteRT-for-Microcontrollers still the most-used MCU runtime; ExecuTorch growing (best with NPUs); **Ethos-U85** adds transformer support + TOSA; ONNX + INT8 the de facto interchange | Medium |
| **Azure IoT** | IoT Hub + **IoT Operations** (Arc/K8s edge, MQTT broker, OPC UA connectors, 72 h offline); releases 2510, 2603 GA'd persistence, X.509 via Device Registry, no-code dataflow graphs. IoT Central retirement notice was **retracted as erroneous** — verify current status | High |
| **AWS IoT** | IoT Core + Greengrass **v2**; ⚠️ **Greengrass V1 end of support 7 Oct 2026** | Medium |
| **Google Cloud IoT Core** | **Retired 16 Aug 2023.** No managed replacement on GCP | Settled |
| **Single-pair Ethernet** | IEEE 802.3cg: 10BASE-T1L (1000 m, 10 Mbps) and 10BASE-T1S (multidrop, ~25 m); **Ethernet-APL** builds on T1L for intrinsically-safe process (trunk-and-spur, ~1000 m, ~50 devices, ~500 mW/spur); 10BASE-T1M and 100BASE-T1L in progress | Medium |

**What goes stale fastest**, in order: cloud platform service names and retirement dates;
Matter/Bluetooth spec versions; vendor SDK major versions; regulatory deadlines. **What
essentially never goes stale**: §1 → `embedded-silicon-and-firmware-models` (silicon fundamentals), §4 → `embedded-languages-realtime-and-patterns` (concurrency), §5 → `embedded-languages-realtime-and-patterns` (patterns),
§7 → `embedded-industrial-control-connectivity-and-cloud` (control theory), §16 (case studies).

---

## §18. Quick Reference Cards

### 18.1 "Why doesn't my peripheral work?" — in diagnostic order
1. Is the **peripheral clock enabled**? (+ dummy read-back after enabling)
2. Is the **pin muxed** to the right alternate function, at the right speed/pull?
3. Is the peripheral **out of reset** and **enabled**?
4. For SPI: **right mode** (try all four). For I²C: **pull-ups sized**, right 7-bit address
   (shifted or not — datasheets disagree).
5. Is the **interrupt enabled** in both the peripheral **and** the NVIC?
6. Is the **ISR name** exactly the weak symbol from the startup file? (A typo silently
   leaves the default infinite-loop handler in the vector table.)
7. Is **DMA** configured with the right stream/channel/request, direction, and increment
   modes — and is the buffer **32-byte aligned and cache-maintained** on an M7?
8. Scope it. The bus either has edges or it doesn't.

### 18.2 "Why does it crash randomly?"
Stack overflow → interrupt priority misconfiguration (FreeRTOS `configMAX_SYSCALL...`) →
race on a shared variable → buffer overrun → uninitialized pointer/variable → cache
coherency with DMA → power supply droop/brown-out → flash corruption from an unsafe write
→ hardware errata. Enable the specific fault handlers (§5.8 → `embedded-languages-realtime-and-patterns`) and MPU stack guards before
guessing.

### 18.3 "Why is battery life bad?"
Measure first, with a current probe, at µs resolution. Then check: never actually entering
deep sleep (a peripheral or debugger holds a clock domain); tickless idle not enabled;
floating GPIOs; regulator/pull-up quiescent current; radio interval too aggressive;
retries because of poor RF; a chatty logging path; wake-up sources firing more often than
you think.

### 18.4 Numbers worth memorizing
- Cortex-M exception entry: **~12 cycles** (16 with FP stacking); tail-chained: **~6**.
- 32-bit ms counter rolls over at **49.7 days**; 32-bit µs at **71.6 minutes**.
- I²C standard/fast/fast+/high-speed: **100 k / 400 k / 1 M / 3.4 M**.
- CAN classic max **1 Mbps**; CAN-FD data phase up to **8 Mbps**.
- BLE connection interval range **7.5 ms – 4 s** (1.25 ms units); **375 µs** minimum from
  Bluetooth 6.2.
- Default BLE ATT MTU **23 bytes** (20 payload) until negotiated.
- LoRaWAN EU868 duty cycle typically **1%** per sub-band — a legal limit.
- MQTT QoS 1 = 2 messages; QoS 2 = 4 messages.
- Rate-monotonic utilization bound: **69.3%** as N→∞.
- Control loop sampling: **10–20×** the desired closed-loop bandwidth.
- Cascade loops: each inner loop **5–10×** faster than the one enclosing it.
- Cache line on Cortex-M7: **32 bytes** — align every DMA buffer to it.
- TLS 1.2/1.3 client on an MCU: roughly **20–40 KB flash, 15–30 KB RAM**.
- LiteRT-Micro core runtime: **~16 KB** on Cortex-M3.
- UART at 115200: **~87 µs per character**. Never in an ISR.

### 18.5 Review checklist for someone else's firmware
- [ ] Is there a hardware seam that makes logic host-testable? (§5.1 → `embedded-languages-realtime-and-patterns`)
- [ ] Any `delay()`, blocking call, or `malloc` in a real-time path? (§5.10 → `embedded-languages-realtime-and-patterns`)
- [ ] Every `while(!flag)` bounded by a timeout?
- [ ] Every return code checked?
- [ ] Time comparisons rollover-safe? (§5.5 → `embedded-languages-realtime-and-patterns`)
- [ ] ISRs short, non-blocking, correct `FromISR` APIs, correct priorities? (§5.7 → `embedded-languages-realtime-and-patterns`)
- [ ] Shared variables `volatile` **and** atomic/locked? (§4.3 → `embedded-languages-realtime-and-patterns`)
- [ ] Mutexes (with PI) for locking, not binary semaphores? (§2.4 → `embedded-silicon-and-firmware-models`)
- [ ] Watchdog supervised, not blindly kicked? (§5.9 → `embedded-languages-realtime-and-patterns`)
- [ ] Fault handler captures PC/LR/CFSR and persists it? (§5.8 → `embedded-languages-realtime-and-patterns`)
- [ ] Stack sizes justified by high-water marks + MPU guards? (§1.2 → `embedded-silicon-and-firmware-models`)
- [ ] DMA buffers aligned and cache-maintained (M7)? (§1.2 → `embedded-silicon-and-firmware-models`)
- [ ] Secrets not in flash; OTA signed with rollback protection? (§9.3 → `embedded-industrial-control-connectivity-and-cloud`, §10 → `embedded-security-safety-and-testing`)
- [ ] Build reproducible, versioned, SBOM emitted? (§12.6 → `embedded-security-safety-and-testing`)

---

## §19. Sources and Method

**Method note.** This document was assembled as a narrative (not systematic) review.
Durable engineering content (§1 → `embedded-silicon-and-firmware-models`, §4 → `embedded-languages-realtime-and-patterns`, §5 → `embedded-languages-realtime-and-patterns`, §7 → `embedded-industrial-control-connectivity-and-cloud`, §11 → `embedded-security-safety-and-testing`, §16) is synthesized from established
practice and the canonical literature in §15. Every **time-sensitive** claim — versions,
dates, regulatory deadlines, product status — was verified against a primary or
near-primary source in **August 2026** and is flagged in §17 with a decay-risk rating.
Where practitioners disagree, §14 presents both cases rather than adjudicating, and
disputed claims (notably OPC UA PubSub adoption and Azure IoT Central's status) are
marked as disputed in place.

**Search log** (queries run, August 2026): Zephyr LTS status · embedded-hal 1.0 / Embassy /
RTIC ecosystem · EU CRA deadlines · Matter specification releases · Bluetooth Core
versions · Azure IoT Central/Hub/Operations status · MISRA C:2025 and C++:2023 · EN 18031
and the RED delegated act · Unified Namespace / Sparkplug B / OPC UA · TinyML runtimes and
Ethos-U · FreeRTOS LTS and kernel versions · ESP-IDF v6.0 and RISC-V ESP32 parts ·
MCUboot/SUIT/post-quantum firmware signing · PREEMPT_RT mainlining and Yocto releases ·
Ferrocene safety qualification · IEC 62443 parts and current practice · cellular IoT
(NB-IoT/LTE-M/RedCap) status · single-pair Ethernet and Ethernet-APL · AWS IoT
Core/Greengrass status.

**Primary sources consulted (selected):**
- Zephyr Project release documentation and release-management wiki — docs.zephyrproject.org
- FreeRTOS 202604 LTS announcement (AWS) and FreeRTOS-Kernel release notes — freertos.org, github.com/FreeRTOS
- European Commission, Cyber Resilience Act and CRA reporting obligations — digital-strategy.ec.europa.eu
- CEN-CENELEC and Commission Implementing Decision (EU) 2025/138 on EN 18031 harmonisation
- MISRA Consortium — misra.org.uk (MISRA C and MISRA C++ pages)
- Bluetooth SIG — bluetooth.com (Core 6.0/6.2 feature overviews and release blogs)
- Connectivity Standards Alliance — csa-iot.org (Matter 1.5, 1.5.1 releases)
- Microsoft Learn / Azure IoT Operations documentation and release notes; Microsoft Tech Community
- AWS IoT Greengrass documentation (V1 end-of-support notice)
- Espressif — ESP-IDF v6.0 announcement and Programming Guide
- Yocto Project release notes 6.0 (Wrynose)
- Ferrous Systems — Ferrocene qualification announcements and release notes
- Arm Developer — Cortex-M and Ethos-U edge AI documentation
- NIST SP 800-208; NSA CNSA 2.0 advisory; IETF RFCs 9019, 9124, 8554, 8391
- Linux Foundation realtime wiki; Linux 6.12 release coverage
- Embassy and rust-embedded working group documentation

**Confidence statement.** High confidence in §1–§8 → `embedded-silicon-and-firmware-models`, `embedded-industrial-control-connectivity-and-cloud`, §11–§13 → `embedded-security-safety-and-testing`, §15–§16 and §18 (durable
engineering and well-documented history). High confidence in §17's verified items as of
the stated date. Moderate confidence in market-adoption characterizations (§6.4 → `embedded-industrial-control-connectivity-and-cloud`, §8.1 → `embedded-industrial-control-connectivity-and-cloud`,
§8.3 → `embedded-industrial-control-connectivity-and-cloud`) — these rest partly on vendor and practitioner commentary, where incentives differ;
they are stated as tendencies, not measurements.
