---
name: ee-reference
description: "Use when checking an electronics anti-pattern, looking up a voltage, current, tolerance or magnitude, finding the textbook canon, or needing the core equations, a part picker, and the first-power-up checklist to run before applying power to a new board. Companion to the other electrical-engineering skills."
---

# Electrical Engineering: Anti-Patterns, Numbers, and Canon

> **Part 5 of 5** of the *Electrical Engineering* reference (plugin `electrical-engineering`), covering §16–§20. Sibling skills: `ee-fundamentals-components-and-circuit-analysis` (§0–§4), `ee-semiconductors-op-amps-logic-and-power` (§5–§8), `ee-signal-integrity-emc-and-pcb-design` (§9–§11), `ee-test-selection-safety-and-debugging` (§12–§15). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §16. Anti-Patterns

| Anti-pattern | Why |
|---|---|
| Voltage divider as a power supply | ⚠️ **Sags under load. Use a regulator or buffer** (§1 → `ee-fundamentals-components-and-circuit-analysis`) |
| Inductive load with no flyback diode | ⚠️ **Destroys the switch, sometimes slowly** (§1 → `ee-fundamentals-components-and-circuit-analysis`) |
| Ignoring ceramic DC bias derating | ⚠️ **10 µF can be 2 µF in circuit** (§2.2 → `ee-fundamentals-components-and-circuit-analysis`) |
| Standard MOSFET driven from a 3.3 V GPIO | ⚠️ **Barely on, dissipates heat, fails** (§5.3 → `ee-semiconductors-op-amps-logic-and-power`) |
| No gate pull-down on a load switch | Load turns on during MCU reset (§5.3 → `ee-semiconductors-op-amps-logic-and-power`) |
| GPIO driving a big power FET directly | Slow edges, linear-region heat (§5.3 → `ee-semiconductors-op-amps-logic-and-power`) |
| Trusting "3.3 V and 5 V are compatible" | ⚠️ **Compare V_OH against V_IH from both datasheets** (§7.1 → `ee-semiconductors-op-amps-logic-and-power`) |
| 5 V into a non-5V-tolerant pin | ⚠️ **ESD diode conducts; slow mysterious death** (§7.2 → `ee-semiconductors-op-amps-logic-and-power`) |
| Floating CMOS input | Oscillation and heating (§7.4 → `ee-semiconductors-op-amps-logic-and-power`) |
| LDO for a large voltage drop | ⚠️ **12→3.3 V at 500 mA is 4.35 W and 27% efficient** (§8.1 → `ee-semiconductors-op-amps-logic-and-power`) |
| Ignoring LDO dropout as a battery sags | Regulation stops (§8.1 → `ee-semiconductors-op-amps-logic-and-power`) |
| Creative switching-regulator layout | ⚠️ **Follow the reference layout** (§8.2 → `ee-semiconductors-op-amps-logic-and-power`) |
| Routing a fast signal across a plane split | ⚠️ **The return current detours; that loop is an antenna** (§9.1 → `ee-signal-integrity-emc-and-pcb-design`) |
| Decoupling cap "somewhere near" the chip | Loop area is what matters (§9.3 → `ee-signal-integrity-emc-and-pcb-design`) |
| Analogue/digital ground split, routed across | Usually worse than a solid plane (§9.4 → `ee-signal-integrity-emc-and-pcb-design`) |
| Ferrite bead + bulk cap without damping | ⚠️ **LC tank that amplifies at resonance** (§2.3 → `ee-fundamentals-components-and-circuit-analysis`) |
| Uncompensated scope probe | ⚠️ **Distorted edges you'll chase for an hour** (§12.2 → `ee-test-selection-safety-and-debugging`) |
| Long crocodile ground lead on fast edges | ⚠️ **Ringing that isn't in your circuit** (§12.2 → `ee-test-selection-safety-and-debugging`) |
| Scope ground clipped to a live mains node | ⚠️ **Short through earth. Use a differential probe** (§12.2 → `ee-test-selection-safety-and-debugging`, §14 → `ee-test-selection-safety-and-debugging`) |
| Ammeter across a voltage source | Short circuit; blown fuse (§12.1 → `ee-test-selection-safety-and-debugging`) |
| First power-up without current limiting | Turns a short into scrap (§12.3 → `ee-test-selection-safety-and-debugging`, §15 → `ee-test-selection-safety-and-debugging`) |
| Designing to "typical" datasheet values | ⚠️ **Design to min/max** (§13 → `ee-test-selection-safety-and-debugging`) |
| Treating absolute maximum as an operating point | ⚠️ **Those are destruction limits** (§13 → `ee-test-selection-safety-and-debugging`) |
| Ignoring part lifecycle and stock | A design you can't build (§13 → `ee-test-selection-safety-and-debugging`) |
| Assuming low voltage means safe | ⚠️ **~100 mA is the lethal mechanism** (§14 → `ee-test-selection-safety-and-debugging`) |
| Probing a board with no test points | You'll wish you'd spent the 20 minutes (§11 → `ee-signal-integrity-emc-and-pcb-design`) |
| Changing three things then retesting | You've learned nothing (§15 → `ee-test-selection-safety-and-debugging`) |

