---
name: em-current-energy-flow-circuits-and-ac
description: "Use when the lumped-circuit picture is failing or a claim about electricity sounds wrong: what current actually is including drift velocity, resistance and how far Ohm's law really extends, where energy actually flows via the Poynting vector rather than through the wire, circuit theory and the conditions under which it stops being valid, AC and impedance with phasors and reactance, and power, RMS and power factor."
---

# Electromagnetism: What Current Actually Is, Resistance and Ohm's Law, Where the Energy Actually Flows, Circuit Theory and Its Validity, AC and Impedance, and Power Factor

> **Part 2 of 6** of the *Electromagnetism and the Physics of Electricity* reference (plugin `electromagnetism-and-electricity`), covering §6–§11. Sibling skills: `em-electrostatics-fields-potential-and-dielectrics` (§0–§5), `em-magnetism-induction-and-transformers` (§12–§15), `em-maxwell-waves-transmission-lines-and-relativity` (§16–§19), `em-conduction-semiconductors-grounding-and-electrical-safety` (§20–§25), `em-reference` (§26–§31). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The theory has been settled since 1865. Two areas are live. See §26 → `em-reference` for superconductivity claims, and wide-bandgap power semiconductors.

> **⚠️ The most complete classical theory in physics, and the one whose everyday
> descriptions are most wrong.** ⚠️ **Almost every intuition taught in school — electrons
> flowing fast through wires, energy travelling inside the conductor, current choosing the
> path of least resistance — is false, and the corrections are not pedantry: they change
> what you predict** (§6, §8, §9).
>
> **Complements a fundamental-physics reference (quantum foundations), a radio-technology
> reference (RF practice), and a thermodynamics reference (energy accounting).**
>
> **⚠️ GOTCHA** boxes mark the misconceptions and the places where a valid model is being
> used outside its domain.
>
> **⚠️ Safety, stated once**: ⚠️ **mains and higher voltages kill, capacitors hold charge
> after power is removed, and it is CURRENT THROUGH THE BODY that harms** (§25 → `em-conduction-semiconductors-grounding-and-electrical-safety`). **Nothing
> here is a substitute for qualified electrical work.**
>
> **The three ideas that organize this document:**
> 1. **⚠️ FIELDS are the physical objects; charges and currents are sources** (§3 → `em-electrostatics-fields-potential-and-dielectrics`, §16 → `em-maxwell-waves-transmission-lines-and-relativity`).
>    **The field carries the energy and the momentum, and it is local — action at a
>    distance is not what happens.**
> 2. **⚠️ ENERGY FLOWS IN THE FIELD AROUND THE WIRE, NOT THROUGH IT** (§8). **The Poynting
>    vector is the correction that reorganizes everything downstream, including why
>    transmission lines, EMC and antennas behave as they do.**
> 3. **⚠️ Circuit theory is an APPROXIMATION with a stated validity condition** (§9).
>    **It holds when the circuit is small compared to the wavelength. Above that, you need
>    fields — and most confusing high-speed behaviour is this boundary being crossed.**

---

## §6. ⚠️ What Current Actually Is

```
⚠️ I = dQ/dt. Current density J = nqv_d
⚠️ DRIFT VELOCITY in a copper wire at typical currents is on the order
   of MILLIMETRES PER SECOND — ⚠️ slower than walking pace
⚠️ RANDOM THERMAL VELOCITY of the same electrons is ~10⁶ m/s.
   ⚠️ Drift is a tiny bias on enormous random motion
⚠️ THE SIGNAL propagates at a substantial fraction of c, because it is
   the FIELD that propagates, not the electrons (§8)
```
> **⚠️ GOTCHA — three related corrections that matter.**
> ⚠️ **First, "electrons flow from the battery to the bulb" gets the timescale absurdly
> wrong — an electron would take HOURS to traverse a circuit that lights instantly.**
> ⚠️ **Second, CONVENTIONAL CURRENT flows opposite to electron motion, a historical
> convention from before the electron was known; it is arbitrary but universal, so use it.**
> ⚠️ **Third, in electrolytes and plasmas the charge carriers are IONS of both signs, and
> in semiconductors HOLES behave as genuine positive carriers** (§21 → `em-conduction-semiconductors-grounding-and-electrical-safety`).

