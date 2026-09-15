---
name: embedded-security-safety-and-testing
description: "Use when securing, certifying, testing, or bringing up an embedded device. Covers the threat model for a connected device, cryptography on constrained devices, secure boot and debug lockdown, the 2026 regulatory landscape (EU CRA, RED/EN 18031, IEC 62443, PSA Certified, FDA), a practical security baseline; the functional safety standards map (IEC 61508, ISO 26262, DO-178C, IEC 62304), SIL/ASIL and the quantitative core, firmware techniques that produce safety evidence; the embedded testing pyramid, unit testing firmware, simulation and HIL, static analysis and formal methods, the debugging toolkit, CI/CD for firmware; and board bring-up."
---

# Embedded & IoT: Security, Functional Safety, Testing, and Board Bring-Up

> **Part 4 of 5** of the *Embedded Systems & IoT Controls — Deep Technical Reference* reference (plugin `embedded-iot-controls`), covering §10–§13. Sibling skills: `embedded-silicon-and-firmware-models` (§0–§2), `embedded-languages-realtime-and-patterns` (§3–§5), `embedded-industrial-control-connectivity-and-cloud` (§6–§9), `embedded-reference` (§14–§19). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 → `embedded-reference` for the currency snapshot and what goes stale first.

> **How to read this.** This is a reference, not a tutorial. Sections are independent.
> Three markers appear throughout:
> - **[UNIVERSAL]** — physics, math, or architecture. True regardless of vendor. Trust it.
> - **[VENDOR]** — specific to a chip, SDK, or toolchain. Verify against the datasheet/errata.
> - **[CONTESTED]** — competent engineers disagree. Both cases are presented. Do not pick a side on the reader's behalf.
>
> **⚠️ GOTCHA** boxes mark the failure modes that actually burn people. They are the
> highest-value content in this document.

---

## §10. Security

### 10.1 Threat model for a connected device

Attack surfaces, roughly in order of how often they're actually used:
1. **Default/shared credentials** — the Mirai lesson. Still the #1 real-world IoT
   compromise vector.
2. **Unauthenticated or downgradeable firmware update** — full device takeover, fleet-wide.
3. **Cloud API / companion app** — often weaker than the device; horizontal authorization
   bugs let you control someone else's device by changing an ID.
4. **Exposed debug interfaces** — JTAG/SWD unlocked, UART console with a root shell, test
   pads on the PCB.
5. **Network-facing stack bugs** — Ripple20/URGENT-11-class vulnerabilities in third-party
   TCP/IP stacks that ship inside thousands of products with no SBOM to find them.
6. **Firmware extraction** → hard-coded secrets, shared keys, API endpoints.
7. **Physical/fault injection** — voltage/clock glitching to bypass secure boot, side
   channels to extract keys. Real, and demonstrated against mainstream MCUs.
8. **Supply chain** — a compromised dependency, a malicious contract manufacturer flashing
   extra firmware.

### 10.2 Cryptography on constrained devices

