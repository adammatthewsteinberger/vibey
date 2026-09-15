---
name: em-conduction-semiconductors-grounding-and-electrical-safety
description: "Use for materials and real-world electrical practice: conduction and band theory, semiconductors and junction behaviour, superconductivity and how to read a superconductivity claim, plasma, grounding, shielding and EMC including ground loops and return-current paths, and the physics of electrical safety — what current does to the body, why let-go thresholds matter, and how protective devices actually work."
---

# Electromagnetism: Conduction and Band Theory, Semiconductors, Superconductivity, Plasma, Grounding, Shielding and EMC, and the Physics of Electrical Safety

> **Part 5 of 6** of the *Electromagnetism and the Physics of Electricity* reference (plugin `electromagnetism-and-electricity`), covering §20–§25. Sibling skills: `em-electrostatics-fields-potential-and-dielectrics` (§0–§5), `em-current-energy-flow-circuits-and-ac` (§6–§11), `em-magnetism-induction-and-transformers` (§12–§15), `em-maxwell-waves-transmission-lines-and-relativity` (§16–§19), `em-reference` (§26–§31). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> after power is removed, and it is CURRENT THROUGH THE BODY that harms** (§25). **Nothing
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

## §20. Conduction and Band Theory

**⚠️ The Drude model (electrons as a classical gas) gets DC conductivity roughly right and
fails badly on heat capacity and the temperature dependence** — ⚠️ **which was one of the
motivations for quantum theory.**
**⚠️ Band theory is the correct picture**: ⚠️ **atomic levels broaden into bands; the FERMI
LEVEL and the presence or absence of a gap determine everything.**
```
⚠️ CONDUCTOR      partially filled band — carriers available at any energy
⚠️ INSULATOR      large gap (⚠️ several eV) — no carriers at room temperature
⚠️ SEMICONDUCTOR  small gap (⚠️ ~1 eV) — ⚠️ thermally excited carriers,
                  hence conductivity RISING with temperature (§7)
```
**⚠️ Resistance in metals comes from SCATTERING** — ⚠️ **from phonons (temperature-dependent)
and from impurities and defects (temperature-independent, the residual resistivity).**
⚠️ **A perfect lattice at absolute zero would have zero resistance without being
superconducting — the mechanisms are different** (§22).

---

## §21. Semiconductors

**⚠️ Doping**: **n-type (donors, electrons) and p-type (acceptors, holes).** ⚠️ **Holes are
genuine quasiparticles with positive charge and their own mobility, not merely "missing
electrons" as a bookkeeping device.**
**⚠️ The pn junction** is where it all comes from: ⚠️ **diffusion creates a depletion region
and a built-in potential; forward bias reduces the barrier and current flows
exponentially; reverse bias widens it and blocks.**
**⚠️ Devices**: **diodes, BJTs (current-controlled), MOSFETs (⚠️ voltage-controlled, and the
basis of essentially all digital logic), LEDs and photodiodes (⚠️ direct-bandgap materials
required for efficient light emission), and solar cells.**
**⚠️ MOSFET switching physics is what governs power electronics** (§26.2 → `em-reference`): ⚠️ **conduction
loss (I²R_DS(on)) and SWITCHING loss (energy per transition × frequency).** ⚠️ **Faster
switching cuts switching loss and raises EMI and ringing — the central design tension.**
**⚠️ Wide-bandgap materials** (SiC ~3.3 eV, GaN ~3.4 eV vs silicon ~1.1 eV) ⚠️ **have higher
breakdown fields, allowing thinner drift regions and therefore much lower on-resistance at
a given voltage** (§26.2 → `em-reference`).

---

## §22. Superconductivity

```
⚠️ TWO defining properties, and the second is the real test
   ⚠️ ZERO DC RESISTANCE below Tc
   ⚠️ THE MEISSNER EFFECT — ACTIVE expulsion of magnetic flux.
      ⚠️ This is NOT merely "perfect conductivity"; a perfect
      conductor would trap existing flux, while a superconductor
      EXPELS it on cooling through Tc
⚠️ BCS THEORY  phonon-mediated Cooper pairs; explains conventional
   superconductors and ⚠️ does NOT satisfactorily explain the cuprates
⚠️ TYPE I vs TYPE II  ⚠️ Type II admits flux vortices and survives to
   much higher fields — which is why all practical magnets are Type II
⚠️ CRITICAL SURFACE  ⚠️ THREE limits: temperature, magnetic field AND
   current density. All three must be satisfied
```
**⚠️ Applications where it already matters**: ⚠️ **MRI magnets, particle accelerators,
SQUIDs (extraordinarily sensitive magnetometers), superconducting qubits, and fusion
magnets — where high-temperature superconducting tape has been genuinely enabling.**
**⚠️ See §26.1 → `em-reference`**, ⚠️ **because this is a field with an unusually instructive recent record
of extraordinary claims.**

