---
name: logic-devices-transistors-cmos-gates-and-power
description: "Use for the circuit level underneath digital logic: the two layers this subject spans, diodes, transistors used as switches, MOSFET switching behaviour, static CMOS gate construction and why the pull-up and pull-down networks are duals, sizing and drive strength, the other logic families and when they still appear, and where power actually goes in CMOS between dynamic, short-circuit and leakage. Includes the router for the whole digital logic and firmware reference."
---

# Digital Logic and Firmware: The Two Layers, Diodes, Transistors as Switches, MOSFET Switching, Static CMOS Gates, Sizing, Logic Families, and Power in CMOS

> **Part 1 of 5** of the *CMOS, Logic Gates and Firmware Engineering* reference (plugin `digital-logic-and-firmware-engineering`), covering §0–§8. Sibling skills: `logic-standard-cells-boolean-minimization-and-arithmetic` (§9–§13), `logic-sequential-timing-metastability-cdc-and-hdl` (§14–§19), `logic-firmware-boot-root-of-trust-embedded-practice-and-security` (§20–§25), `logic-reference` (§26–§31). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Boolean algebra and CMOS circuit design do not change. Two things are moving. See §26 → `logic-reference` for the Secure Boot certificate expiry, and open-source firmware and silicon roots of trust.

> **⚠️ SCOPE, because this sits between existing neighbours.** ⚠️ **A semiconductor
> reference covers device physics and fabrication; a microarchitecture reference covers how
> gates become processors. Neither covers the two layers here: HOW TRANSISTORS BECOME
> BOOLEAN LOGIC, and HOW A MACHINE GETS FROM POWER-ON TO AN OPERATING SYSTEM.**
>
> **⚠️ These are the two ends of the stack where the abstractions are built, and where they
> most often leak.**
>
> **⚠️ GOTCHA** boxes mark where the textbook idealization and the real circuit diverge.
>
> **The three ideas that organize this document:**
> 1. **⚠️ CMOS COMPUTES BY CONNECTING, NOT BY AMPLIFYING** (§5). **A static CMOS gate is two
>    complementary switch networks, one connecting the output to power and one to ground,
>    never both. Once you see this, gate construction becomes mechanical and the power
>    behaviour becomes obvious.**
> 2. **⚠️ TIMING IS THE REAL CONSTRAINT, NOT LOGIC** (§15 → `logic-sequential-timing-metastability-cdc-and-hdl`, §17 → `logic-sequential-timing-metastability-cdc-and-hdl`). **Getting the Boolean
>    function right is the easy part. Setup and hold violations, clock skew and metastability
>    are what actually make digital systems fail, and they fail intermittently.**
> 3. **⚠️ TRUST IS A CHAIN THAT STARTS BEFORE ANY SOFTWARE RUNS** (§22 → `logic-firmware-boot-root-of-trust-embedded-practice-and-security`, §25 → `logic-firmware-boot-root-of-trust-embedded-practice-and-security`, §26 → `logic-reference`). **Every
>    security property the OS provides rests on firmware that executed first. Firmware is
>    the most privileged and least examined code in the machine.**

---

## §0. Routing

| You want... | Go to |
|---|---|
| The two layers here | §1 |
| **⚠️ Diodes** | **§2** |
| Transistors as switches | §3 |
| MOSFET switching behaviour | §4 |
| **⚠️ Static CMOS gates** | **§5** |
| Sizing and drive strength | §6 |
| Other logic families | §7 |
| **⚠️ Power in CMOS** | **§8** |
| Standard cells | §9 → `logic-standard-cells-boolean-minimization-and-arithmetic` |
| **⚠️ Boolean algebra** | **§10 → `logic-standard-cells-boolean-minimization-and-arithmetic`** |
| Minimization | §11 → `logic-standard-cells-boolean-minimization-and-arithmetic` |
| Combinational blocks | §12 → `logic-standard-cells-boolean-minimization-and-arithmetic` |
| **⚠️ Arithmetic** | **§13 → `logic-standard-cells-boolean-minimization-and-arithmetic`** |
| **⚠️ Latches and flip-flops** | **§14 → `logic-sequential-timing-metastability-cdc-and-hdl`** |
| **⚠️ Timing and metastability** | **§15 → `logic-sequential-timing-metastability-cdc-and-hdl`** |
| State machines | §16 → `logic-sequential-timing-metastability-cdc-and-hdl` |
| **⚠️ Clock domain crossing** | **§17 → `logic-sequential-timing-metastability-cdc-and-hdl`** |
| HDL and synthesis | §18 → `logic-sequential-timing-metastability-cdc-and-hdl` |
| Test and DFT | §19 → `logic-sequential-timing-metastability-cdc-and-hdl` |
| Firmware landscape | §20 → `logic-firmware-boot-root-of-trust-embedded-practice-and-security` |
| **⚠️ The boot sequence** | **§21 → `logic-firmware-boot-root-of-trust-embedded-practice-and-security`** |
| **⚠️ Root of trust** | **§22 → `logic-firmware-boot-root-of-trust-embedded-practice-and-security`** |
| ACPI and platform interfaces | §23 → `logic-firmware-boot-root-of-trust-embedded-practice-and-security` |
| Embedded firmware | §24 → `logic-firmware-boot-root-of-trust-embedded-practice-and-security` |
| **⚠️ Firmware security** | **§25 → `logic-firmware-boot-root-of-trust-embedded-practice-and-security`** |
| **What's live** | **§26 → `logic-reference`** |
| Misconceptions, numbers | §27–§28 → `logic-reference` |
| Sources, quick ref, method | §29–§31 → `logic-reference` |