---

## §17. Numbers

```
FUNDAMENTALS
Si diode V_f 0.6–0.7 V · Schottky 0.2–0.4 V · LED 1.8 V (red) to 3.4 V (blue/white)
BJT V_BE 0.7 V · V_CE(sat) ~0.2 V · drive I_B ≈ I_C/10
⚠️ Logic-level MOSFET: check R_DS(on) at YOUR V_GS

LOGIC LEVELS
3.3 V CMOS: V_OH ≥2.4 · V_OL ≤0.4 · V_IH ≥2.0 · V_IL ≤0.8
5 V TTL:    V_IH ≥2.0  ⚠️ (3.3 V drives this)
5 V CMOS:   V_IH ≥3.5  ⚠️ (3.3 V does NOT reliably drive this)

TIME AND FREQUENCY
τ = RC · 63% in 1τ · ~99% in 5τ · f_c = 1/(2πRC)
⚠️ f_knee ≈ 0.35/t_rise  · −3 dB = half POWER (half voltage = −6 dB)
FR4 propagation ~6 in/ns (~150 ps/inch)
⚠️ Transmission-line territory above ~1–2 inches for ns edges

PHYSICAL
Trace/wire inductance ~1 nH/mm · Via ~1 nH
1 oz copper 10 mil trace ≈ 0.05 Ω/inch
Z₀ typical: 50 Ω single-ended, 90–100 Ω differential
Decoupling: 100 nF per power pin + bulk 10–100 µF per region

POWER
Li-ion 4.2 V full / 3.7 nominal / 3.0 empty ⚠️ (40% swing)
LiFePO₄ 3.2 V · Alkaline 1.5 V · NiMH 1.2 V
LDO efficiency = V_out/V_in · Switching 85–95%
⚠️ Derate: power 50%, tantalum voltage 50%+, silicon life halves per +10 °C

SAFETY ⚠️
1 mA perception · 10 mA let-go · 30 mA respiratory · 100 mA fibrillation
Dry skin ~100 kΩ · wet ~1 kΩ  ⚠️ 120 V across 1 kΩ = 120 mA

MEASUREMENT
Scope bandwidth ≥3–5× signal knee frequency · sample rate ≥5× bandwidth
10× probe: 10 MΩ, ~10 pF · 1× probe: 1 MΩ, ~100 pF ⚠️
DMM input ~10 MΩ
I²C pull-ups: 10 kΩ lazy default; 2.2–4.7 kΩ at 400 kHz
Switch bounce 1–50 ms
```

---

## §18. Books