- **Symmetric**: **AES-GCM** or **ChaCha20-Poly1305** (better when there's no AES
  accelerator — it's fast in software on 32-bit cores). Always AEAD; never
  encrypt-without-authenticate.
- **Asymmetric**: **ECC P-256 (secp256r1)** or **Curve25519/Ed25519**. RSA-2048+ is
  painfully slow and large on MCUs; avoid for new designs.
- **Hashing**: SHA-256. SHA-1 and MD5 are dead for security purposes (fine as
  non-security checksums, but use CRC for that).
- **Integrity without security**: **CRC-32** for storage/transport error detection.
  ⚠️ A CRC is **not** a security control — it's trivially forgeable. Philip Koopman's work
  on checksum/CRC selection is the reference for choosing a polynomial with adequate
  Hamming distance for your message length; the default polynomial is often *not* the best
  one for short messages.
- **Hardware accelerators**: use them, but verify constant-time behaviour and that the
  driver doesn't leak keys into general RAM.

**TLS/DTLS on MCUs**: **mbedTLS** (widely integrated, PSA Crypto API), **wolfSSL** (small,
commercially supported, FIPS options), **TinyDTLS** (minimal CoAP use). Footprint reality:
a trimmed TLS 1.2/1.3 client with ECDHE-ECDSA-AES128-GCM needs roughly **20–40 KB flash
and 15–30 KB RAM** — the RAM is dominated by the record buffer (16 KB max record; use
`MBEDTLS_SSL_MAX_CONTENT_LEN` and the max-fragment-length extension to cut it).

> **⚠️ GOTCHA — the certificate validation triad.** Devices routinely fail at one of:
> (a) not validating the chain at all, (b) validating the chain but not the hostname,
> (c) having no reliable clock, so expiry checks pass anything. All three are common.
> Fix (c) by getting time from a trusted source before the first TLS handshake, or by
> using a boot-time-anchored monotonic check plus certificate pinning.

### 10.3 Secure boot and debug lockdown

**Secure boot chain**: immutable ROM verifies the bootloader signature against a public
key hash burned into **eFuses**; the bootloader verifies the application. The root of trust
must be **immutable** — a "secure boot" whose key can be changed by software isn't one.

**Debug port lockdown** is a lifecycle decision:
- Development: open SWD/JTAG.
- Production: **permanently disable** or require authenticated debug (ADAC / Arm Debug
  Authentication, or vendor equivalents like STM32 RDP Level 2).
- **⚠️ GOTCHA**: RDP Level 2 on many STM32 parts is **irreversible** — you cannot ever
  re-open the part, which means you cannot do failure analysis on returns. Plan a
  deliberate policy: a small number of "engineering" units at RDP1, production at RDP2, or
  use authenticated debug unlock where the silicon supports it.
- Remember the **UART console**. A locked JTAG next to an unauthenticated shell on a test
  header is theatre.

**TrustZone-M / TF-M**: partitions the MCU into Secure and Non-Secure worlds with
hardware-enforced boundaries (SAU/IDAU). **Trusted Firmware-M** provides the reference
secure-side implementation with PSA services: Crypto, Internal Trusted Storage, Protected
Storage, Initial Attestation. This is the standards-track answer for "keys and secrets
isolated from application bugs" on M33/M23.

### 10.4 Regulation — the 2026 compliance landscape

This section is time-sensitive. Verify before relying on it.

**EU Cyber Resilience Act (CRA), Regulation (EU) 2024/2847** — horizontal, applies to
essentially every "product with digital elements" placed on the EU market, from any
manufacturer worldwide.
- Entered into force **10/11 December 2024**.
- **11 June 2026** — conformity assessment body notification provisions apply.
- **11 September 2026** — ⚠️ **vulnerability and incident reporting obligations apply.**
  Manufacturers must report **actively exploited vulnerabilities** and **severe incidents**
  via the ENISA **CRA Single Reporting Platform**: **early warning within 24 hours**, full
  notification within 72 hours, final report within 14 days (vulnerabilities, once a fix
  exists) or one month (severe incidents). **This applies to products already on the
  market**, including ones shipped years ago.
- **11 December 2027** — full application: essential cybersecurity requirements, secure-
  by-default configuration, security update provision across the support period,
  **SBOM**, technical documentation, conformity assessment, CE marking.
- The Commission published practical guidance on 27 July 2026.
- **Practical implication for August 2026**: the reporting clock starts in three weeks.
  If a product doesn't have an SBOM, a monitored vulnerability intake channel, a CVE
  triage process, and a named responsible person, that is an *immediate* gap, not a 2027
  gap.

**EU Radio Equipment Directive (RED) Article 3(3)(d)(e)(f)** via Delegated Regulation
2022/30 — **mandatory since 1 August 2025** for internet-connectable radio equipment.
Harmonised standards **EN 18031-1** (network protection → 3.3(d)), **EN 18031-2** (privacy
and personal data → 3.3(e)), **EN 18031-3** (financial fraud → 3.3(f)) were cited in the
OJ in January 2025 **with restrictions** (Implementing Decision (EU) 2025/138).
⚠️ Those restrictions matter: certain clauses (notably around user ability to skip
password setup and some parental-control provisions) **do not confer presumption of
conformity**, so products touching them still need a **Notified Body**. There is **no
grace period** — products non-compliant in August 2025 remain non-compliant now.
EN 18031 maps onto **ETSI EN 303 645** (the consumer IoT baseline) provisions, and is
also the foundation for future CRA harmonised standards.

**Other regimes worth knowing:**
- **ETSI EN 303 645** — the consumer IoT security baseline (no universal default
  passwords, vulnerability disclosure, keep software updated, securely store credentials…).
- **NIST IR 8259 / NISTIR 8425** — US device manufacturer capability guidance; underpins
  the **US Cyber Trust Mark** consumer labelling scheme.
- **UK PSTI Act** — in force; bans default passwords, mandates a disclosure policy and a
  published support period.
- **IEC 62443** — the industrial series. **62443-4-1** = secure development lifecycle for
  product suppliers; **62443-4-2** = component technical requirements (seven Foundational
  Requirements: IAC, UC, SI, DC, RDF, TRE, RA); **62443-3-2** = risk assessment and
  zones/conduits design; **62443-3-3** = system requirements; **62443-2-1** = asset owner
  programme (2nd edition Aug 2024). Security Levels **SL 1–4** are assigned per
  zone/conduit, not per plant. It is referenced by NIS2, TSA pipeline directives, and
  increasingly written directly into procurement contracts — and it is the natural
  technical framework onto which CRA obligations map for industrial products.
- **UNECE R155/R156** — automotive cybersecurity management system and software update
  management system; type-approval prerequisites.
- **FDA premarket cybersecurity guidance / FD&C §524B** — US medical devices must ship an
  SBOM and a vulnerability management plan.
- **SBOM formats**: **SPDX** and **CycloneDX**. **VEX** documents let you state
  "component X contains CVE-Y but this product is not affected because…" — essential once
  you have an SBOM, or you'll drown in irrelevant CVEs.

### 10.5 A practical security baseline

Minimum bar for a connected product in 2026:
- [ ] Unique per-device credentials; **no shared or default passwords, ever**
- [ ] Secure boot with an immutable root of trust
- [ ] Signed OTA with rollback protection and an anti-rollback counter
- [ ] Private keys in a secure element or TrustZone-isolated storage
- [ ] TLS 1.2+ with full chain **and hostname** validation, and a trustworthy clock
- [ ] Debug interfaces locked in production (including UART); documented policy
- [ ] SBOM generated at build time, stored per release, monitored against CVE feeds
- [ ] Published vulnerability disclosure policy + a monitored intake address
- [ ] Documented support period and a working path to ship a patch to every unit
- [ ] Threat model written down and reviewed when the architecture changes
- [ ] Reporting runbook ready for the CRA 24/72-hour clocks

---

## §11. Functional Safety

### 11.1 The standards map

| Standard | Domain | Levels | Notes |
|---|---|---|---|
| **IEC 61508** | Generic / industrial (parent standard) | SIL 1–4 | The root from which most others derive |
| **ISO 26262** | Automotive | ASIL A–D (+QM) | Adds ASIL decomposition, HARA, item definition |
| **IEC 62061 / ISO 13849** | Machinery | SIL CL 1–3 / PL a–e | 13849 uses categories + MTTFd + DC + CCF |
| **IEC 61511** | Process industry | SIL 1–3 | Safety Instrumented Systems; sits on 61508 |
| **DO-178C** | Airborne software | DAL A–E | Objectives-based; **MC/DC coverage required at DAL A/B** |
| **IEC 62304** | Medical device software | Class A/B/C | Lifecycle process standard, not a technique standard |
| **EN 50128 / EN 50657** | Rail | SIL 0–4 | Rail-specific software |
| **ISO 25119 / ISO 13849** | Agricultural machinery | AgPL | |

**[UNIVERSAL] These are *process* standards.** They do not tell you how to write good code;
they tell you what evidence you must produce that you wrote it deliberately, verified it,
and can trace every requirement to a test. The artefacts are the deliverable.

### 11.2 The quantitative core

- **PFD_avg** (probability of failure on demand) for low-demand systems; **PFH**
  (probability of dangerous failure per hour) for high-demand/continuous. SIL bands are
  defined by these numbers — e.g. SIL 2 continuous mode is PFH between 10⁻⁷ and 10⁻⁶ /h.
- **SFF** (safe failure fraction) and **HFT** (hardware fault tolerance) jointly cap the
  achievable SIL for a given architecture.
- **Diagnostic Coverage (DC)** — the fraction of dangerous failures detected by
  diagnostics. This is where firmware earns its keep: RAM march tests, CPU register tests,
  flash CRC, program-flow monitoring, watchdog with window, and plausibility checks all
  raise DC.
- **Architectures**: 1oo1 (no redundancy), **1oo1D** (with diagnostics), 1oo2 (either
  channel can trip — safe but nuisance-trip-prone), 2oo2 (both must agree — available but
  less safe), **2oo3** (voting — the classic high-availability-and-safety compromise).
- **Analysis methods**: **FMEA/FMEDA** (bottom-up, component→effect, produces the failure
  rates that feed PFD), **FTA** (top-down from the hazard), **HAZOP** (guideword-driven
  process hazard study), **LOPA** (layer of protection analysis → determines required SIL).

### 11.3 Firmware techniques that produce safety evidence

- **Memory partitioning with the MPU**: each task gets only the regions it needs.
  This provides **freedom from interference** — the property that lets you run a
  lower-integrity task (comms, UI) alongside a safety task on one MCU without inheriting
  its integrity requirement. Without it, *everything* on the chip must be developed to the
  highest ASIL/SIL present, which is ruinously expensive. This is why FreeRTOS's expanded
  MPU support and Zephyr's user-mode/memory-domain features matter commercially.
- **Lockstep cores** (Cortex-R5F in lockstep, TI Hercules, Infineon AURIX): two cores
  execute identically with a cycle offset; a comparator flags divergence. Gives very high
  DC for the CPU itself.
- **ECC on RAM and flash**; **CRC over the whole program image checked at boot** and
  periodically in the background.
- **Program flow monitoring**: a checksum accumulated across control-flow checkpoints,
  verified against the expected value; catches wild jumps and skipped code.
- **Periodic self-tests**: RAM march-C, CPU register/ALU tests, ADC reference plausibility,
  clock cross-check (verify the main oscillator against an independent low-speed one).
- **Defined safe state** and a bounded **fault reaction time interval**: the total time
  from fault occurrence to reaching the safe state must be less than the process safety
  time. Every diagnostic's detection latency counts against this budget.
- **Tool qualification**: your compiler, static analyzer, and code generator need
  qualification evidence proportionate to their ability to inject or fail to detect an
  error (ISO 26262 TCL, DO-178C tool qualification levels). This is why qualified
  toolchains (compiler vendors' safety packs, **Ferrocene** for Rust) command a premium.

> **⚠️ GOTCHA — "we'll certify it later."** Retrofitting certification onto existing code
> is typically more expensive than rewriting it. Requirements traceability, a documented
> development process, and coverage evidence must exist *from the start*. Deciding at
> month 18 that the product needs SIL 2 is a schedule catastrophe, not a paperwork
> exercise.

---

## §12. Testing, Verification, and Debugging

### 12.1 The testing pyramid, embedded edition

```
        ▲  Field / fleet monitoring (§9.4)   ← the ultimate integration test
       ╱ ╲ HIL — real firmware, real MCU, simulated plant
      ╱   ╲ On-target integration — real hardware, real peripherals
     ╱     ╲ Simulation (Renode, QEMU, Wokwi) — full system, no hardware
    ╱       ╲ Host unit tests with fakes — milliseconds, run on every commit
   ╱_________╲ Static analysis + compiler warnings — run on every save
```
**[UNIVERSAL] The biggest single productivity lever in embedded software is being able to
run most of your tests on a host machine in under 10 seconds.** That requires the
hardware seam from §5.1 → `embedded-languages-realtime-and-patterns`. Teams without it have a 5-minute flash-and-observe loop and
consequently test far less.

### 12.2 Unit testing firmware

**Frameworks**: **Unity + CMock + Ceedling** (C, the classic embedded stack, generates
mocks from headers), **CppUTest** (C/C++, has a memory-leak detector), **GoogleTest**,
**Catch2**, **FFF** (Fake Function Framework — header-only C fakes, minimal ceremony).

**Dual-target build**: the same source compiles for the host (native, with fakes and
sanitizers) and for the target. Enables **ASan/UBSan/TSan on the host**, which find
memory bugs that are invisible on the target until they corrupt something three modules
away.

```c
/* Host test using FFF — no hardware, no vendor SDK, runs in ~1 ms */
#include "fff.h"
DEFINE_FFF_GLOBALS;
FAKE_VALUE_FUNC(int, i2c_write, void*, uint8_t, const uint8_t*, size_t);
FAKE_VALUE_FUNC(int, i2c_read,  void*, uint8_t,       uint8_t*, size_t);

static uint8_t canned[3] = { 0x7E, 0x8C, 0x00 };   /* datasheet's worked example */
static int read_canned(void *c, uint8_t a, uint8_t *d, size_t n) {
    memcpy(d, canned, n); return 0;
}

void test_temp_matches_datasheet_reference(void) {
    i2c_read_fake.custom_fake = read_canned;
    bme280_t dev = { .bus = &fake_bus, .addr = 0x76 };
    int32_t t;
    TEST_ASSERT_EQUAL(0, bme280_read_temp(&dev, &t));
    TEST_ASSERT_INT32_WITHIN(50, 25400, t);        /* 25.4 °C ± 0.05 */
    TEST_ASSERT_EQUAL(1, i2c_write_fake.call_count);
    TEST_ASSERT_EQUAL(0xFA, i2c_write_fake.arg2_history[0][0]);
}
```

**What to test on the host**: protocol parsers (feed them fuzzed input!), state machines
(every transition, including illegal ones), control algorithms (step response against
expected), data transformations, checksum/CRC, compensation math, ring buffers, and
anything with an if-statement. **What you cannot test on the host**: timing, ISR
interactions, actual peripheral behaviour, and silicon errata.

**Fuzzing**: compile your protocol parser for the host and run **libFuzzer** or **AFL++**
against it. Firmware parsers handle untrusted network input and are almost never fuzzed.
This is an unusually high return on a day's work.

**Property-based testing** (theft, RapidCheck, Hypothesis via a Python harness): assert
invariants (e.g. "pushing then popping a ring buffer returns the same bytes in order, for
any sequence of operations") and let the tool find the counterexample. Excellent for
buffers, encoders, and state machines.

### 12.3 Simulation and HIL

- **Renode** — the standout tool: full-system emulation of real boards (multi-node
  networks, sensors, and interconnects included), scriptable, deterministic, runs your
  actual binary in CI. This is how you get "test the firmware on 20 virtual devices with a
  simulated flaky radio" into a pipeline.
- **QEMU** — good for Cortex-A/Linux and some M-profile boards; less peripheral fidelity
  than Renode for MCU work.
- **Wokwi** — browser-based, excellent for ESP32/Arduino/RP2040 prototyping and teaching;
  has a CI mode.
- **HIL (hardware-in-the-loop)** — real MCU running real firmware, with the plant
  simulated in real time (Speedgoat, dSPACE, or a home-built RT Linux box with an FPGA
  I/O card). Essential for motor/vehicle/process control where you cannot test failure
  modes on the real plant. The realistic minimum viable HIL is a second MCU or a Raspberry
  Pi plus a logic-level interface, driving the DUT's inputs and asserting on its outputs.
- **Hardware test farm**: a rack of real boards with programmable power supplies (to test
  brown-out and power-fail-during-write), relay-switched network, and a CI runner. The
  single most valuable piece of infrastructure a firmware team can build after host tests.

### 12.4 Static analysis and formal methods

| Tool | Type | Notes |
|---|---|---|
| Compiler warnings | free | `-Wall -Wextra -Wconversion -Wshadow -Wundef -Werror`. **`-Wconversion` alone catches an enormous amount of integer-promotion breakage.** |
| **clang-tidy** | free | Modernization + bug-prone patterns; integrates with CI |
| **Cppcheck** | free | Decent, low false-positive rate, MISRA add-on |
| **PC-lint Plus / Coverity / Klocwork / Parasoft / LDRA / Axivion** | commercial | MISRA/CERT/AUTOSAR rule sets with certification evidence |
| **Polyspace** | commercial | **Abstract interpretation — proves absence** of certain runtime errors, not just finds them |
| **Frama-C** | free | ACSL contracts, deductive verification of C |
| **CBMC** | free | Bounded model checking; **AWS uses it to prove memory safety of FreeRTOS libraries** |
| **SPARK** | commercial | Provable absence of runtime errors in Ada |
| **TLA+ / Alloy** | free | Model the *protocol*, not the code — finds distributed-state bugs before implementation |

**Coverage**: statement → branch → **MC/DC** (modified condition/decision coverage,
required for DO-178C DAL A/B). On-target coverage needs instrumentation (gcov with a
retrieval channel) or trace hardware (ETM). Host-based coverage is far easier and catches
most logic gaps.

### 12.5 Debugging toolkit

| Tool | Reveals | When |
|---|---|---|
| **SWD/JTAG + GDB** (OpenOCD, pyOCD, **probe-rs**, J-Link) | State, breakpoints, memory | Always |
| **SEGGER RTT** | printf-speed logging with ~µs overhead, no UART pin | Always — vastly better than UART printf |
| **defmt** (Rust) | Interned format strings; tiny wire format | Rust projects |
| **ITM / SWO** | Instrumentation trace, printf, timestamps | Cortex-M3+ |
| **ETM / ETB** | Full instruction trace — reconstruct exactly what executed | Hard bugs, timing analysis; needs trace probe |
| **SystemView / Tracealyzer / Percepio** | RTOS task/ISR timeline, blocking, priority inversion | Any RTOS timing problem — this is the tool |
| **Logic analyzer** (Saleae, sigrok) | Protocol decode, timing | Every bus bring-up |
| **Oscilloscope** | Analog reality: ringing, droop, rise time, glitches | Signal integrity, power |
| **GPIO toggle + scope** | ISR latency, task jitter, WCET | The universal timing measurement |
| **Current probe / Otii / Joulescope** | Real energy per operation | Every battery product |
| **ftrace / perf / LTTng / eBPF** | Linux kernel and userspace latency | Embedded Linux |

**The GPIO-toggle technique** deserves emphasis: set a pin high on ISR entry, low on exit;
scope it. You get latency, duration, jitter, and frequency in one shot, with ~2 cycles of
overhead and no tooling. It is the fastest path from "it feels slow" to a number.

**⚠️ GOTCHA — printf debugging changes timing.** A blocking UART `printf` at 115200 baud
takes ~87 µs *per character*. Putting one in an ISR will change the behaviour you're
trying to observe (and often "fix" the bug). Use RTT, defmt, a ring buffer flushed by a
low-priority task, or GPIO toggles.

### 12.6 CI/CD for firmware

A pipeline that actually works:
```
commit
 ├─ format check (clang-format) + lint (clang-tidy, cppcheck/MISRA)
 ├─ host unit tests (Unity/CppUTest) + ASan/UBSan  ....... < 30 s
 ├─ build all targets in a pinned container ............. reproducible
 ├─ size regression gate (flash/RAM vs baseline, fail on >2% growth)
 ├─ simulation tests (Renode) ........................... minutes
 ├─ SBOM generation (SPDX/CycloneDX) + CVE scan ......... CRA evidence
 ├─ artifact signing (HSM-backed) ....................... never a laptop key
 └─ nightly: hardware test farm + power-fail-during-OTA + soak
```
**Version everything into the binary**: git hash, build date, toolchain version, and a
build-type flag, exposed via a diagnostic command. "Which firmware is this device
running?" must have a definitive answer from the device itself.

---

## §13. Board Bring-Up

A sequence that saves days, in order. Do not skip ahead.

1. **Power rails first, with the MCU unpopulated or held in reset.** Verify every rail's
   voltage, ripple, and sequencing on a scope. A rail that's 200 mV low explains
   everything downstream.
2. **Reset and boot pins**: confirm reset releases and BOOT straps read as intended.
3. **Clock**: probe the crystal (with a low-capacitance probe — a 10 pF probe can stop a
   marginal oscillator). Output the system clock on the MCU's clock-out pin (MCO) and
   measure it. A wrong PLL config invalidates every timing measurement you make later.
4. **Debug connection**: can the probe halt and read the core? If not, check SWD pins
   aren't remapped, power isn't in a low-power mode at boot, and there's no code already
   flashed that disables debug.
5. **Blink an LED** from a bare-metal register write. This proves clock + GPIO + toolchain
   + flash programming + linker script all work. Do not proceed until it blinks.
6. **UART/RTT output**: get a "hello" out. Now you have observability.
7. **Each peripheral, one at a time, in isolation**, verified with a logic analyzer against
   the datasheet's timing diagram — not against "the sensor returned something."
8. **Power measurement**: measure sleep current before you write application code. If
   deep-sleep current is 3 mA instead of 3 µA, you want to know now, while the cause is
   still findable.
9. **Then** integrate.

**Hardware/firmware co-development**: firmware should review the schematic before layout.
The cheap things to catch at that stage: test points on every bus, a debug header that
isn't under a connector, no strapping pins used as outputs, LEDs on spare GPIOs for
state indication, a way to measure current (a 0 Ω shunt in series with the MCU supply),
and pull-ups sized for the actual bus capacitance.