---

## §1. The Two Layers

```
⚠️ WHERE THIS FILE SITS
   device physics ────────── a semiconductor reference
   ⚠️ TRANSISTORS AS SWITCHES ──── §2-§4     ← here
   ⚠️ CMOS GATES ───────────────── §5-§9     ← here
   ⚠️ BOOLEAN LOGIC ────────────── §10-§13   ← here
   ⚠️ SEQUENTIAL AND TIMING ────── §14-§19   ← here
   microarchitecture ─────── a microarchitecture reference
   ⚠️ FIRMWARE AND BOOT ────────── §20-§25   ← here
   OS and applications ───── elsewhere
⚠️ THE SYMMETRY WORTH NOTICING  ⚠️ both layers are ones people
   treat as solved and invisible — and both are where the
   hardest-to-diagnose failures live. ⚠️ A setup-time violation
   and a firmware bug share a signature: intermittent,
   environment-dependent, and invisible at the layer above
```

---

# PART I — DEVICES AS SWITCHES

## §2. ⚠️ Diodes

```
⚠️ THE BEHAVIOUR  ⚠️ conducts one way, blocks the other.
   ⚠️ Forward drop ~0.7 V for silicon, ~0.3 V for Schottky,
   and the exponential I-V relation means the "0.7 V" is a
   convenient fiction that shifts with current
⚠️ THE TYPES AND WHAT EACH IS FOR
   ⚠️ SIGNAL / RECTIFIER  power conversion, half and full wave
   ⚠️ SCHOTTKY  ⚠️ low forward drop, very fast recovery, higher
      leakage — used where switching speed or drop matters
   ⚠️ ZENER  ⚠️ deliberately operated in REVERSE BREAKDOWN as a
      voltage reference or clamp
   ⚠️ TVS  ⚠️ transient voltage suppression — the ESD protection
      part on every exposed line (see a peripherals reference §18)
   ⚠️ LED  forward-biased emission; ⚠️ needs current limiting,
      because the exponential I-V means a small voltage
      increase destroys it
   ⚠️ PHOTODIODE and solar cell — the same junction run backwards
   ⚠️ VARACTOR  voltage-controlled capacitance, used in tuning
⚠️ THE PRACTICAL USES THAT RECUR  ⚠️ FLYBACK/freewheeling diode
   across any inductive load (⚠️ a relay or motor without one
   destroys the driving transistor) · reverse polarity
   protection · ⚠️ diode-OR for redundant supplies · clamping ·
   level shifting
⚠️ ⚠️ DIODE LOGIC exists (AND/OR from diodes alone) but ⚠️ CANNOT
   INVERT and degrades the signal at every stage — which is
   exactly why active devices are necessary for real logic
```

---

## §3. Transistors as Switches

