---
name: em-maxwell-waves-transmission-lines-and-relativity
description: "Use when wavelength starts to matter: Maxwell's equations and what each one says, electromagnetic waves with propagation, polarization and the wave equation, transmission lines including characteristic impedance, reflection and matching, and the relativistic origin of magnetism — why magnetism is electrostatics seen from a moving frame."
---

# Electromagnetism: Maxwell's Equations, Electromagnetic Waves, Transmission Lines, and Magnetism as Relativistic Electrostatics

> **Part 4 of 6** of the *Electromagnetism and the Physics of Electricity* reference (plugin `electromagnetism-and-electricity`), covering §16–§19. Sibling skills: `em-electrostatics-fields-potential-and-dielectrics` (§0–§5), `em-current-energy-flow-circuits-and-ac` (§6–§11), `em-magnetism-induction-and-transformers` (§12–§15), `em-conduction-semiconductors-grounding-and-electrical-safety` (§20–§25), `em-reference` (§26–§31). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The theory has been settled since 1865. Two areas are live. See §26 → `em-reference` for superconductivity claims, and wide-bandgap power semiconductors.

> **⚠️ The most complete classical theory in physics, and the one whose everyday
> descriptions are most wrong.** ⚠️ **Almost every intuition taught in school — electrons
> flowing fast through wires, energy travelling inside the conductor, current choosing the
> path of least resistance — is false, and the corrections are not pedantry: they change
> what you predict** (§6 → `em-current-energy-flow-circuits-and-ac`, §8 → `em-current-energy-flow-circuits-and-ac`, §9 → `em-current-energy-flow-circuits-and-ac`).
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
> 1. **⚠️ FIELDS are the physical objects; charges and currents are sources** (§3 → `em-electrostatics-fields-potential-and-dielectrics`, §16).
>    **The field carries the energy and the momentum, and it is local — action at a
>    distance is not what happens.**
> 2. **⚠️ ENERGY FLOWS IN THE FIELD AROUND THE WIRE, NOT THROUGH IT** (§8 → `em-current-energy-flow-circuits-and-ac`). **The Poynting
>    vector is the correction that reorganizes everything downstream, including why
>    transmission lines, EMC and antennas behave as they do.**
> 3. **⚠️ Circuit theory is an APPROXIMATION with a stated validity condition** (§9 → `em-current-energy-flow-circuits-and-ac`).
>    **It holds when the circuit is small compared to the wavelength. Above that, you need
>    fields — and most confusing high-speed behaviour is this boundary being crossed.**

---

## §16. ⚠️ Maxwell's Equations

```
⚠️ ∇·E = ρ/ε₀            GAUSS — charges source the electric field
⚠️ ∇·B = 0               NO MAGNETIC MONOPOLES
⚠️ ∇×E = −∂B/∂t          FARADAY — changing B makes circulating E
⚠️ ∇×B = μ₀J + μ₀ε₀∂E/∂t AMPÈRE-MAXWELL — ⚠️ current AND changing E
                          make circulating B
```
**⚠️ Maxwell's addition — the DISPLACEMENT CURRENT term — is the piece that completes the
theory**, ⚠️ **and it was required for consistency with charge conservation (consider the
gap of a charging capacitor: conduction current stops, yet B continues around it).**
> **⚠️ GOTCHA — the payoff is that the equations predict WAVES, at a speed given by
> 1/√(μ₀ε₀), computed from purely electrical and magnetic measurements — and that number
> matched the measured speed of light.** ⚠️ **That is one of the great moments in physics:
> light was identified as an electromagnetic phenomenon by ARITHMETIC, before anyone
> looked for the waves.**

**⚠️ Note also**: ⚠️ **Maxwell's equations are already relativistically correct — they
predate special relativity and were part of the motivation for it** (§19).

---

## §17. Electromagnetic Waves

