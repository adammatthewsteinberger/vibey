---
name: biochem-thermodynamics-kinetics-and-equilibrium
description: "Use when asking whether a reaction goes and how fast: the laws of thermodynamics and the Gibbs free energy relation, enthalpy and entropy, chemical kinetics and rate laws, activation energy and catalysis, equilibrium and Le Chatelier, acid-base chemistry, pH and buffers, and redox and electrochemistry including half-reactions, cell potentials and the Nernst equation."
---

# Biology and Chemistry Foundations: Thermodynamics, Kinetics, Equilibrium, and Electrochemistry

> **Part 2 of 5** of the *Biology and Chemistry Foundations* reference (plugin `biology-chemistry-foundations`), covering §4–§7. Sibling skills: `biochem-atoms-bonding-and-intermolecular-forces` (§0–§3), `biochem-organic-chemistry-and-analytical-methods` (§8–§9), `biochem-biomolecules-cells-and-evolution` (§10–§16), `biochem-reference` (§17–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Settled science — thermodynamics is 19th century, quantum chemistry and the Michaelis-Menten treatment early 20th, the genetic code and the chemiosmotic hypothesis 1960s. Nothing here has a currency dependency.

> **Scope.** The layer underneath. A biomedical-engineering reference covers imaging,
> signals, PK/PD and clinical statistics; a genetics-and-neuroscience reference covers
> molecular genetics, gene regulation and circuits. **This document is what both of those
> assume you already know** — and it points there rather than repeating.
>
> **⚠️ GOTCHA** boxes mark where the standard teaching account is wrong, or where an
> equation gets applied outside its validity.
>
> **The three ideas that unify everything below:**
> 1. **⚠️ Electronegativity difference drives nearly all of chemistry.** Bonding type,
>    polarity, solubility, acidity, and reaction direction all follow from where electrons
>    prefer to sit (§1.3 → `biochem-atoms-bonding-and-intermolecular-forces`, §2 → `biochem-atoms-bonding-and-intermolecular-forces`).
> 2. **⚠️ ΔG determines direction; kinetics determines whether it happens in your
>    lifetime.** These are independent, and conflating them is the most common error in
>    both chemistry and biology (§4, §5).
> 3. **Life is a kinetically-controlled, thermodynamically-open system.** ⚠️ **Enzymes
>    never change equilibrium — they change the rate of approach to it.** Everything
>    metabolism does is couple unfavourable reactions to favourable ones and keep the
>    system far from equilibrium (§11 → `biochem-biomolecules-cells-and-evolution`, §12 → `biochem-biomolecules-cells-and-evolution`).

---

## §4. Thermodynamics

### 4.1 The laws and the central equation
```
0th  thermal equilibrium is transitive → temperature exists
1st  ΔU = q − w                        energy conserved
2nd  ΔS_universe > 0 for any spontaneous process
3rd  S → 0 as T → 0 for a perfect crystal
```
**Enthalpy** `H = U + PV`, so `ΔH = q_p` at constant pressure.
**Gibbs free energy** — ⚠️ **the master equation:**
```
ΔG = ΔH − TΔS
ΔG < 0  spontaneous (exergonic)     ΔG > 0  non-spontaneous     ΔG = 0  equilibrium
```

> **⚠️ GOTCHA — the four things ΔG does not tell you.**
> 1. **Nothing about rate.** ⚠️ **Diamond → graphite has ΔG < 0 and takes geological
>    time.** Spontaneous ≠ fast (§5).
> 2. **"Spontaneous" is a technical term meaning thermodynamically favourable**, not
>    "happens by itself quickly."
> 3. **⚠️ ΔG° (standard state) ≠ ΔG (actual).** `ΔG = ΔG° + RT ln Q`. **Cells operate far
>    from standard state, and reactions with unfavourable ΔG° run forward routinely
>    because Q is held low by consuming the product** (§12 → `biochem-biomolecules-cells-and-evolution`).
> 4. **Exothermic ≠ spontaneous.** ⚠️ **Ice melting above 0 °C is endothermic and
>    spontaneous** — TΔS wins.

**Entropy is not "disorder"** — ⚠️ **it's the number of accessible microstates**,
`S = k_B ln W`. **The disorder metaphor fails badly** for the hydrophobic effect (§3.2 → `biochem-atoms-bonding-and-intermolecular-forces`),
where aggregation *increases* total entropy.

**Coupling**: an unfavourable reaction runs if coupled to a more favourable one sharing an
intermediate. ⚠️ **This is the entire logic of ATP in metabolism** (§12 → `biochem-biomolecules-cells-and-evolution`).

**Hess's law**: ΔH is path-independent. **`ΔG° = −RT ln K`** connects thermodynamics to
equilibrium (§6), and **`ΔG° = −nFE°`** connects it to redox (§7).

---

## §5. Kinetics

**Rate laws** are experimental, not stoichiometric: `rate = k[A]^m[B]^n`.
⚠️ **Order is determined by the mechanism, specifically the rate-determining step — you
cannot read it off the balanced equation.**

```
Zero order:   [A] = [A]₀ − kt         t½ = [A]₀/2k
First order:  ln[A] = ln[A]₀ − kt     ⚠️ t½ = ln2/k — INDEPENDENT of concentration
Second order: 1/[A] = 1/[A]₀ + kt     t½ = 1/(k[A]₀)
```
**⚠️ The concentration-independent half-life of first-order kinetics is why radioactive
decay and most drug elimination have a fixed t½** (see a biomedical-engineering
reference §8).

**Arrhenius**: `k = A·e^(−Ea/RT)`, or `ln k = ln A − Ea/RT`.
⚠️ **The exponential dependence is why a 10 °C rise roughly doubles many reaction rates**,
and why small Ea reductions produce enormous rate increases.

**Transition state theory**: reaction proceeds through a maximum-energy configuration.
`ΔG‡` is the activation barrier, and `k ∝ e^(−ΔG‡/RT)`.

> **⚠️ GOTCHA — catalysts and equilibrium.** A catalyst **lowers ΔG‡, accelerating forward
> and reverse reactions equally.** ⚠️ **It cannot change ΔG, K, or the equilibrium
> position.** Any claim that a catalyst "drives" a reaction to completion is wrong — what
> drives it is removing product (§4.1, Le Chatelier §6).

---

## §6. Equilibrium and Acid-Base

**Equilibrium constant** `K = [products]^coeffs/[reactants]^coeffs` (activities, strictly).
**Reaction quotient Q** compared to K gives direction: ⚠️ **Q < K → forward; Q > K →
reverse.**
**Le Chatelier**: a system at equilibrium shifts to partially oppose an imposed change.
⚠️ **"Partially" is the word people drop — the system never fully undoes the disturbance.**

**Acids and bases**: Arrhenius (H⁺/OH⁻) → **Brønsted-Lowry** (proton donor/acceptor,
⚠️ **conjugate pairs**) → **Lewis** (electron pair acceptor/donor — ⚠️ **the most general,
and the one organic mechanism uses**).

```
pH = −log[H⁺]           K_w = [H⁺][OH⁻] = 1.0×10⁻¹⁴ at 25 °C
pK_a = −log K_a         ⚠️ lower pK_a = stronger acid
Henderson-Hasselbalch:  pH = pK_a + log([A⁻]/[HA])
```
**⚠️ Buffers work best within ±1 pH unit of pK_a**, and maximum buffer capacity is *at*
pK_a where `[A⁻] = [HA]`. **Physiological buffers**: bicarbonate (⚠️ **pK_a 6.1, which
looks poorly matched to pH 7.4 — it works because CO₂ is an open system vented by the
lungs**), phosphate (pK_a 7.2), and protein histidine residues (pK_a ~6).

**⚠️ What determines acid strength** — and this is the mechanistic core:
1. **Conjugate base stability.** Anything stabilizing A⁻ strengthens HA.
2. **Electronegativity** — right across a period. CH₄ < NH₃ < H₂O < HF.
3. **Size** — down a group. ⚠️ **HI > HBr > HCl > HF**, because the larger anion spreads
   charge better. **This overrides electronegativity and surprises people.**
4. **Resonance** — ⚠️ **carboxylic acids (pK_a ~5) beat alcohols (pK_a ~16) by ten orders
   of magnitude because the carboxylate delocalizes charge over two oxygens.**
5. **Induction** — electron-withdrawing groups nearby. Trichloroacetic acid pK_a 0.7 vs
   acetic 4.76.

**Solubility**: `K_sp`, common-ion effect, and ⚠️ **pH dependence for salts of weak acids.**

---

## §7. Redox and Electrochemistry

**Oxidation is electron loss; reduction is gain** (⚠️ **OIL RIG**). Track with **oxidation
states.**

**Cell potential**: `E°_cell = E°_cathode − E°_anode`.
```
ΔG° = −nFE°           F = 96,485 C/mol
Nernst: E = E° − (RT/nF)·ln Q   ≈  E° − (0.0592/n)·log Q at 25 °C
```
**⚠️ The Nernst equation is the same one that gives membrane potentials** (see a
genetics-and-neuroscience reference §7) — an ion gradient is an electrochemical cell.

**⚠️ Positive E° means favourable, and the standard hydrogen electrode is the arbitrary
zero.** In biology, the convention is **E°′ at pH 7** rather than pH 0, which changes
values substantially — ⚠️ **quoting an E° from a chemistry table for a biological
half-reaction is a common error.**

**Biologically central couples (E°′, pH 7):**
```
NAD⁺/NADH        −0.32 V     ⚠️ strong reductant — the electron donor of catabolism
FAD/FADH₂        ~−0.22 V
Ubiquinone       +0.045 V
Cytochrome c     +0.254 V
½O₂/H₂O          +0.816 V    ⚠️ the terminal acceptor, and why aerobic respiration
                              yields so much: ΔE°′ ≈ 1.14 V from NADH to O₂
```