**⚠️ Continuity**: ⚠️ **charge is conserved locally, so ∇·J = −∂ρ/∂t.** **This is what
Kirchhoff's current law is** (§9).

---

## §7. Resistance and Ohm's Law

**⚠️ V = IR is a MATERIAL BEHAVIOUR, not a law of nature.** ⚠️ **Many things are not ohmic:
diodes, transistors, filaments (resistance rises with temperature), thermistors, arcs
(negative resistance region), and most of the interesting components.**
**⚠️ Resistivity ρ and its temperature coefficient**: ⚠️ **metals increase resistance with
temperature (more phonon scattering); semiconductors DECREASE (more carriers) — an
inversion that follows directly from §20 → `em-conduction-semiconductors-grounding-and-electrical-safety`'s band picture.**
**⚠️ R = ρL/A**, **and ⚠️ the SKIN EFFECT confines high-frequency current to a thin surface
layer, making effective A much smaller and AC resistance much higher than DC.**
> **⚠️ GOTCHA — "current takes the path of least resistance" is FALSE.** ⚠️ **Current takes
> ALL available paths, dividing in inverse proportion to resistance.** **⚠️ The correct
> version matters in practice: a fault current does not politely go down the earth
> conductor and ignore the person in parallel with it.**
> **⚠️ The higher-frequency version is even less intuitive: return current follows the
> path of least IMPEDANCE, which above a few hundred kHz means it flows directly beneath
> the signal trace to minimize loop inductance — not by the shortest route** (§24 → `em-conduction-semiconductors-grounding-and-electrical-safety`).

---

## §8. ⚠️ Where the Energy Actually Flows

> **⚠️ The single most clarifying correction in this document.**
> ⚠️ **Electrical energy does NOT travel through the inside of the wire. It travels through
> the ELECTROMAGNETIC FIELD in the space AROUND the conductors.**
```
⚠️ POYNTING VECTOR  S = E × H  (W/m²) — energy flux density
⚠️ The wire's role is to GUIDE the field and to establish the surface
   charges that shape it. ⚠️ The wire is a waveguide, not a pipe
⚠️ At a resistor, S points INTO the resistor from the surrounding
   field — ⚠️ the dissipated energy arrives through the surface,
   not along the conductor
```
**⚠️ Why this reorganizes everything downstream:**
- ⚠️ **It explains why LOOP AREA governs inductance and radiation** — **the field volume is
  the physical thing** (§14 → `em-magnetism-induction-and-transformers`, §24 → `em-conduction-semiconductors-grounding-and-electrical-safety`).
- ⚠️ **It explains transmission lines**: **the signal is a field structure propagating in
  the dielectric BETWEEN the conductors** (§18 → `em-maxwell-waves-transmission-lines-and-relativity`).
- ⚠️ **It explains why a coaxial cable works and why the shield matters.**
- ⚠️ **It explains transformer action across an air gap with no conduction path** (§14 → `em-magnetism-induction-and-transformers`).
- ⚠️ **It explains why "ground" is a return CURRENT PATH and a field boundary, not a
  magic sink** (§24 → `em-conduction-semiconductors-grounding-and-electrical-safety`).
**⚠️ The famous thought experiment**: ⚠️ **a very long circuit with a battery, a switch and
a lamp, where the lamp is one metre from the battery but the wires run a light-second in
each direction.** **⚠️ A small current begins in the lamp almost immediately — because the
field couples across the metre gap — while full steady current takes the round-trip time.**
**⚠️ The dispute over how to describe this is largely semantic; the field picture predicts
it and the "electrons in wires" picture does not.**

---

## §9. ⚠️ Circuit Theory and Its Validity

