---
name: ee-semiconductors-op-amps-logic-and-power
description: "Use when designing the active parts of a circuit: diodes, BJTs and MOSFETs including the ones you will actually use and their thermal behaviour, op-amp circuits and their real-world limits, digital logic levels and where the real bugs live, level shifting, open-drain and buses, input protection, and power — regulator types, switching supply practicalities, sequencing, protection and batteries."
---

# Electrical Engineering: Semiconductors, Op-Amps, Digital Interfacing, and Power

> **Part 2 of 5** of the *Electrical Engineering* reference (plugin `electrical-engineering`), covering §5–§8. Sibling skills: `ee-fundamentals-components-and-circuit-analysis` (§0–§4), `ee-signal-integrity-emc-and-pcb-design` (§9–§11), `ee-test-selection-safety-and-debugging` (§12–§15), `ee-reference` (§16–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §5. Semiconductors

### 5.1 Diodes
`V_f` ≈ 0.7 V silicon, **0.2–0.4 V Schottky** (⚠️ **lower drop and faster, but higher
reverse leakage**). **Zener** for voltage reference/clamping. **TVS** for transient
protection (§10 → `ee-signal-integrity-emc-and-pcb-design`). **LED** — ⚠️ **always needs a current limit**: `R = (V_supply − V_f)/I_f`.

**⚠️ The diode applications you must know:**
- **Flyback/freewheeling** across every inductive load (§1 → `ee-fundamentals-components-and-circuit-analysis`) — ⚠️ **omit it and you destroy
  the switch.**
- **Reverse polarity protection** — a series diode (costs `V_f`) or ⚠️ **a P-channel MOSFET
  (near-zero drop, and the better answer).**
- **Rectification** — half-wave, full-wave bridge.
- **Clamping** to rails on inputs.

### 5.2 BJTs
Current-controlled: `I_C = β·I_B`, `V_BE ≈ 0.7 V`.
**Saturation** (fully on, `V_CE(sat)` ≈ 0.2 V) is what you want for switching —
⚠️ **drive the base hard enough: `I_B ≈ I_C/10`, ignoring β, because β varies enormously
part to part and with temperature.**

### 5.3 MOSFETs — the ones you'll actually use
**Voltage-controlled** via `V_GS`. `R_DS(on)` when on.
**⚠️ N-channel switches the low side; P-channel switches the high side.** N-channel is
cheaper and better (lower `R_DS(on)` for the same die) — ⚠️ **which is why high-side
N-channel switching needs a gate driver with a charge pump or bootstrap, since the gate
must go above the rail.**

> **⚠️ GOTCHA — "logic level" is the specification that gets missed.** A standard MOSFET
> may specify `R_DS(on)` at **V_GS = 10 V**. Drive it from a 3.3 V GPIO and it is barely
> on, dissipating heat in the linear region, and it will get hot and fail.
> **⚠️ You need a *logic-level* MOSFET rated at V_GS = 2.5 V or 4.5 V — check the
> `R_DS(on)` at YOUR gate voltage, not the headline number.**

**⚠️ Gate charge matters at speed**: the gate is a capacitor (`Q_g`), so switching fast
needs real current. **A GPIO cannot drive a large power MOSFET quickly** — you get slow
edges, long time in the linear region, and heat. **Use a gate driver.**
**⚠️ Always fit a gate pull-down** (10–100 kΩ) so the FET is off while the MCU is in reset
or unprogrammed — otherwise the load turns on at power-up.

**Body diode** conducts from source to drain — ⚠️ **useful in synchronous rectification,
and a hazard if you didn't expect it (it defeats naive reverse-polarity schemes).**

**GaN and SiC** for high-frequency and high-voltage power — ⚠️ **much faster switching,
and correspondingly much more demanding layout and gate drive.**

### 5.4 Thermal
```
T_junction = T_ambient + P·(θ_JA)
```
**⚠️ `θ_JA` from a datasheet assumes a specific board and copper pour** — it is nearly
always optimistic for your layout. **Derate hard.** Heatsinks, thermal vias, and copper
area are the levers. ⚠️ **Silicon lifetime falls roughly by half for every 10 °C rise**;
running cool is a reliability decision, not an aesthetic one.

---

## §6. Op-Amps

**⚠️ The two golden rules (for an ideal op-amp with negative feedback):**
1. **No current flows into the inputs.**
2. **The output does whatever it takes to make `V+ = V−`.**

**⚠️ Rule 2 only holds with negative feedback and within the output's ability.** Remove the
feedback and it's a comparator; exceed the rails and it clips.

**The standard configurations:**
```
Buffer/follower     gain 1 ⚠️ — impedance conversion, and the fix for a loaded divider (§1)
Inverting           −R_f/R_in
Non-inverting       1 + R_f/R_in     ⚠️ minimum gain 1
Differential        amplifies (V₂−V₁), rejects common mode
Instrumentation     ⚠️ high input Z + high CMRR — the right choice for sensor bridges
Integrator / Differentiator
Comparator          ⚠️ use an actual comparator, not an op-amp
Sallen-Key          active filter (§4)
Transimpedance      current → voltage (photodiodes)
```

**⚠️ Real op-amp limits that break designs:**
- **Input offset voltage** — matters at high gain.
- **Bias current** — ⚠️ **flows through your source impedance and becomes an error
  voltage.**
- **Slew rate** (V/µs) — ⚠️ **large-signal bandwidth is limited by this, not by GBW.**
- **Gain-bandwidth product** — ⚠️ **available gain falls with frequency: GBW/gain = usable
  bandwidth.**
- **Rail-to-rail?** ⚠️ **Most op-amps cannot swing to their rails, and many cannot accept
  inputs at the rails.** Check both input and output specs separately.
- **⚠️ Capacitive loading causes oscillation.** Adding a cap on an op-amp output to "clean
  it up" is a classic way to make it ring.

**⚠️ Comparators need hysteresis.** Without it, a slowly-crossing noisy input produces
multiple transitions — **the analogue of switch bounce, and it produces the same class of
mysterious multiple-interrupt bugs.** Add positive feedback (Schmitt trigger).

---

## §7. Digital Logic and Interfacing

### 7.1 Logic levels — where the real bugs live
```
V_OH  minimum the driver guarantees as HIGH
V_OL  maximum the driver guarantees as LOW
V_IH  minimum the receiver accepts as HIGH
V_IL  maximum the receiver accepts as LOW
Noise margin = V_OH − V_IH  (high side)   ⚠️ this is what you're actually designing
```
**⚠️ The interoperability trap**: a 3.3 V CMOS output has `V_OH` ≈ 3.0 V, and 5 V TTL
needs `V_IH` = 2.0 V — **that works.** But **5 V CMOS needs `V_IH` = 3.5 V** —
⚠️ **and 3.3 V will not reliably drive it.** **Always compare the actual numbers from both
datasheets; "3.3 V and 5 V are compatible" is not a fact, it's a coincidence that
sometimes holds.**

### 7.2 Level shifting
```
3.3 V → 5 V input     often works directly ⚠️ IF the receiver is TTL-threshold. Verify.
5 V → 3.3 V input     ⚠️ NOT safe unless the pin is 5V-tolerant — check the datasheet
                      Options: resistor divider (slow), series R + clamp diode,
                      dedicated translator IC, or a MOSFET shifter for bidirectional
Bidirectional (I²C)   ⚠️ the classic single-N-FET shifter with pull-ups to each rail
```
**⚠️ Feeding 5 V into a non-tolerant 3.3 V pin doesn't always fail immediately.** The
internal ESD diode conducts into the 3.3 V rail — **it may work, may raise the 3.3 V rail,
and may kill the part slowly.** Intermittent, temperature-dependent, and awful to debug.

### 7.3 Open-drain and buses
**Open-drain/open-collector** can only pull low; a pull-up provides the high.
⚠️ **This enables wired-AND and multi-master buses (I²C), and level shifting for free by
pulling up to the lower rail.**
**⚠️ Pull-up sizing for I²C**: `t_rise ≈ 0.85 · R · C_bus`. The spec caps rise time
(1 µs standard, 300 ns fast mode), so **more bus capacitance demands a smaller resistor**,
which raises current. ⚠️ **The classic "I²C works on the bench and fails with the long
cable" is exactly this.**

### 7.4 Inputs
**⚠️ Never leave a CMOS input floating** — it drifts through the threshold region, both
output transistors conduct, and you get oscillation and heating. **Pull it somewhere.**
**Switch debouncing** — mechanical contacts bounce for **1–50 ms**. ⚠️ **Debounce in
firmware (simplest and most flexible) or with an RC + Schmitt trigger.**
**Protection**: series resistor limits fault current, clamp diodes to the rails,
TVS for ESD (§10 → `ee-signal-integrity-emc-and-pcb-design`).

---

## §8. Power

### 8.1 Regulator types
| Type | Efficiency | ⚠️ Notes |
|---|---|---|
| **Linear / LDO** | ⚠️ **V_out/V_in** | Simple, quiet, ⚠️ **burns the difference as heat** |
| **Buck (step-down)** | 85–95% | Switching noise; needs layout care |
| **Boost (step-up)** | 85–95% | ⚠️ **Cannot current-limit or disconnect a shorted output** |
| **Buck-boost / SEPIC** | 80–90% | In or out of range either way |
| **Charge pump** | moderate | Small currents, no inductor |
| **Isolated (flyback etc.)** | varies | Safety isolation (§14 → `ee-test-selection-safety-and-debugging`) |

**⚠️ The LDO heat calculation people skip**: dropping 12 V to 3.3 V at 500 mA dissipates
`(12−3.3)×0.5 = 4.35 W` **in a package that probably can't shed it.** ⚠️ **Efficiency is
27%.** **Use a buck.** **LDOs are for small drops, small currents, or clean analogue
rails downstream of a switcher.**

**⚠️ Dropout voltage** — an LDO needs `V_in > V_out + V_dropout`. **A "5 V to 3.3 V" LDO
with 1.2 V dropout stops regulating as the battery sags.**

### 8.2 Switching supply practicalities
**⚠️ The layout is the design.** The high-`di/dt` loop (input cap → switch → diode/synchronous
FET) must be **physically tiny**, or you radiate and get ringing. **Follow the datasheet's
reference layout — this is not the place for creativity.**
**Feedback divider** near the IC, sensed at the load if possible. **Output ripple** set by
inductor, output cap ESR, and frequency. **Inductor saturation** (§2.3 → `ee-fundamentals-components-and-circuit-analysis`) is the classic
failure.

### 8.3 Sequencing, protection, batteries
**⚠️ Power sequencing matters** — many parts require rails to come up in a specific order,
and violating it can latch up or damage them. Check the datasheet.
**Protection**: fuses (⚠️ **slow — they protect the wiring, not the semiconductors**),
PTC resettable fuses, TVS diodes, ideal-diode controllers, inrush limiting.

**Batteries**: Li-ion nominal 3.7 V (⚠️ **4.2 V full, ~3.0 V empty — a 40% swing your
design must tolerate**), LiFePO₄ 3.2 V (safer, flatter), alkaline 1.5 V (⚠️ **sloping
discharge**), NiMH 1.2 V. **⚠️ Li-ion demands protection circuitry — overcharge,
overdischarge, overcurrent, and temperature.** **Capacity in mAh is at a specified
discharge rate**; ⚠️ **actual capacity falls at high current (Peukert), and falls badly in
the cold.**

**Sleep-mode budgeting**: ⚠️ **quiescent current of the regulator often dominates a
battery device's average consumption** — an LDO drawing 50 µA quiescent defeats an MCU
sleeping at 2 µA.
