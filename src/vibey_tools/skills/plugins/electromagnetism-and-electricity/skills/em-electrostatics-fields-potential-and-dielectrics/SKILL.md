---
name: em-electrostatics-fields-potential-and-dielectrics
description: "Use when starting from the field picture: the abstraction ladder and which model is valid when, charge and Coulomb's law, electric fields and Gauss's law, potential, voltage and capacitance, and dielectrics including polarization and breakdown. Includes the router for the whole electromagnetism reference."
---

# Electromagnetism: The Abstraction Ladder, Charge and Coulomb's Law, Fields and Gauss's Law, Potential and Capacitance, and Dielectrics

> **Part 1 of 6** of the *Electromagnetism and the Physics of Electricity* reference (plugin `electromagnetism-and-electricity`), covering §0–§5. Sibling skills: `em-current-energy-flow-circuits-and-ac` (§6–§11), `em-magnetism-induction-and-transformers` (§12–§15), `em-maxwell-waves-transmission-lines-and-relativity` (§16–§19), `em-conduction-semiconductors-grounding-and-electrical-safety` (§20–§25), `em-reference` (§26–§31). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 1. **⚠️ FIELDS are the physical objects; charges and currents are sources** (§3, §16 → `em-maxwell-waves-transmission-lines-and-relativity`).
>    **The field carries the energy and the momentum, and it is local — action at a
>    distance is not what happens.**
> 2. **⚠️ ENERGY FLOWS IN THE FIELD AROUND THE WIRE, NOT THROUGH IT** (§8 → `em-current-energy-flow-circuits-and-ac`). **The Poynting
>    vector is the correction that reorganizes everything downstream, including why
>    transmission lines, EMC and antennas behave as they do.**
> 3. **⚠️ Circuit theory is an APPROXIMATION with a stated validity condition** (§9 → `em-current-energy-flow-circuits-and-ac`).
>    **It holds when the circuit is small compared to the wavelength. Above that, you need
>    fields — and most confusing high-speed behaviour is this boundary being crossed.**

---

## §0. Routing

| You want... | Go to |
|---|---|
| The abstraction ladder | §1 |
| Charge and Coulomb | §2 |
| **Fields and Gauss** | **§3** |
| Potential and capacitance | §4 |
| Dielectrics | §5 |
| **⚠️ What current actually is** | **§6 → `em-current-energy-flow-circuits-and-ac`** |
| Resistance and Ohm's law | §7 → `em-current-energy-flow-circuits-and-ac` |
| **⚠️ Where energy flows** | **§8 → `em-current-energy-flow-circuits-and-ac`** |
| **⚠️ Circuit theory and its limits** | **§9 → `em-current-energy-flow-circuits-and-ac`** |
| AC and impedance | §10 → `em-current-energy-flow-circuits-and-ac` |
| Power and RMS | §11 → `em-current-energy-flow-circuits-and-ac` |
| Magnetic fields | §12 → `em-magnetism-induction-and-transformers` |
| **Induction** | **§13 → `em-magnetism-induction-and-transformers`** |
| Inductance and transformers | §14 → `em-magnetism-induction-and-transformers` |
| Magnetic materials | §15 → `em-magnetism-induction-and-transformers` |
| **⚠️ Maxwell's equations** | **§16 → `em-maxwell-waves-transmission-lines-and-relativity`** |
| EM waves | §17 → `em-maxwell-waves-transmission-lines-and-relativity` |
| **Transmission lines** | **§18 → `em-maxwell-waves-transmission-lines-and-relativity`** |
| **⚠️ Magnetism as relativity** | **§19 → `em-maxwell-waves-transmission-lines-and-relativity`** |
| Conduction and bands | §20 → `em-conduction-semiconductors-grounding-and-electrical-safety` |
| Semiconductors | §21 → `em-conduction-semiconductors-grounding-and-electrical-safety` |
| **Superconductivity** | **§22 → `em-conduction-semiconductors-grounding-and-electrical-safety`** |
| Plasma | §23 → `em-conduction-semiconductors-grounding-and-electrical-safety` |
| Grounding and EMC | §24 → `em-conduction-semiconductors-grounding-and-electrical-safety` |
| **⚠️ Electrical safety** | **§25 → `em-conduction-semiconductors-grounding-and-electrical-safety`** |
| **What's live** | **§26 → `em-reference`** |
| Misconceptions, numbers | §27–§28 → `em-reference` |
| Books, quick ref, method | §29–§31 → `em-reference` |

---

## §1. The Abstraction Ladder

