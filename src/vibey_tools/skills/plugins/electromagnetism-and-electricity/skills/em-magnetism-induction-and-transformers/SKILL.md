---
name: em-magnetism-induction-and-transformers
description: "Use for magnetics: magnetic fields and the Biot-Savart and Ampère laws, electromagnetic induction and Faraday's and Lenz's laws, inductance, mutual inductance and transformer behaviour including leakage and saturation, and magnetic materials with permeability, hysteresis, core losses and saturation."
---

# Electromagnetism: Magnetic Fields, Induction, Inductance and Transformers, and Magnetic Materials

> **Part 3 of 6** of the *Electromagnetism and the Physics of Electricity* reference (plugin `electromagnetism-and-electricity`), covering §12–§15. Sibling skills: `em-electrostatics-fields-potential-and-dielectrics` (§0–§5), `em-current-energy-flow-circuits-and-ac` (§6–§11), `em-maxwell-waves-transmission-lines-and-relativity` (§16–§19), `em-conduction-semiconductors-grounding-and-electrical-safety` (§20–§25), `em-reference` (§26–§31). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 1. **⚠️ FIELDS are the physical objects; charges and currents are sources** (§3 → `em-electrostatics-fields-potential-and-dielectrics`, §16 → `em-maxwell-waves-transmission-lines-and-relativity`).
>    **The field carries the energy and the momentum, and it is local — action at a
>    distance is not what happens.**
> 2. **⚠️ ENERGY FLOWS IN THE FIELD AROUND THE WIRE, NOT THROUGH IT** (§8 → `em-current-energy-flow-circuits-and-ac`). **The Poynting
>    vector is the correction that reorganizes everything downstream, including why
>    transmission lines, EMC and antennas behave as they do.**
> 3. **⚠️ Circuit theory is an APPROXIMATION with a stated validity condition** (§9 → `em-current-energy-flow-circuits-and-ac`).
>    **It holds when the circuit is small compared to the wavelength. Above that, you need
>    fields — and most confusing high-speed behaviour is this boundary being crossed.**

---

## §12. Magnetic Fields

**⚠️ Magnetism has NO MONOPOLES** — ⚠️ **∇·B = 0, field lines always close.** **This is one
of Maxwell's four equations and it's an experimental fact with no known exception.**
**⚠️ Sources**: **moving charge and current.** **Biot-Savart for the general case; ⚠️ Ampère's
law for symmetric cases; ⚠️ and the force law F = qv × B, which is a CROSS PRODUCT —
perpendicular to both velocity and field.**
> **⚠️ GOTCHA — the magnetic force does NO WORK on a charge.** ⚠️ **Because F ⊥ v always,
> it changes direction but never speed.** **⚠️ Motors therefore do not work by "magnetic
> force doing work" in the naive sense — the energy comes from the electrical source via
> the induced back-EMF** (§13), **and tracing that properly is a genuinely subtle piece of
> physics.**

**⚠️ Solenoids and toroids**: ⚠️ **B = μ₀nI inside a long solenoid, essentially uniform and
independent of radius — which is why solenoids are the standard field source.**

---

## §13. Induction

**⚠️ Faraday: EMF = −dΦ/dt.** ⚠️ **A CHANGING magnetic flux induces an electric field.**
**⚠️ Lenz's law is the minus sign, and it is conservation of energy in disguise**:
⚠️ **the induced current opposes the change producing it.** **⚠️ If it reinforced instead,
you'd have a runaway energy source.**
```
⚠️ FLUX CHANGES THREE WAYS  changing B · changing area · changing
   orientation. ⚠️ All three are used in real machines
⚠️ MOTIONAL EMF  a conductor moving through a field
⚠️ EDDY CURRENTS  induced loops in bulk conductors. ⚠️ Cause loss in
   transformer cores (hence LAMINATION) and are exploited in induction
   heating, magnetic braking and metal detection
```
**⚠️ Back-EMF is the key to understanding motors**: ⚠️ **a spinning motor generates an EMF
opposing the supply, so the current drawn is set by (V − back-EMF)/R.** **⚠️ At stall,
back-EMF is zero and the current is limited only by winding resistance — which is why
stalled motors burn out and why inrush current is large.**
**⚠️ The induction paradox in KVL** (§9 → `em-current-energy-flow-circuits-and-ac`): ⚠️ **around a loop enclosing changing flux, the
"voltage" you measure depends on where your probe leads run**, **because the field is not
conservative there.** **⚠️ This is a real measurement problem, not a curiosity.**

---

## §14. Inductance and Transformers

**⚠️ Self-inductance L = Φ/I; V = L(dI/dt)** — ⚠️ **inductance resists CHANGE in current,
and its energy U = ½LI² lives in the field.**
> **⚠️ GOTCHA — interrupting current in an inductor produces a large voltage spike, because
> dI/dt is huge.** ⚠️ **This destroys switches and semiconductors, and it's why flyback
> diodes exist across relay coils and motor windings.** **⚠️ It is also the operating
> principle of ignition coils and boost converters — the same physics, deliberately
> exploited.**

**⚠️ Mutual inductance and transformers**: **V₂/V₁ = N₂/N₁, I₂/I₁ = N₁/N₂**; ⚠️ **impedance
transforms as the SQUARE of the turns ratio, which is what makes matching networks work.**
**⚠️ Transformers require CHANGING flux, so they do not work on DC** — **and applying DC
to a transformer saturates the core and burns it.**
**⚠️ Real transformer losses**: ⚠️ **copper (I²R), core hysteresis, eddy currents (§13),
leakage inductance, and winding capacitance.** ⚠️ **The reason high-voltage transmission
exists is entirely §11 → `em-current-energy-flow-circuits-and-ac`: at fixed power, higher V means lower I means I²R losses fall as
the square.**

---

## §15. Magnetic Materials

```
DIAMAGNETIC   weakly repelled (⚠️ all matter is, weakly);
   ⚠️ superconductors are PERFECT diamagnets (§22)
PARAMAGNETIC  weakly attracted
⚠️ FERROMAGNETIC  strong, with DOMAINS, HYSTERESIS and REMANENCE.
   ⚠️ Above the CURIE TEMPERATURE, ferromagnetism disappears entirely
FERRIMAGNETIC  ⚠️ ferrites — magnetic AND insulating, so no eddy
   currents, which is why they're the standard HF core material
```
**⚠️ The B-H curve and hysteresis loop**: ⚠️ **loop AREA is the energy lost per cycle, which
is why soft magnetic materials (narrow loop) are used for transformers and hard ones (wide
loop) for permanent magnets.**
**⚠️ SATURATION is the practical limit that surprises designers**: ⚠️ **once the core
saturates, incremental permeability collapses toward that of air, inductance plummets and
current rises sharply.** **⚠️ Most inductor failures in switching supplies are saturation,
not overheating.**

---

# PART IV — MAXWELL AND WAVES
