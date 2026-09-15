---
name: ee-fundamentals-components-and-circuit-analysis
description: "Use when analyzing a circuit or choosing a part: the fundamentals (Ohm's and Kirchhoff's laws, power, Thevenin and Norton equivalents), real component behaviour and parasitics — resistors, capacitors and the dielectric behaviour that surprises everyone, inductors and ferrites, wires, traces and connectors — DC analysis, and AC analysis with impedance, reactance, resonance, Bode plots and filter design. Includes the router for the whole electrical-engineering reference."
---

# Electrical Engineering: Fundamentals, Real Components, and DC and AC Analysis

> **Part 1 of 5** of the *Electrical Engineering* reference (plugin `electrical-engineering`), covering §0–§4. Sibling skills: `ee-semiconductors-op-amps-logic-and-power` (§5–§8), `ee-signal-integrity-emc-and-pcb-design` (§9–§11), `ee-test-selection-safety-and-debugging` (§12–§15), `ee-reference` (§16–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Settled physics and mature practice — Ohm 1827, Kirchhoff 1845, Heaviside's transmission-line theory in the 1880s. Component part numbers change; the physics does not.

> **Scope.** Complements an embedded-IoT reference (MCUs, buses, firmware at the systems
> level), a signal-processing reference (DSP), and a nanotechnology reference (§5,
> semiconductor process). **This is the circuit layer underneath all three** — the physics
> you need when the board does something your code can't explain.
>
> **⚠️ GOTCHA** boxes mark what destroys hardware, injures people, or produces measurements
> that are confidently wrong.
>
> **The three ideas that separate people who debug hardware from people who guess:**
> 1. **⚠️ Current flows in loops, and it always returns.** Every signal has a return path.
>    **Most signal integrity and EMI problems are the return path being somewhere you
>    didn't intend** (§9 → `ee-signal-integrity-emc-and-pcb-design`).
> 2. **⚠️ Every component is also the other two.** A capacitor has inductance and
>    resistance; a wire has both; a resistor has capacitance. **Above a few MHz these
>    parasitics dominate the labelled value** (§2).
> 3. **⚠️ It's the loop area and the edge rate, not the clock frequency.** A 1 MHz signal
>    with 1 ns edges radiates like a 350 MHz signal, because the spectrum is set by the
>    rise time (§9 → `ee-signal-integrity-emc-and-pcb-design`, §10 → `ee-signal-integrity-emc-and-pcb-design`).

---

## §0. Routing

| You want... | Go to |
|---|---|
| **Fundamentals** | **§1** |
| Real component behaviour | §2 |
| DC analysis | §3 |
| AC, impedance, filters | §4 |
| Diodes, transistors, MOSFETs | §5 → `ee-semiconductors-op-amps-logic-and-power` |
| Op-amps | §6 → `ee-semiconductors-op-amps-logic-and-power` |
| **Digital logic and interfacing** | **§7 → `ee-semiconductors-op-amps-logic-and-power`** |
| **Power supplies** | **§8 → `ee-semiconductors-op-amps-logic-and-power`** |
| **Signal integrity and grounding** | **§9 → `ee-signal-integrity-emc-and-pcb-design`** |
| EMC/EMI | §10 → `ee-signal-integrity-emc-and-pcb-design` |
| PCB design | §11 → `ee-signal-integrity-emc-and-pcb-design` |
| **Test equipment** | **§12 → `ee-test-selection-safety-and-debugging`** |
| Datasheets and selection | §13 → `ee-test-selection-safety-and-debugging` |
| **Safety** | **§14 → `ee-test-selection-safety-and-debugging`** |
| Debugging methodology | §15 → `ee-test-selection-safety-and-debugging` |
| Anti-patterns | §16 → `ee-reference` |
| Numbers | §17 → `ee-reference` |
| Books | §18 → `ee-reference` |
| Quick reference | §19 → `ee-reference` |

---

## §1. Fundamentals

```
V = I·R                    Ohm's law
P = V·I = I²R = V²/R       power  ⚠️ the I²R form is why current, not voltage, melts things
Q = C·V                    charge on a capacitor
I = C·dV/dt                ⚠️ capacitor current is proportional to RATE of voltage change
V = L·di/dt                ⚠️ inductor voltage is proportional to RATE of current change
E = ½CV²  ·  E = ½LI²      stored energy
```

**Kirchhoff**: **KCL** — current into a node equals current out (charge conservation).
**KVL** — voltages around a loop sum to zero (energy conservation). ⚠️ **Everything in
circuit analysis is these two plus component laws.**

> **⚠️ GOTCHA — the two `dV/dt` and `di/dt` relations explain most surprises.**
> - **A capacitor resists voltage change**, and **an inductor resists current change.**
> - ⚠️ **Interrupting current through an inductor generates a large voltage spike**
>   (`V = L·di/dt`, and switching gives you a huge `di/dt`). **This is why every relay and
>   motor needs a flyback diode**, and why omitting one destroys the driving transistor
>   — often not immediately, which makes it worse to diagnose.
> - ⚠️ **A discharged capacitor looks like a short circuit at the instant you connect
>   power.** This is inrush current, and it's why large supplies need soft-start.

**Series and parallel**:
```
R series: R₁+R₂     R parallel: (R₁R₂)/(R₁+R₂)
C series: like R parallel  ⚠️ (capacitors combine backwards from resistors)
C parallel: C₁+C₂
L combines like R
```

**Voltage divider** — `V_out = V_in · R₂/(R₁+R₂)`.
⚠️ **Only valid unloaded.** The moment you draw current, the ratio shifts. **Rule of
thumb: the divider's current should be at least 10× the load current**, or use a buffer
(§6 → `ee-semiconductors-op-amps-logic-and-power`). ⚠️ **A divider is not a power supply** — this is a genuinely common beginner error
that produces a rail that sags under load.

---

## §2. Real Components

**⚠️ This section is the one that catches software people out.** The schematic symbol is a
lie of convenience.

### 2.1 Resistors
Real = R + series L + parallel C. **Tolerance** (1% is standard and cheap; 5% for
non-critical), **power rating** (⚠️ **derate to ~50% of rated dissipation for reliability
and temperature**), **temperature coefficient (ppm/°C)**.
**⚠️ Pull-up sizing is a real trade**: too high and noise or leakage wins and edges are
slow; too low and you waste current and stress the driving pin. **10 kΩ is the lazy
default; I²C at 400 kHz typically wants 2.2–4.7 kΩ** because the bus capacitance and the
required rise time set it (§7.3 → `ee-semiconductors-op-amps-logic-and-power`).

### 2.2 Capacitors — and the one that surprises everyone
| Type | Use | ⚠️ Notes |
|---|---|---|
| **Ceramic X7R/X5R** | Decoupling, general | ⚠️ **See the DC bias gotcha below** |
| **Ceramic C0G/NP0** | Timing, filters, precision | Stable, small values only |
| **Ceramic Y5V/Z5U** | ⚠️ **Avoid** | Terrible tempco and bias behaviour |
| **Electrolytic** | Bulk energy storage | ⚠️ **Polarized. Dries out. Finite life, worse hot** |
| **Tantalum** | Compact bulk | ⚠️ **Fails SHORT and can ignite. Derate voltage 50%+** |
| **Film** | Audio, precision, high current | Bulky, excellent |

> **⚠️ GOTCHA — a ceramic capacitor loses most of its capacitance under DC bias.**
> An X5R rated 10 µF at 6.3 V, operated at 5 V, may deliver **2 µF or less.** The
> derating is worse in smaller packages for the same value. ⚠️ **Datasheets bury this in a
> bias-vs-capacitance curve, and it is the reason a decoupling network that looks right on
> the schematic doesn't work on the bench.** **Check the curve, and use a higher voltage
> rating or a larger package than you think you need.**

**⚠️ ESR and ESL are the parameters that matter for decoupling**, not the capacitance
alone. Every capacitor self-resonates at `f = 1/(2π√(LC))`; **above that it is
inductive and no longer a capacitor** (§9.3 → `ee-signal-integrity-emc-and-pcb-design`).

### 2.3 Inductors and ferrites
**Saturation current** — ⚠️ **above it, inductance collapses and current rises without
limit.** **This is the failure mode in switching supplies**, and it's why you size for
peak, not average. **DCR** costs efficiency. **Ferrite beads** are lossy resistors at RF,
specified in **Ω at 100 MHz, not henries** — ⚠️ **and putting one in a power rail with a
big cap after it makes an LC resonant tank that can *amplify* noise at the resonant
frequency.**

### 2.4 Wires, traces, connectors
**⚠️ Every conductor has inductance — roughly 1 nH per mm.** At high `di/dt`, that
matters: 10 nH with a 100 mA/ns edge gives 1 V of ground bounce.
**Trace resistance and current capacity**: 1 oz copper, 10 mil trace ≈ 0.05 Ω/inch;
⚠️ **use an IPC-2221 calculator rather than guessing.**
**⚠️ Connectors and cables are the most common physical failure point** — flex, corrosion,
and contact resistance. **Suspect them early** (§15 → `ee-test-selection-safety-and-debugging`).

---

## §3. DC Analysis

**Thévenin**: any linear network = one voltage source + one series resistance.
**Norton**: current source + parallel resistance. ⚠️ **Thévenin is how you reason about
what a circuit looks like to the next stage**, and it's the formal justification for the
divider-loading rule in §1.

**Maximum power transfer** at `R_load = R_source` — ⚠️ **but that's 50% efficient, so it's
what you want for signals and RF, and emphatically not what you want for power delivery.**

**Node-voltage and mesh-current analysis** are the systematic methods; **superposition**
for multiple sources in linear circuits.

**⚠️ The practical DC skills that matter most**: calculate the current before connecting
anything, compute dissipation (`I²R`) and check it against the part's rating, and
**sanity-check that your ground return can carry what you're pushing.**

---

## §4. AC, Impedance, Filters

**Impedance** is complex resistance:
```
Z_R = R          Z_L = jωL          Z_C = 1/(jωC)          ω = 2πf
|Z| = √(R² + X²)          θ = arctan(X/R)
```
⚠️ **Inductive reactance rises with frequency; capacitive reactance falls.** That single
fact explains filters, decoupling, and most parasitic behaviour.

**RC filters**:
```
f_c = 1/(2πRC)           ⚠️ −3 dB point, 20 dB/decade rolloff for first order
τ = RC                   63% of final value in one τ; ~99% in 5τ
```
**RL**: `τ = L/R`. **Resonance**: `f₀ = 1/(2π√(LC))`, with **Q** setting sharpness.

**Filter types**: low-pass, high-pass, band-pass, notch. **Topologies**: passive RC/LC,
active Sallen-Key (§6 → `ee-semiconductors-op-amps-logic-and-power`), **Butterworth** (⚠️ **maximally flat passband — the default
choice**), Chebyshev (steeper, with passband ripple), Bessel (⚠️ **linear phase — use it
when waveform shape matters**).

**dB**: `20·log₁₀(V₁/V₂)` for voltage, `10·log₁₀(P₁/P₂)` for power.
⚠️ **−3 dB is half power, not half voltage** (half voltage is −6 dB). **This trips people
constantly.**

**⚠️ For a software dev, the most useful AC insight**: **a digital edge is a broadband
signal**. Its spectrum extends to roughly `f_knee ≈ 0.35/t_rise`. **A 1 ns edge has
significant energy to ~350 MHz regardless of how slowly you're clocking it** — which is
why §9 → `ee-signal-integrity-emc-and-pcb-design` and §10 → `ee-signal-integrity-emc-and-pcb-design` apply to "slow" circuits.
