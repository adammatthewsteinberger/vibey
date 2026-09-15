---
name: semi-transistor-architectures-interconnect-memory-and-wafers
description: "Use for modern devices and starting material: transistor architectures from planar through FinFET to gate-all-around and what each solved, interconnect and why wires rather than transistors now dominate delay and power, the memory technologies and their cell structures, and how sand becomes a polished monocrystalline wafer."
---

# Semiconductors and Chip Manufacturing: Transistor Architectures, Interconnect, Memory, and From Sand to Wafer

> **Part 2 of 6** of the *Semiconductors and Chip Manufacturing* reference (plugin `semiconductors-and-chip-manufacturing`), covering §6–§9. Sibling skills: `semi-carriers-doping-junctions-mosfet-and-scaling` (§0–§5), `semi-cleanroom-lithography-deposition-etch-and-cmp` (§10–§15), `semi-integration-yield-metrology-test-and-packaging` (§16–§20), `semi-pcb-assembly-reliability-design-flow-and-economics` (§21–§26), `semi-reference` (§27–§32). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The physics is settled. Two frontiers are moving. See §27 → `semi-reference` for High-NA lithography adoption, and advanced packaging as the binding constraint.

> **⚠️ The most complex manufacturing humans do, by a wide margin.** ⚠️ **A leading-edge
> chip involves on the order of a thousand process steps, features smaller than a virus,
> tolerances measured in atoms, and a supply chain with genuine single points of failure.**
>
> **Builds directly on an electromagnetism reference (band theory, pn junctions, MOSFET
> physics, wide-bandgap materials). Complements a manufacturing reference (tolerancing and
> yield), an organic-chemistry reference (photoresists and packaging polymers), and a
> resource-extraction reference (where the materials come from).**
>
> **⚠️ GOTCHA** boxes mark where marketing and physics diverge — and this industry has more
> of that gap than most.
>
> **The three ideas that organize this document:**
> 1. **⚠️ "NODE NAMES ARE MARKETING"** (§5 → `semi-carriers-doping-junctions-mosfet-and-scaling`). **"3nm" does not describe any physical
>    dimension on the chip. It has been a marketing label for roughly a decade, and
>    comparing nodes across foundries by name is meaningless.**
> 2. **⚠️ YIELD IS THE WHOLE BUSINESS** (§17 → `semi-integration-yield-metrology-test-and-packaging`). **Everything — die size, chiplet
>    architecture, defect control, cleanroom spend — is downstream of the fact that
>    profitability is set by what fraction of die work.**
> 3. **⚠️ THE BOTTLENECK MOVED TO THE BACK END** (§20 → `semi-integration-yield-metrology-test-and-packaging`, §27.2 → `semi-reference`). **For AI accelerators the
>    binding constraint is no longer transistors — it is packaging and memory, which is a
>    genuine reversal of thirty years of industry structure.**

---

## §6. Transistor Architectures

```
⚠️ PLANAR  gate controls the channel from one side. ⚠️ Ran out of
   electrostatic control around 28–22nm
⚠️ FinFET  ⚠️ the channel is a vertical fin, gated on three sides.
   ⚠️ Vastly better control, and it bought roughly a decade.
   ⚠️ Note the quantization: you get integer numbers of fins,
   so drive strength comes in steps
⚠️ GAA / NANOSHEET (RibbonFET at Intel)  ⚠️ the gate wraps the
   channel COMPLETELY — stacked horizontal sheets. ⚠️ Best
   electrostatics, and ⚠️ sheet WIDTH is continuously tunable,
   restoring analog drive-strength control. ⚠️ This is the 2nm-class
   generation now in production
⚠️ CFET (complementary FET)  ⚠️ stack the n and p devices
   VERTICALLY on top of each other. Research/early development —
   the next major architectural step
⚠️ BACKSIDE POWER DELIVERY (PowerVia at Intel, Super Power Rail
   at TSMC)  ⚠️ move power routing to the WAFER BACKSIDE, freeing
   the front side entirely for signal. ⚠️ Reduces IR drop and
   routing congestion — one of the genuinely significant recent
   changes, and separate from the transistor itself
⚠️ STRAIN, high-k/metal gate, and SiGe channels are the materials
   levers used alongside the geometry
```