---

## §23. Plasma

**⚠️ Ionized gas, quasi-neutral, dominated by collective electromagnetic behaviour** —
**⚠️ and the most common state of ordinary matter in the universe.**
**Debye shielding, plasma frequency (⚠️ below which EM waves are reflected — which is why
the ionosphere reflects HF radio and enables long-distance shortwave), and magnetohydro-
dynamics.**
**⚠️ Everyday plasmas**: **fluorescent and neon lamps, arc welding, lightning, sparks,
and plasma etching in semiconductor manufacture.**
**⚠️ Arcs have a negative resistance region** (§7 → `em-current-energy-flow-circuits-and-ac`), ⚠️ **which is why they need ballast to
be stable and why DC arcs are so hard to extinguish — a real problem in high-voltage DC
switchgear and in EV and solar systems.**

---

# PART VI — PRACTICE

## §24. Grounding, Shielding and EMC

> **⚠️ "Ground" is the most abused word in electronics.** ⚠️ **It means at least three
> different things — earth safety connection, a circuit reference node, and a return
> current path — and conflating them causes most grounding problems.**
```
⚠️ THE CENTRAL INSIGHT (from §8)  ⚠️ CURRENT FLOWS IN LOOPS, and the
   LOOP AREA determines both radiated emission and susceptibility.
   ⚠️ Minimize loop area and most EMC problems shrink
⚠️ RETURN CURRENT PATH  ⚠️ above a few hundred kHz, return current
   flows DIRECTLY UNDER the signal trace, because that minimizes
   inductance (§7). ⚠️ Splitting a ground plane under a trace forces
   a detour and creates a large loop — a classic self-inflicted failure
⚠️ GROUND LOOPS  two "ground" points at different potentials, joined,
   giving circulating current. ⚠️ The cause of hum in audio
⚠️ SHIELDING  ⚠️ works by reflection and absorption; ⚠️ APERTURES
   matter relative to wavelength — a shield with a slot longer than
   ~λ/20 leaks badly, which is why seams and cable entries dominate
⚠️ DECOUPLING  local charge reservoirs, ⚠️ effective only below their
   self-resonant frequency (§9)
COMMON MODE vs DIFFERENTIAL MODE — ⚠️ different problems, different cures
```

---

## §25. ⚠️ The Physics of Electrical Safety

> **⚠️ CURRENT through the body causes harm, not voltage — but voltage is what drives it
> through a body of given impedance, so both matter.**
```
⚠️ APPROXIMATE EFFECTS of AC current through the body (mA, hand to hand)
   ~1        perception threshold
   ~5        painful
   ⚠️ ~10-20 "LET-GO" threshold exceeded — ⚠️ muscles contract and
             the person CANNOT RELEASE the conductor. ⚠️ This is why
             low-current shocks kill: the victim can't let go
   ⚠️ ~100+  VENTRICULAR FIBRILLATION — the usual mechanism of death
   Higher    burns, cardiac arrest, respiratory arrest
⚠️ BODY IMPEDANCE  varies hugely: ⚠️ DRY skin is a substantial
   resistance; ⚠️ WET or broken skin drops it dramatically.
   ⚠️ This is why bathrooms and outdoor sockets are high-risk
⚠️ PATH MATTERS  ⚠️ hand-to-hand or hand-to-foot crosses the heart.
   Hence the "one hand in the pocket" habit
⚠️ FREQUENCY  ⚠️ mains frequency (50/60 Hz) is close to the WORST case
   for fibrillation; higher frequencies are less dangerous
   electrically and more dangerous thermally
```
**⚠️ Protective devices and what each actually does**: ⚠️ **FUSES and BREAKERS protect the
WIRING from overcurrent — they do NOT protect people, because the fault current through a
person is far below their trip rating.** ⚠️ **RCD / GFCI devices protect PEOPLE by detecting
an imbalance between live and neutral (current going somewhere it shouldn't) and tripping
at a few tens of milliamps in milliseconds.** **⚠️ AFCIs detect arcing.**
**⚠️ Earthing** provides a low-impedance fault path so protective devices operate; ⚠️ **and
equipotential bonding prevents dangerous potential DIFFERENCES rather than eliminating
voltage.**
**⚠️ Capacitors and stored energy**: ⚠️ **large capacitors hold lethal charge long after
disconnection — CRT and switch-mode supplies especially.** **Discharge and verify.**
**⚠️ Static discharge** is high voltage, tiny energy — ⚠️ **harmless to people, routinely
destructive to semiconductors, which is why ESD precautions exist.**