**⚠️ In vacuum: E and B are perpendicular to each other and to the direction of propagation,
in phase, with E = cB.** ⚠️ **The wave carries energy (Poynting, §8 → `em-current-energy-flow-circuits-and-ac`) and MOMENTUM — hence
radiation pressure and solar sails.**
**⚠️ In media**: **v = c/n, and ⚠️ DISPERSION (n varying with frequency) causes prism
separation, rainbow formation and pulse spreading in optical fibre.**
**⚠️ Polarization**: **linear, circular, elliptical; ⚠️ and Brewster's angle, at which
reflected light is completely polarized.**
**⚠️ The spectrum is one continuum** — ⚠️ **radio through gamma differ only in frequency,
and the boundaries are conventional.**
**⚠️ IONIZING vs NON-IONIZING is the physically meaningful boundary** (§25 → `em-conduction-semiconductors-grounding-and-electrical-safety`): ⚠️ **around the
UV range, photon energy becomes sufficient to break chemical bonds.** **⚠️ Below it,
photon energy is too low to ionize regardless of intensity — which is a quantum fact and
the basis of the mainstream position on radiofrequency exposure.**
**⚠️ Radiation requires ACCELERATING charge** — ⚠️ **steady current does not radiate; changing
current does.**

---

## §18. Transmission Lines

**⚠️ Once a circuit is comparable to a wavelength** (§9 → `em-current-energy-flow-circuits-and-ac`), ⚠️ **voltage and current vary
ALONG the line and you must treat it as distributed.**
```
⚠️ CHARACTERISTIC IMPEDANCE  Z₀ = √(L/C) per unit length —
   ⚠️ a GEOMETRIC property, not a resistance. A 50 Ω cable does not
   dissipate; it presents 50 Ω to a wave
⚠️ REFLECTION  Γ = (Z_L − Z₀)/(Z_L + Z₀)
   ⚠️ Open circuit → Γ = +1 · Short → Γ = −1 · Matched → Γ = 0
⚠️ VSWR · standing waves · ⚠️ the Smith chart as the classic tool
⚠️ VELOCITY FACTOR  signals travel slower than c in dielectric
```
**⚠️ Why 50 Ω and 75 Ω exist**: ⚠️ **in coax, minimum loss and maximum power handling occur
at different impedances (~77 Ω and ~30 Ω respectively), and 50 Ω is roughly the
compromise; 75 Ω is the low-loss choice used for video and broadcast.**
**⚠️ Digital designers meet this constantly**: ⚠️ **fast edges have high-frequency content
regardless of clock rate, so PCB traces become transmission lines, and ringing and
overshoot are reflections from impedance mismatch — fixed by termination, not by
"slowing things down."**

---

## §19. ⚠️ Magnetism as Relativistic Electrostatics

> **⚠️ One of the most satisfying results in physics, and it explains why E and B are one
> field rather than two.**
⚠️ **Consider a current-carrying wire, neutral in the lab frame, and a charge moving
parallel to it.** ⚠️ **In the charge's rest frame, LENGTH CONTRACTION applies differently
to the moving and stationary charge distributions in the wire, so the wire is no longer
neutral in that frame — and there is an ELECTROSTATIC force.**
**⚠️ What one observer calls a magnetic force, another calls electric.** ⚠️ **They are the
same field, decomposed differently by frame.**
**⚠️ The startling part**: ⚠️ **drift velocities are millimetres per second (§6 → `em-current-energy-flow-circuits-and-ac`), so the
relativistic correction is fantastically small — and it is only observable because §2 → `em-electrostatics-fields-potential-and-dielectrics`'s
charge cancellation is so nearly perfect that a tiny residual still produces a force you
can feel.** **⚠️ Magnetism is a relativistic effect you can observe with a compass.**
**⚠️ Formally: the electromagnetic field tensor F^μν unifies E and B, and Maxwell's four
equations collapse to two tensor equations.**

---

# PART V — ELECTROMAGNETISM IN MATTER