```
⚠️ KIRCHHOFF'S CURRENT LAW = charge conservation (§6)
⚠️ KIRCHHOFF'S VOLTAGE LAW = ⚠️ conservative field — and it FAILS
   when there is a changing magnetic flux through the loop (§13),
   which is exactly why a probe loop in a switching supply reads
   voltages that "shouldn't be there"
⚠️ THE VALIDITY CONDITION  circuit dimensions ≪ wavelength.
   ⚠️ Rule of thumb: if the physical size exceeds roughly a tenth of
   a wavelength, use transmission line theory (§18)
```
**⚠️ Analysis tools**: **nodal and mesh analysis, Thévenin and Norton equivalents,
superposition (⚠️ linear circuits only), and the maximum power transfer theorem
(⚠️ which maximizes POWER, not efficiency — at matched impedance you dissipate half the
power in the source, which is why power distribution deliberately does NOT match).**
**⚠️ Time domain**: **RC and RL time constants (τ = RC, L/R), and ⚠️ RLC damping regimes.**
**⚠️ The parasitics are the real circuit at high frequency**: ⚠️ **every capacitor has
series inductance (ESL) and resistance (ESR) and therefore SELF-RESONATES, above which it
behaves as an inductor; every inductor has parallel capacitance; every wire has
inductance.** ⚠️ **A "100 nF decoupling capacitor" stops decoupling above its self-resonant
frequency, which is why multiple values in parallel are used.**

---

## §10. AC and Impedance

**⚠️ Sinusoids are special because they are the EIGENFUNCTIONS of linear time-invariant
systems** — ⚠️ **a sinusoid in gives a sinusoid out at the same frequency, changed only in
amplitude and phase.** **That's why phasors work and why Fourier analysis is the right
tool.**
```
⚠️ IMPEDANCE Z = R + jX
   ⚠️ RESISTOR  Z = R          (in phase)
   ⚠️ INDUCTOR  Z = jωL        (⚠️ voltage LEADS current by 90°)
   ⚠️ CAPACITOR Z = 1/(jωC)    (⚠️ current LEADS voltage by 90°)
   ⚠️ REACTANCE stores and returns energy; it does NOT dissipate
⚠️ RESONANCE at ω₀ = 1/√(LC); ⚠️ Q sets bandwidth and selectivity
```
**⚠️ Filters** (**low/high/band-pass, and ⚠️ the −3 dB point as the conventional corner**),
**and ⚠️ Bode plots as the standard way to see it.**
**⚠️ The mnemonic "ELI the ICE man"** — ⚠️ **in an inductor (L), E leads I; in a capacitor
(C), I leads E.**

---

## §11. Power, RMS and Power Factor

**⚠️ RMS is defined so that an AC quantity delivers the same average power into a resistor
as a DC quantity of the same value** — ⚠️ **for a sine, V_rms = V_peak/√2, which is where
the ~0.707 factor comes from.** **⚠️ It is NOT the average of the waveform, and it differs
for non-sinusoidal waveforms.**
```
⚠️ REAL power P (W) — actually dissipated
⚠️ REACTIVE power Q (VAR) — ⚠️ sloshes back and forth, dissipates nothing,
   ⚠️ AND STILL CAUSES I²R LOSSES IN THE WIRES. That's why it matters
⚠️ APPARENT power S (VA) = VI ;  ⚠️ POWER FACTOR = P/S
```
**⚠️ Power factor correction** exists because ⚠️ **the distribution system must be sized for
APPARENT power while only real power is billed to many customers** — **hence industrial PF
penalties.**
**⚠️ Harmonics and non-linear loads**: ⚠️ **switch-mode supplies draw current in pulses, so
PF can be poor even with voltage and current "in phase," and ⚠️ triplen harmonics ADD in
the neutral of a three-phase system rather than cancelling — which is why neutrals in
harmonic-rich installations can carry more current than the phases.**

---

# PART III — MAGNETISM