| Author | Work | Why |
|---|---|---|
| **Horowitz & Hill** | ***The Art of Electronics*** (3rd ed.) | ⚠️ **The book. Practical, opinionated, and written by people who build things** |
| **Horowitz & Hill** | *The Art of Electronics: The X-Chapters* | Deeper dives on the hard parts |
| **Scherz & Monk** | *Practical Electronics for Inventors* | ⚠️ **The friendlier entry point** |
| **Johnson & Graham** | ***High-Speed Digital Design: A Handbook of Black Magic*** | ⚠️ **§9 → `ee-signal-integrity-emc-and-pcb-design` and §10 → `ee-signal-integrity-emc-and-pcb-design`, definitively. Read it before your first fast board** |
| **Ott** | *Electromagnetic Compatibility Engineering* | The EMC reference |
| **Ritchie** | *Grounding and Shielding* (Morrison) | §9.4 → `ee-signal-integrity-emc-and-pcb-design` done properly |
| **Williams** | *Analog Circuit Design* (and the Jim Williams app notes) | ⚠️ **Linear Technology app notes are among the best engineering writing anywhere** |
| **Maxfield** | *Bebop to the Boolean Boogie* | Digital, enjoyable |
| **Pease** | *Troubleshooting Analog Circuits* | ⚠️ **§15 → `ee-test-selection-safety-and-debugging`'s philosophy, from a legend** |
| **Sedra & Smith** | *Microelectronic Circuits* | The academic reference |

**Practical resources**: **vendor application notes** (⚠️ **TI, Analog Devices, Linear —
frequently better than textbooks and free**), **datasheets** (§13 → `ee-test-selection-safety-and-debugging`), **KiCad
documentation**, **LTspice** (free), **EEVblog** (⚠️ **Dave Jones's teardowns and
fundamentals videos**), **/r/AskElectronics**, **the IPC standards** (IPC-2221 for design,
IPC-A-610 for acceptability) for anything going to manufacture.

---

## §19. Quick Reference

### 19.1 Equations
```
V = IR · P = VI = I²R = V²/R
I = C·dV/dt · V = L·di/dt          ⚠️ the two that explain most surprises
V_out = V_in · R₂/(R₁+R₂)          ⚠️ unloaded only
Z_L = jωL · Z_C = 1/(jωC) · ω = 2πf
f_c = 1/(2πRC) · τ = RC · f₀ = 1/(2π√(LC))
f_knee ≈ 0.35/t_rise               ⚠️ the spectrum of a digital edge
Γ = (Z_L − Z₀)/(Z_L + Z₀)          reflection
T_j = T_a + P·θ_JA                 ⚠️ θ_JA is optimistic
R_LED = (V_supply − V_f)/I_f
dB = 20log₁₀(V₁/V₂) = 10log₁₀(P₁/P₂)
t_rise(I²C) ≈ 0.85·R·C_bus
```

### 19.2 Picker
| Need | Use |
|---|---|
| Step down, efficiency matters | **Buck** (§8.1 → `ee-semiconductors-op-amps-logic-and-power`) |
| Step down, small drop, quiet rail | **LDO** (§8.1 → `ee-semiconductors-op-amps-logic-and-power`) |
| Switch a load from a 3.3 V GPIO | ⚠️ **Logic-level MOSFET + gate pull-down** (§5.3 → `ee-semiconductors-op-amps-logic-and-power`) |
| Switch a high-side load | P-channel, or N-channel + gate driver (§5.3 → `ee-semiconductors-op-amps-logic-and-power`) |
| Drive an inductive load | ⚠️ **Add the flyback diode** (§1 → `ee-fundamentals-components-and-circuit-analysis`) |
| Buffer a high-impedance node | **Op-amp follower** (§6 → `ee-semiconductors-op-amps-logic-and-power`) |
| Compare two voltages | ⚠️ **Comparator with hysteresis** (§6 → `ee-semiconductors-op-amps-logic-and-power`) |
| Amplify a sensor bridge | **Instrumentation amp** (§6 → `ee-semiconductors-op-amps-logic-and-power`) |
| Convert 5 V logic to 3.3 V | ⚠️ **Translator IC, or divider if slow** (§7.2 → `ee-semiconductors-op-amps-logic-and-power`) |
| Bidirectional level shift (I²C) | **N-FET shifter + pull-ups** (§7.2 → `ee-semiconductors-op-amps-logic-and-power`) |
| Clean up a noisy digital input | **RC + Schmitt**, or debounce in firmware (§7.4 → `ee-semiconductors-op-amps-logic-and-power`) |
| Protect a connector from ESD | **TVS at the connector** (§10 → `ee-signal-integrity-emc-and-pcb-design`) |
| Local transient current for an IC | **100 nF at the pin, minimal loop** (§9.3 → `ee-signal-integrity-emc-and-pcb-design`) |
| Stop ringing on a fast point-to-point trace | **Series termination at the source** (§9.2 → `ee-signal-integrity-emc-and-pcb-design`) |
| Find a short | ⚠️ **Current-limited supply + thermal camera** (§12.3 → `ee-test-selection-safety-and-debugging`, §15 → `ee-test-selection-safety-and-debugging`) |
| Debug a protocol | **Logic analyzer, not a scope** (§12.3 → `ee-test-selection-safety-and-debugging`) |
| Measure a fast edge honestly | ⚠️ **10× probe, compensated, spring ground** (§12.2 → `ee-test-selection-safety-and-debugging`) |