**⚠️ BJT versus MOSFET**, ⚠️ **and the distinction that matters for logic:**
```
⚠️ BJT  ⚠️ CURRENT-controlled. Base current sets collector
   current. ⚠️ Continuous base current means continuous power —
   which is why bipolar logic families (TTL, ECL) burn power
   even when idle
⚠️ MOSFET  ⚠️ VOLTAGE-controlled via an insulated gate.
   ⚠️ ESSENTIALLY NO DC GATE CURRENT. ⚠️ THIS IS THE PROPERTY
   THAT MADE CMOS WIN — a gate that draws no static current can
   be scaled to billions
⚠️ THE MODES  cutoff (off) · ⚠️ linear/triode (⚠️ acting as a
   resistor — this is the SWITCH-ON region for logic) ·
   saturation (⚠️ constant current — the AMPLIFIER region, which
   digital design mostly passes THROUGH rather than sits in)
⚠️ n-CHANNEL vs p-CHANNEL  ⚠️ nMOS conducts when gate is HIGH;
   pMOS conducts when gate is LOW. ⚠️ This complementary pair is
   the whole basis of §5
⚠️ ⚠️ nMOS PASSES A STRONG 0 AND A WEAK 1; pMOS PASSES A STRONG 1
   AND A WEAK 0. ⚠️ This asymmetry is not a detail — it dictates
   which network goes where in a CMOS gate, and it is why pass
   transistor logic needs care (§7)
```

---

## §4. MOSFET Switching Behaviour

**⚠️ The parasitic capacitances are the whole story of speed**: ⚠️ **gate capacitance must
be charged and discharged to switch the device, and everything a gate drives is capacitance
to the driver.**
**⚠️ Propagation delay** is therefore ⚠️ **roughly the load capacitance divided by the
available drive current — which is why delay depends on FANOUT and on wire length.**
**⚠️ Rise and fall times** and ⚠️ **the danger of slow edges: a slowly-transitioning input
leaves BOTH transistors in the receiving gate partially on, causing SHORT-CIRCUIT current
(§8) and, at the extreme, oscillation.**
**⚠️ The Miller effect** — ⚠️ **gate-drain capacitance appears amplified during the
transition, which is why the switching waveform has a plateau.**
**⚠️ Threshold voltage, body effect, and temperature dependence** — ⚠️ **and the
uncomfortable fact that transistors get SLOWER hot but LEAKIER hot, so the worst case for
timing and the worst case for power are at opposite corners.**
**⚠️ PVT corners** (process, voltage, temperature) — ⚠️ **designs must work at all of them,
which is why sign-off is done at multiple corners rather than nominal.**

---

# PART II — CMOS CIRCUIT DESIGN

## §5. ⚠️ Static CMOS Gates

> **⚠️ The single most useful construction in this file. Once you see it, you can draw any
> logic gate from its Boolean expression mechanically.**
```
⚠️ THE STRUCTURE  ⚠️ every static CMOS gate is TWO NETWORKS
   ⚠️ PULL-UP NETWORK (PUN)  ⚠️ pMOS transistors, connects output
      to VDD
   ⚠️ PULL-DOWN NETWORK (PDN)  ⚠️ nMOS transistors, connects
      output to GND
   ⚠️ THEY ARE COMPLEMENTARY AND MUTUALLY EXCLUSIVE — exactly one
      conducts for any input combination. ⚠️ Both on = short
      circuit; both off = floating output
⚠️ ⚠️ THE CONSTRUCTION RULE
   ⚠️ PDN: SERIES nMOS = AND · PARALLEL nMOS = OR
   ⚠️ PUN: the DUAL — series becomes parallel and vice versa
   ⚠️ The output is INHERENTLY INVERTED
⚠️ ⚠️ THEREFORE NAND AND NOR ARE THE NATURAL GATES, and
   ⚠️ AND and OR are MORE EXPENSIVE than NAND and NOR because
   they are a NAND/NOR followed by an inverter. ⚠️ This is
   backwards from how people learn Boolean algebra, and it is
   why synthesized netlists are full of NANDs
⚠️ THE INVERTER  one pMOS, one nMOS, gates tied together —
   ⚠️ the simplest possible instance of the pattern
⚠️ ⚠️ NAND IS PREFERRED OVER NOR in practice, because NOR puts
   pMOS devices in SERIES — and pMOS is intrinsically weaker
   (lower hole mobility), so a series pMOS stack is slow (§6)
⚠️ COMPLEX GATES  ⚠️ AOI (and-or-invert) and OAI implement
   multi-level functions in ONE gate, which is faster and
   smaller than composing separate gates
⚠️ STACK HEIGHT  ⚠️ practically limited to about 3-4 series
   devices, because series resistance and body effect compound
```

---

## §6. Sizing and Drive Strength

