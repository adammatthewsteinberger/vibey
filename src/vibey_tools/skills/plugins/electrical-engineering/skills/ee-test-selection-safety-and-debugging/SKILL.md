---
name: ee-test-selection-safety-and-debugging
description: "Use when at the bench: multimeters, oscilloscopes and how not to lie to yourself with probing and bandwidth choices, other instruments, reading datasheets and selecting parts with real margins, electrical safety including mains, isolation and energy limits, and a systematic method for debugging hardware that is not working."
---

# Electrical Engineering: Test Equipment, Part Selection, Safety, and Debugging

> **Part 4 of 5** of the *Electrical Engineering* reference (plugin `electrical-engineering`), covering §12–§15. Sibling skills: `ee-fundamentals-components-and-circuit-analysis` (§0–§4), `ee-semiconductors-op-amps-logic-and-power` (§5–§8), `ee-signal-integrity-emc-and-pcb-design` (§9–§11), `ee-reference` (§16–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    parasitics dominate the labelled value** (§2 → `ee-fundamentals-components-and-circuit-analysis`).
> 3. **⚠️ It's the loop area and the edge rate, not the clock frequency.** A 1 MHz signal
>    with 1 ns edges radiates like a 350 MHz signal, because the spectrum is set by the
>    rise time (§9 → `ee-signal-integrity-emc-and-pcb-design`, §10 → `ee-signal-integrity-emc-and-pcb-design`).

---

## §12. Test Equipment

### 12.1 Multimeter
**⚠️ Measure voltage in parallel, current in series.** Putting an ammeter across a
voltage source is a short circuit — **that's what the fuse in your meter is for, and it's
the most common way meters die.**
**⚠️ Input impedance ~10 MΩ loads high-impedance nodes** and shifts what you're measuring.
**True-RMS matters** for anything non-sinusoidal. **Continuity, diode test, and capacitance
modes** are the daily drivers.

### 12.2 Oscilloscope — and how to not lie to yourself
**⚠️ The probe is part of the measurement, and most bad scope readings are probe errors.**
- **Compensate your 10× probe** against the scope's calibration output ⚠️ **every time you
  move it to a different channel or scope** — an uncompensated probe distorts edges and
  you will chase a phantom.
- **⚠️ The ground lead is an inductor.** That long crocodile clip forms a loop with the
  probe tip and **rings on every fast edge** — producing overshoot that isn't in your
  circuit. **For anything fast, use the spring ground tip.** This single habit removes a
  large share of imaginary signal-integrity problems.
- **10× probe** reduces loading (10 MΩ, ~10 pF) at the cost of amplitude —
  ⚠️ **1× loading (1 MΩ, ~100 pF) is enough to change a fast circuit's behaviour.**
- **Bandwidth**: ⚠️ **you need roughly 3–5× the signal's knee frequency** to see edges
  faithfully. A 100 MHz scope shows a 100 MHz square wave as a sine.
- **Sample rate ≥ 5× bandwidth**; watch for **aliasing** on repetitive signals.
- **Triggering** is the skill: edge, pulse-width, and ⚠️ **runt/glitch triggers are how
  you catch the intermittent event you're actually hunting.**
- **⚠️ Scope ground is usually mains earth** — **connecting it to a non-isolated hot node
  creates a short through the earth path** (§14). **Use a differential probe or an
  isolated scope.**

### 12.3 Other instruments
**Logic analyzer** — ⚠️ **the right tool for protocol debugging; a cheap 8-channel unit
with a protocol decoder is one of the best value purchases in the field.**
**Bench supply** — ⚠️ **current limiting is the feature that matters. Set it before you
power a new board and it will save hardware.**
**Function generator**, **spectrum analyzer**, **LCR meter**, **thermal camera**
(⚠️ **finds the hot part instantly — brilliant for locating a short**), **microscope**.

---

## §13. Datasheets and Selection

**⚠️ Read in this order**: absolute maximum ratings (⚠️ **these are *destruction* limits,
not operating conditions — a part operated at abs max is out of spec, not fine**) →
recommended operating conditions → electrical characteristics **with their test
conditions** → typical application circuit → package and thermal → **errata**.

**⚠️ The word "typical" is doing enormous work.** Design to **min/max**, not typical.
**Every spec has test conditions** — a `R_DS(on)` at `V_GS = 10 V` tells you nothing about
your 3.3 V drive (§5.3 → `ee-semiconductors-op-amps-logic-and-power`).

**Selection practicalities**: **derate** (voltage 50%+ on tantalums and electrolytics,
power 50%, current well below saturation), check **temperature range** (commercial /
industrial / automotive), **package** vs your assembly capability, ⚠️ **lifecycle status —
"NRND" or "obsolete" is a design-in you'll regret**, and **second sources**.

**⚠️ Availability is a design constraint.** Check stock at distributors before committing.
A perfect design with a 52-week lead-time part is not a design.

---

## §14. Safety

> **⚠️ GOTCHA — it is current through the body that harms, not voltage, and the threshold
> is far lower than people assume.**
> ```
> ~1 mA      perception
> ~10 mA     ⚠️ "let-go" threshold — above this you may not be able to release the conductor
> ~30 mA     respiratory arrest risk
> ~100 mA    ⚠️ ventricular fibrillation — this is the lethal mechanism, and it is not a
>            large current
> ```
> **Dry skin is ~100 kΩ; wet or broken skin can be ~1 kΩ.** ⚠️ **At 1 kΩ, 120 V gives
> 120 mA. Mains kills, routinely, and the fatal current is small.**

**Mains work**: ⚠️ **if you are not confident, don't.** Use an **isolation transformer**
and **RCD/GFCI**, work one-handed where possible (⚠️ **keeps current out of the
heart-crossing path**), **never work alone on live mains**, and **verify de-energized with
a meter you have just tested on a known-live source.**

**⚠️ Capacitors store lethal energy after power is removed.** Mains-rated bulk caps and
flash/CRT circuits especially. **Discharge through a resistor and verify with a meter.**

**Batteries**: ⚠️ **Li-ion shorted delivers enormous current and can vent, ignite, or
explode.** Never puncture, never charge below 0 °C, and use protection circuitry.
**⚠️ Lead-acid produces hydrogen — no sparks.**

**Other**: **ESD** protection for components (wrist strap, mat) — ⚠️ **you can destroy or,
worse, *partially* damage a part without feeling the discharge, producing an
intermittent field failure**; **soldering** (⚠️ **lead and flux fumes — ventilate**); and
**eye protection when cutting leads.**

---

## §15. Debugging Hardware

**⚠️ The sequence, and it's deliberately unglamorous:**
```
0. ⚠️ POWER OFF and inspect. Backwards parts, solder bridges, cold joints, missing
   components, wrong values. Use magnification. This finds a large share of faults
   before you power anything.
1. Check the rails — ⚠️ EVERY rail, at the load, under load, with a scope not just a DMM.
   Ripple and droop don't show on a multimeter.
2. Current draw sane? ⚠️ Use a current-limited bench supply on first power-up. Way too
   high = short. Way too low = it isn't running.
3. Thermal check — hand or camera. ⚠️ A hot part is a found fault.
4. Clocks and resets present and correct? ⚠️ Nothing else matters if these are wrong.
5. Signals — scope them. Levels, edges, timing. Compare against the datasheet.
6. Bisect: half the circuit at a time. Inject a known-good signal; remove sections.
7. Compare to a known-good board if one exists — ⚠️ the fastest method when available.
```

**⚠️ The rules that keep you honest:**
- **Change one thing at a time.** Under pressure this is the first discipline to go.
- **⚠️ Suspect your measurement setup before you suspect physics.** Probe compensation,
  ground lead, meter mode, and where you clipped the ground are the usual culprits (§12).
- **Connectors, cables, and solder joints first** — ⚠️ **they fail far more often than
  silicon.**
- **⚠️ "It works when I touch it" means a bad joint or a floating input** (§7.4 → `ee-semiconductors-op-amps-logic-and-power`).
- **⚠️ "It works when the lid is off" means thermal.**
- **⚠️ "It fails only at high load" means power delivery, not logic.**
- **⚠️ "It fails only with the long cable" means signal integrity or bus capacitance**
  (§7.3 → `ee-semiconductors-op-amps-logic-and-power`, §9 → `ee-signal-integrity-emc-and-pcb-design`).
- **Write down what you changed and what happened.** You will not remember.
