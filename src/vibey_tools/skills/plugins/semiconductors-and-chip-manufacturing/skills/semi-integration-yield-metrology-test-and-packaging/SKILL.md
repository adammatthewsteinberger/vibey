---
name: semi-integration-yield-metrology-test-and-packaging
description: "Use for making the process actually produce working parts: process integration and how hundreds of steps compose, yield and the models and defect mechanisms behind it, metrology and inspection, test including wafer sort, burn-in and the coverage question, and advanced packaging with 2.5D, 3D, chiplets and the interposer and bonding options."
---

# Semiconductors and Chip Manufacturing: Process Integration, Yield, Metrology and Inspection, Test, and Advanced Packaging

> **Part 4 of 6** of the *Semiconductors and Chip Manufacturing* reference (plugin `semiconductors-and-chip-manufacturing`), covering §16–§20. Sibling skills: `semi-carriers-doping-junctions-mosfet-and-scaling` (§0–§5), `semi-transistor-architectures-interconnect-memory-and-wafers` (§6–§9), `semi-cleanroom-lithography-deposition-etch-and-cmp` (§10–§15), `semi-pcb-assembly-reliability-design-flow-and-economics` (§21–§26), `semi-reference` (§27–§32). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 2. **⚠️ YIELD IS THE WHOLE BUSINESS** (§17). **Everything — die size, chiplet
>    architecture, defect control, cleanroom spend — is downstream of the fact that
>    profitability is set by what fraction of die work.**
> 3. **⚠️ THE BOTTLENECK MOVED TO THE BACK END** (§20, §27.2 → `semi-reference`). **For AI accelerators the
>    binding constraint is no longer transistors — it is packaging and memory, which is a
>    genuine reversal of thirty years of industry structure.**

---

## §16. Process Integration

**⚠️ The discipline of making hundreds of individually-working steps work TOGETHER.**
⚠️ **FEOL (front end of line — transistors) → MOL (contacts) → BEOL (interconnect).**
**⚠️ A mask set for a leading node runs to dozens of layers and costs millions**, ⚠️ **which
is a large part of why NRE at the leading edge is prohibitive for low-volume designs**
(§25 → `semi-pcb-assembly-reliability-design-flow-and-economics`).
**⚠️ The integration engineer's problem is that everything interacts**: ⚠️ **a change in
etch chemistry shifts a CMP rate, which changes overlay, which shifts device parameters.**
**⚠️ Process control** uses SPC and increasingly run-to-run feedback (see a manufacturing
reference on Cp/Cpk) — ⚠️ **and PROCESS VARIATION is now a first-order design concern:
random dopant fluctuation, line edge roughness and metal grain variation make nominally
identical transistors measurably different.**

---

## §17. ⚠️ Yield

> **⚠️ The number that decides whether a fab makes money.**
```
⚠️ THE MODELS  ⚠️ Poisson yield ≈ e^(−AD) where A is die area and
   D is defect density. ⚠️ Murphy's and negative binomial models
   are used in practice because defects CLUSTER
⚠️ ⚠️ THE CENTRAL CONSEQUENCE: YIELD FALLS EXPONENTIALLY WITH DIE
   AREA. ⚠️ Doubling die size does far more than double the loss
⚠️ ⚠️ THIS IS THE ENTIRE ARGUMENT FOR CHIPLETS (§20) —
   four small dies yield far better than one large die of the
   same total area, and you can bin and mix them
⚠️ THE RETICLE LIMIT  ⚠️ a hard maximum die size set by the
   exposure field. ⚠️ Large AI accelerators are AT it, which is
   another forcing function toward multi-die
⚠️ YIELD TYPES  ⚠️ line yield (wafers surviving the flow) ·
   ⚠️ DIE yield (good die per wafer) · parametric yield (die that
   work but miss spec) · packaging and final test yield
⚠️ DEFECT SOURCES  particles · pattern defects · ⚠️ systematic
   layout-sensitive defects (⚠️ these are DESIGN issues, addressed
   by DFM rules) · contamination · equipment excursions
⚠️ LEARNING CURVE  ⚠️ yield ramps over months to years; ⚠️ early
   production of a new node is often economically poor, which is
   why node transitions are financially painful
```
**⚠️ Binning** monetizes partial failures — ⚠️ **a die with a defective core or cache block
is sold as a lower-tier product rather than scrapped, which is why product stacks look the
way they do.**