```
⚠️ QED                    the fundamental theory; photons mediate
⚠️ MAXWELL (classical)    fields, exact for everything non-quantum (§16)
⚠️ QUASI-STATIC           fields but ignoring propagation delay
⚠️ TRANSMISSION LINE      distributed L and C along a length (§18)
⚠️ LUMPED CIRCUIT         V, I, R, L, C — ⚠️ valid only when the circuit
                          is SMALL compared to the wavelength (§9)
⚠️ OHM'S LAW              a material property, not a law of nature (§7)
```
**⚠️ The engineering skill is knowing which rung you're on** — ⚠️ **and most bafflement
in electronics is a lumped-model intuition applied where the field model is required.**

---

# PART I — ELECTROSTATICS

## §2. Charge and Coulomb's Law

**⚠️ Charge is quantized (e ≈ 1.602×10⁻¹⁹ C), conserved exactly, and comes in two signs.**
**⚠️ Coulomb: F = kq₁q₂/r², inverse square, along the line joining them** — ⚠️ **structurally
identical to gravity except that it can attract OR repel and is ~10³⁶ times stronger
between two protons.**
> **⚠️ GOTCHA — the reason you don't notice this enormous force is CANCELLATION.**
> ⚠️ **Bulk matter is neutral to extraordinary precision, so the residual forces are tiny
> compared to what the constant implies.** **⚠️ And essentially every everyday force you
> experience that isn't gravity — friction, normal force, tension, chemistry, the solidity
> of objects — IS electromagnetic.**

**⚠️ Superposition holds exactly**, ⚠️ **which is why the whole theory is tractable: fields
from multiple sources simply add.**

---

## §3. Fields and Gauss's Law

**⚠️ The field E is defined as force per unit test charge, and the conceptual move is that
the FIELD is the real object** — ⚠️ **charges create fields locally, fields propagate, and
other charges respond to the local field.** **No action at a distance.**
**⚠️ Gauss's law**: **the flux of E through a closed surface equals enclosed charge over
ε₀.** ⚠️ **It is equivalent to the inverse square law and is enormously more useful for
symmetric problems.**
```
⚠️ CONSEQUENCES WORTH KNOWING
   ⚠️ Field inside a conductor in electrostatic equilibrium is ZERO
   ⚠️ Excess charge on a conductor resides on the SURFACE
   ⚠️ FARADAY CAGE — external fields excluded from an enclosed cavity.
      ⚠️ Note this is exact for electrostatics and APPROXIMATE for
      time-varying fields, where aperture size versus wavelength
      governs (§24)
   ⚠️ Field lines meet a conductor surface PERPENDICULARLY
   ⚠️ Charge concentrates at high curvature — hence lightning rods
      and corona discharge at sharp points
```

---

## §4. Potential and Capacitance

**⚠️ Because the electrostatic field is conservative, a scalar potential exists — and this
is why voltage is such a useful concept.** ⚠️ **V is potential ENERGY per unit charge, and
only DIFFERENCES are physical.**
**⚠️ E = −∇V** — ⚠️ **the field points down the steepest potential gradient, which is why
field strength is measured in volts per metre.**
**Capacitance C = Q/V**; ⚠️ **a geometric property. Parallel plate C = ε₀εᵣA/d.**
**⚠️ Energy stored U = ½CV²**, ⚠️ **and the energy density u = ½ε₀E² lives in the FIELD, not
"in the plates" — a point that becomes essential in §8 → `em-current-energy-flow-circuits-and-ac`.**
**⚠️ The classic paradox worth understanding**: ⚠️ **connect a charged capacitor to an
identical uncharged one and half the energy vanishes regardless of the resistance in the
connecting wire.** **⚠️ It goes to resistive heating or to radiation — and taking the
resistance to zero doesn't save it, which tells you the idealization was hiding physics.**

---

## §5. Dielectrics

**⚠️ Insulators POLARIZE rather than conduct** — ⚠️ **bound charges shift or molecular
dipoles align, producing an internal field that partially opposes the applied one.**
**⚠️ Relative permittivity εᵣ therefore reduces the field for a given charge and increases
capacitance.**
**⚠️ Dielectric strength** is the field at which breakdown occurs — ⚠️ **and note it's a
FIELD limit (V/m), not a voltage limit, which is why thin insulation fails at low voltage
and why sharp edges (§3) initiate breakdown.**
**⚠️ Frequency dependence matters practically**: ⚠️ **different polarization mechanisms
(electronic, ionic, dipolar) respond at different timescales, so εᵣ falls with frequency
and the imaginary part (loss tangent) determines dielectric heating — which is exactly how
a microwave oven works.**

---

# PART II — CURRENT AND CIRCUITS