### 19.3 First-power-up checklist
- [ ] Visual inspection under magnification — polarity, bridges, wrong values? (§15 → `ee-test-selection-safety-and-debugging`)
- [ ] Bench supply **current limit set** before connecting? (§12.3 → `ee-test-selection-safety-and-debugging`)
- [ ] Rails checked for shorts to ground with a meter, power off?
- [ ] Power up slowly; watch current draw against expectation (§15 → `ee-test-selection-safety-and-debugging`)
- [ ] Every rail at the correct voltage, **at the load, under load, on a scope**? (§15 → `ee-test-selection-safety-and-debugging`)
- [ ] Thermal check — anything hot? (§15 → `ee-test-selection-safety-and-debugging`)
- [ ] Clocks and resets present? (§15 → `ee-test-selection-safety-and-debugging`)
- [ ] Only then: does the firmware run?

---

## §20. Method

**No searches were run, and none were warranted.** ⚠️ **This is settled physics and mature
practice**: Ohm 1827, Kirchhoff 1845, Heaviside's transmission-line work in the 1880s,
and the CMOS/TTL threshold conventions have been fixed for decades. **Component part
numbers and prices move constantly; none of the content here depends on them.**

**Sources** are the standard references in §18 — chiefly **Horowitz & Hill** for practical
circuit design, **Johnson & Graham** for §9 → `ee-signal-integrity-emc-and-pcb-design` and §10 → `ee-signal-integrity-emc-and-pcb-design` (⚠️ **the high-speed material is
substantially their framing, including the `0.35/t_rise` knee rule and the
return-current-under-the-trace principle**), **Ott** for EMC, and vendor application notes,
which in this field are frequently better than textbooks.

**Scoped to complement**: MCU selection, buses, and firmware architecture sit in an
embedded-IoT reference; DSP in a signal-processing reference; the semiconductor
*fabrication* process in a nanotechnology reference. **This is the circuit layer they all
assume.**

**Confidence: high throughout.** The equations are standard and stated with their validity
conditions — ⚠️ **the conditions are the valuable part, since most errors here come from
applying a correct formula outside its assumptions** (an unloaded divider, a `R_DS(on)`
at the wrong `V_GS`, a `θ_JA` from a different board).

⚠️ **Three deliberate hedges.** **Numerical values in §17 are representative** — logic
thresholds vary by family and vendor, `V_f` varies with current and temperature, and
propagation delay depends on the dielectric. **Always check the specific datasheet.**
**The §9.3 → `ee-signal-integrity-emc-and-pcb-design` note that paralleling many different capacitor values is now considered dubious
reflects a genuine shift in practice** away from older advice, and ⚠️ **you will still find
the old guidance widely repeated** — the anti-resonance argument is the reason for the
change. And **§14 → `ee-test-selection-safety-and-debugging` is orientation, not a safety qualification**: ⚠️ **the current thresholds
are widely-cited approximations that vary with path, duration, frequency and individual.
If you are working on mains and unsure, get someone qualified.**