---

## §7. Interconnect

**⚠️ The wires became the problem.** ⚠️ **Transistors got faster as they shrank; wires got
SLOWER, because resistance rises as cross-section falls while capacitance doesn't fall
proportionally.**
```
⚠️ RC DELAY now dominates at the leading edge, and ⚠️ a large
   fraction of chip power goes into charging and discharging
   interconnect capacitance rather than into switching devices
⚠️ THE MATERIALS RESPONSE  ⚠️ aluminium → COPPER (lower resistivity,
   requiring the DAMASCENE process because copper is hard to etch,
   §13) · ⚠️ LOW-k DIELECTRICS to cut capacitance (⚠️ and they are
   mechanically weak and porous, which causes real integration
   problems)
⚠️ BARRIER LAYERS  ⚠️ copper poisons silicon, so it must be fully
   encapsulated — and the barrier takes an increasing fraction of
   the shrinking wire cross-section, which is a fundamental squeeze
⚠️ ⚠️ ELECTROMIGRATION  ⚠️ momentum transfer from electrons physically
   moves metal atoms, causing voids and eventual open circuits.
   ⚠️ Sets a hard CURRENT DENSITY limit, and it is a wear-out
   mechanism, not a defect (§23)
⚠️ ALTERNATIVES  cobalt and ruthenium for the finest lines;
   ⚠️ and optical interconnect for chip-to-chip (§27.2's CPO)
```

---

## §8. Memory

```
⚠️ SRAM  6 transistors per bit, fast, ⚠️ volatile, ⚠️ EXPENSIVE IN
   AREA. ⚠️ Critically, SRAM HAS SCALED POORLY in recent nodes —
   bitcell area is shrinking much more slowly than logic, which is
   why cache is consuming a growing share of die area and is a
   major driver of chiplet partitioning (§20)
⚠️ DRAM  one transistor + one capacitor. ⚠️ Must be REFRESHED
   because the capacitor leaks. ⚠️ Scaling is limited by the need
   to maintain capacitance in a shrinking footprint — hence deep
   trench and high-aspect-ratio capacitors
   ⚠️ Made on a SEPARATE, specialized process, not logic fabs
⚠️ NAND FLASH  ⚠️ charge trapped on a floating gate or in a charge
   trap. ⚠️ Scaled LATERALLY until it couldn't, then went VERTICAL
   — 3D NAND now stacks hundreds of layers. ⚠️ MLC/TLC/QLC store
   multiple bits per cell by distinguishing charge levels, trading
   density against endurance and retention
   ⚠️ WEAR-OUT IS INTRINSIC — the tunnel oxide degrades with
   program/erase cycles, which is why wear levelling exists
⚠️ HBM  ⚠️ DRAM dies STACKED and connected by through-silicon vias,
   placed adjacent to logic on an interposer. ⚠️ Enormous bandwidth
   via width rather than clock speed — and the central AI
   constraint (§27.2)
⚠️ EMERGING  MRAM, ReRAM, PCM, FeRAM — ⚠️ real products in niches,
   none has displaced the big three
```

---

# PART II — MAKING THE CHIP

## §9. From Sand to Wafer

**⚠️ Metallurgical-grade silicon → the Siemens process → polysilicon of extraordinary
purity → CZOCHRALSKI growth of a single-crystal ingot → slicing, lapping, etching,
polishing → epitaxial layer if required.**
⚠️ **Electronic-grade silicon purity is often quoted at "eleven nines" or better — parts
per billion of impurity — and this is one of the purest materials made at industrial
scale.**
**⚠️ Wafer size economics**: ⚠️ **300 mm is standard; die per wafer scales with AREA while
many process costs scale per WAFER, which is the entire argument for larger wafers.**
⚠️ **450 mm was investigated and effectively abandoned — the tooling cost could not be
justified.**
**⚠️ Crystal orientation, defect density, flatness and edge exclusion** are all specified
tightly, ⚠️ **and the wafer itself is a precision product from a concentrated supplier
base** (§26 → `semi-pcb-assembly-reliability-design-flow-and-economics`).
