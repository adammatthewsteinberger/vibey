---
name: ee-signal-integrity-emc-and-pcb-design
description: "Use when a board misbehaves for reasons the schematic does not explain: the return current principle, transmission lines and reflections, decoupling done properly, grounding and ground planes, EMC and EMI — emissions, susceptibility, and what actually passes a test — and PCB design including stack-up, routing, thermal relief and manufacturability."
---

# Electrical Engineering: Signal Integrity, Grounding, EMC, and PCB Design

> **Part 3 of 5** of the *Electrical Engineering* reference (plugin `electrical-engineering`), covering §9–§11. Sibling skills: `ee-fundamentals-components-and-circuit-analysis` (§0–§4), `ee-semiconductors-op-amps-logic-and-power` (§5–§8), `ee-test-selection-safety-and-debugging` (§12–§15), `ee-reference` (§16–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    didn't intend** (§9).
> 2. **⚠️ Every component is also the other two.** A capacitor has inductance and
>    resistance; a wire has both; a resistor has capacitance. **Above a few MHz these
>    parasitics dominate the labelled value** (§2 → `ee-fundamentals-components-and-circuit-analysis`).
> 3. **⚠️ It's the loop area and the edge rate, not the clock frequency.** A 1 MHz signal
>    with 1 ns edges radiates like a 350 MHz signal, because the spectrum is set by the
>    rise time (§9, §10).

---

## §9. Signal Integrity and Grounding

### 9.1 ⚠️ The return current principle
**Current flows in loops.** At DC, return current takes the path of least *resistance*.
**⚠️ At high frequency, it takes the path of least *inductance* — which is directly under
the trace.**

> **⚠️ GOTCHA — this is the single most important idea in PCB design, and it explains
> most EMI and crosstalk.** **A slot or split in the ground plane under a fast trace
> forces the return current to detour around it**, creating a large loop. **That loop is
> an antenna.** It radiates, it picks up noise, and it adds inductance that ruins your
> signal. **Never route a fast signal across a plane split.**

### 9.2 Transmission lines
**⚠️ A trace behaves as a transmission line when the signal's rise time is comparable to
its propagation delay.** Rule of thumb: **treat it as a transmission line if trace length
> `t_rise × v/6`** — practically, **above roughly 1–2 inches for nanosecond edges.**

**Propagation** ≈ **6 in/ns in FR4** (≈ 150 ps/inch). **Characteristic impedance `Z₀`**
set by geometry and dielectric — typically **50 Ω single-ended, 90–100 Ω differential.**
**Reflection coefficient `Γ = (Z_L − Z₀)/(Z_L + Z₀)`** — ⚠️ **impedance mismatch reflects
energy, producing ringing, overshoot, and false clocking.**
**Termination**: series (at the source, ⚠️ **the cheapest and most common fix for point-to-
point**), parallel, Thévenin, AC.

### 9.3 Decoupling — done properly
**⚠️ The purpose is to supply transient current locally, because the supply is too far away
(inductively) to respond in nanoseconds.**
- **100 nF ceramic per power pin, as close as physically possible** —
  ⚠️ **the loop area from cap to pin to ground is what matters, not the schematic.**
- **Bulk capacitance** (10–100 µF) per board region.
- **⚠️ Via inductance dominates** — use short traces and multiple vias to the plane.
- ⚠️ **The old advice to parallel many different values is now considered dubious**: it
  can create anti-resonances between the caps. **Modern practice favours several
  same-value caps with low ESL, plus bulk.**

### 9.4 Grounding
**⚠️ "Ground" is not an equipotential — it's a conductor with impedance**, and current
flowing through it creates voltage differences. **This is ground bounce, and it is a real
signal.**
- **Single-point (star) ground** for low-frequency and analogue.
- **⚠️ Solid ground plane for anything fast** — it is the lowest-inductance return path
  available and it is worth a board layer.
- **⚠️ Analogue/digital ground splits are more often harmful than helpful** at this point.
  **A single solid plane with careful *placement* and partitioning usually beats a split**
  — because a split forces the §9.1 detour. **If you split, join at exactly one point and
  never route across the gap.**
- **Kelvin (4-wire) sensing** for current shunts and precision — ⚠️ **measure at the
  element, not through the current-carrying path.**

---

## §10. EMC and EMI

**⚠️ Emissions are set by rise time, loop area, and common-mode current — not by clock
frequency.** `f_knee ≈ 0.35/t_rise` (§4 → `ee-fundamentals-components-and-circuit-analysis`).

**Reduce emissions by**: **minimizing loop area** (§9.1 — ⚠️ **the highest-leverage
change**), **slowing edges where you can afford to** (many MCUs have configurable slew
rate — use it), **series termination**, **shielding**, **common-mode chokes on cables**,
and **filtering at the connector, not somewhere in the middle.**

**⚠️ Cables are the antennas.** A board that passes on its own will fail with cables
attached, because **common-mode current on a cable radiates efficiently.** **Filter and
ground at the point of entry.**

**Immunity and ESD**: ⚠️ **a human-body ESD event is kilovolts with nanosecond rise times**
and will find any unprotected exposed pin. **TVS diodes at connectors**, ground the
chassis properly, and **keep the ESD current path away from sensitive circuitry** — a TVS
that dumps into a trace running past your ADC has just moved the problem.

**⚠️ Practical advice**: pre-compliance testing with a cheap near-field probe and a
spectrum analyzer catches most problems before a formal test costs you a redesign cycle.
**Design for EMC from the start; it cannot be retrofitted cheaply.**

---

## §11. PCB Design

**Stackup**: ⚠️ **2-layer is fine for slow, low-power designs and inadequate for anything
fast.** **4-layer (signal / ground / power / signal) is the practical default** — the
ground plane pays for itself. **Keep signal layers adjacent to a reference plane.**

**Layout order that works**: connectors and mechanical constraints → power entry and
regulation → high-speed and sensitive analogue → everything else.
**⚠️ Place before you route, and place by signal flow.** Most routing pain is a placement
problem.

**Rules worth internalizing**:
- ⚠️ **Decoupling caps as close as physically possible to the pin** (§9.3).
- ⚠️ **Never cross a plane split with a fast signal** (§9.1).
- **Keep the switching regulator's high-`di/dt` loop tiny** (§8.2 → `ee-semiconductors-op-amps-logic-and-power`).
- **Match lengths for parallel buses and differential pairs; route pairs together.**
- **Thermal relief on pads connected to planes** — ⚠️ **or you cannot hand-solder them.**
- **Copper pour and thermal vias for heat.**
- ⚠️ **Test points on every rail, key signals, and ground — cheap now, priceless at
  debug time** (§15 → `ee-test-selection-safety-and-debugging`).
- **Silkscreen: polarity marks, pin 1, connector labels, and a version string.**

**⚠️ DFM realities**: respect the fab's minimum trace/space and drill sizes, check
annular ring, avoid acid traps, and **run DRC and actually read the output.**
**Always order a bare-board and check fit before populating a batch.**

**Tools**: **KiCad** (⚠️ **free, and now genuinely professional-grade — the right default
for most people**), Altium, Eagle/Fusion, OrCAD. **Simulation**: LTspice/ngspice
(⚠️ **free, and worth learning for power and analogue**), QUCS, and the vendor design
tools for switching regulators (⚠️ **TI WEBENCH and similar produce a working design and
a bill of materials in minutes — use them**).