**⚠️ Why pMOS is usually wider**: ⚠️ **hole mobility is roughly 2–3× lower than electron
mobility, so a pMOS must be proportionally wider to match an nMOS's drive.** ⚠️ **A
"balanced" inverter uses that ratio; ⚠️ deliberately unbalanced sizing skews the switching
threshold, which is sometimes what you want.**
**⚠️ Series stacks need upsizing** — ⚠️ **two devices in series each need roughly double
width to match a single device's drive.**
**⚠️ LOGICAL EFFORT** is the design method worth knowing: ⚠️ **it separates a gate's
intrinsic difficulty from its load, giving a systematic way to size a path and to find the
optimal number of stages — and the well-known result is that a fanout of roughly 4 per
stage is near-optimal.**
**⚠️ Buffer insertion and repeaters** — ⚠️ **driving a large load or a long wire directly is
slow; a chain of progressively larger buffers is faster despite adding stages.**
**⚠️ Drive strength in a cell library** (§9 → `logic-standard-cells-boolean-minimization-and-arithmetic`) is exactly this made discrete: ⚠️ **X1, X2, X4
versions of the same logic function.**

---

## §7. Other Logic Families

```
⚠️ PASS TRANSISTOR LOGIC  ⚠️ fewer transistors, and ⚠️ suffers
   the threshold drop of §3 — an nMOS pass gate delivers only
   VDD − Vt. ⚠️ Needs level restoration
⚠️ ⚠️ TRANSMISSION GATE  ⚠️ nMOS and pMOS in PARALLEL, gates
   driven oppositely — ⚠️ passes BOTH levels strongly. ⚠️ The
   standard building block for multiplexers and latches (§14)
⚠️ DYNAMIC / DOMINO LOGIC  ⚠️ precharge then evaluate, using a
   clock. ⚠️ Faster and smaller; ⚠️ vulnerable to charge sharing,
   leakage and noise, needs careful clocking, and is much less
   used than it once was because leakage got worse with scaling
⚠️ LEGACY FAMILIES worth recognizing  ⚠️ TTL (bipolar, fast for
   its day, power-hungry) · ⚠️ ECL (very fast, never off,
   enormous power) · ⚠️ 74-series and 4000-series CMOS, still
   genuinely useful for learning and glue logic
⚠️ ⚠️ LOGIC LEVELS AND INTERFACING  ⚠️ VIL/VIH/VOL/VOH and NOISE
   MARGIN. ⚠️ 3.3 V and 5 V and 1.8 V parts do not simply
   interconnect — ⚠️ level shifting is required, and driving a
   5 V-tolerant-only input from 3.3 V may not reach VIH
⚠️ OPEN DRAIN / OPEN COLLECTOR  ⚠️ needs a pull-up, gives
   wired-AND, and is why I²C works as a multi-drop bus
```

---

## §8. ⚠️ Power in CMOS

```
⚠️ ⚠️ DYNAMIC POWER  P = α · C · V² · f
   ⚠️ α = ACTIVITY FACTOR (fraction of cycles the node switches)
   ⚠️ THE V² TERM is why voltage scaling was the most powerful
   lever ever available — and why its end mattered so much
   (see a semiconductor reference §5)
⚠️ SHORT-CIRCUIT POWER  ⚠️ during a transition BOTH networks are
   briefly partially on. ⚠️ Small if edges are fast, and it
   grows badly with slow edges (§4)
⚠️ ⚠️ STATIC / LEAKAGE POWER  ⚠️ subthreshold conduction, gate
   oxide tunnelling, junction leakage. ⚠️ Negligible in old
   processes, MAJOR in modern ones — and it rises sharply with
   temperature, creating a THERMAL RUNAWAY risk
⚠️ THE TECHNIQUES
   ⚠️ CLOCK GATING  ⚠️ the highest-value one — the clock network
      itself switches every cycle and can be a large fraction of
      dynamic power
   ⚠️ POWER GATING  cut supply to idle blocks, attacking leakage
   ⚠️ MULTI-Vt  ⚠️ high-Vt cells on non-critical paths (slow,
      low leakage), low-Vt only where speed is needed
   ⚠️ DVFS · multiple voltage domains with level shifters ·
      operand isolation
⚠️ ⚠️ THE GLITCH PROBLEM  ⚠️ unbalanced path delays cause spurious
   transitions that do real work and burn real power before
   settling — ⚠️ a meaningful fraction of dynamic power in
   arithmetic-heavy logic
```