---

## §18. Metrology and Inspection

**⚠️ You cannot control what you cannot measure, at nanometre scale, non-destructively, on
production wafers.**
**⚠️ Techniques**: ⚠️ **CD-SEM for critical dimensions, scatterometry/OCD for profiles,
ellipsometry for film thickness, overlay metrology (⚠️ the tightest budget of all — sub-nm
at the leading edge), and defect inspection by optical and e-beam.**
**⚠️ The fundamental tension**: ⚠️ **optical inspection is fast and cannot resolve the
smallest defects; e-beam resolves them and is far too slow for full-wafer coverage.**
**⚠️ Hence sampling, hot-spot inspection guided by design, and increasing use of machine
learning to classify defects.**
**⚠️ Failure analysis** works backwards from a failing die: ⚠️ **fault isolation, then FIB
cross-sectioning, then TEM — expensive, slow, and the only way to find root cause.**

---

## §19. Test

**⚠️ Testing is a large fraction of total cost and is easy to underestimate.**
⚠️ **WAFER SORT/probe identifies good die before the expense of packaging; ⚠️ FINAL TEST
after packaging; ⚠️ BURN-IN stresses parts to precipitate infant mortality** (§23 → `semi-pcb-assembly-reliability-design-flow-and-economics`).
**⚠️ DESIGN FOR TEST is mandatory**: ⚠️ **scan chains, BIST, and JTAG boundary scan exist
because a billion-transistor chip has no other way to be observed.**
**⚠️ Coverage versus time is the eternal trade** — ⚠️ **test time is money, and untested
faults escape to customers.**
> **⚠️ GOTCHA — KNOWN GOOD DIE is the problem that makes chiplets hard** (§20).
> ⚠️ **If you assemble ten dies into one package and any is bad, you scrap the whole
> assembly including the good ones.** **⚠️ So multi-die packaging requires far higher
> confidence in pre-assembly test than monolithic designs ever did, and reported estimates
> put chiplet test cost at 15–30% above monolithic for this reason.**

---

# PART III — PACKAGING AND BOARDS

## §20. ⚠️ Advanced Packaging

> **⚠️ Historically an afterthought; now the most strategically important part of the
> chain** (§27.2 → `semi-reference`).
```
⚠️ WHAT PACKAGING DOES  ⚠️ electrical connection · POWER delivery ·
   ⚠️ HEAT removal · mechanical protection · and ⚠️ matching the
   chip's micron-scale pitch to the board's millimetre scale
⚠️ TRADITIONAL  wire bond · flip chip (⚠️ solder bumps, area array,
   far better electrically) · BGA
⚠️ 2.5D  ⚠️ multiple dies side by side on a SILICON INTERPOSER with
   fine wiring. ⚠️ TSMC's CoWoS is the dominant example — this is
   how a GPU sits next to HBM stacks
   ⚠️ EMIB (Intel) embeds a small silicon bridge in the substrate
   instead of a full interposer — cheaper, no through-silicon
   interposer needed
⚠️ 3D  ⚠️ dies stacked vertically, connected by THROUGH-SILICON VIAS
   ⚠️ HYBRID BONDING  ⚠️ direct copper-to-copper and oxide-to-oxide
   bonding with no solder — ⚠️ enables micron-scale pitch, far
   denser than microbumps, and it is becoming essential (§27.2)
⚠️ FAN-OUT WAFER LEVEL PACKAGING  redistribution layers, no substrate
⚠️ CHIPLETS  ⚠️ partition a design into dies, each on the process
   node that suits it — logic on the leading edge, I/O and analog
   on cheaper mature nodes. ⚠️ Yield (§17), cost and reticle limit
   all push this way
⚠️ UCIe  ⚠️ the standard die-to-die interconnect, aiming at an open
   chiplet ecosystem
⚠️ THE HARD PARTS  ⚠️ thermal (stacked dies trap heat) · warpage
   from CTE mismatch · ⚠️ known good die (§19) · ⚠️ ABF SUBSTRATE
   supply, which is concentrated and has had long lead times ·
   power delivery through the stack
```
