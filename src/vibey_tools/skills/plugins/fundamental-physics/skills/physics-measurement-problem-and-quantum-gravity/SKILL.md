---
name: physics-measurement-problem-and-quantum-gravity
description: "Use when reasoning about the foundations rather than the calculations: the measurement problem stated precisely, decoherence and what it does and does not solve, the interpretations (Copenhagen, many-worlds, pilot wave, objective collapse, QBism) and what actually distinguishes them, and the incompatibility of general relativity and quantum field theory — non-renormalizability, the Planck scale, the cosmological constant problem, and the black hole information question."
---

# Fundamental Physics: The Measurement Problem and Why QM and GR Do Not Fit

> **Part 4 of 5** of the *Fundamental Physics* reference (plugin `fundamental-physics`), covering §11–§12. Sibling skills: `physics-quantum-mechanics-and-field-theory` (§0–§3), `physics-relativity-black-holes-and-gravitational-waves` (§4–§6), `physics-cosmology-and-astrophysics` (§7–§10), `physics-reference` (§13–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The formalism is settled — QM 1925, GR 1915, the Standard Model complete by the 1970s and confirmed in 2012. See §17 → `physics-reference` for the experimental frontier, which is the only part that moves.

> **How to read this.** The physics and its mathematics, organized so the connections are
> visible — because the interesting content of this subject is where the frameworks meet
> and where they fail to.
>
> Two markers:
> - **[DURABLE]** — established formalism and confirmed results. Almost everything.
> - **[CONTESTED]** — genuine disagreement among competent physicists (§15 → `physics-reference`, §16 → `physics-reference`, §17 → `physics-reference`).
>
> **⚠️ GOTCHA** boxes mark where the popular account is actively wrong, or where a
> technically-correct statement is routinely misread.
>
> **Conventions**: `ħ = c = 1` in §1–§4 → `physics-quantum-mechanics-and-field-theory`, `physics-relativity-black-holes-and-gravitational-waves` unless stated; metric signature `(−,+,+,+)`;
> Greek indices 0–3, Latin 1–3; Einstein summation throughout.
>
> **The three facts that structure everything:**
> 1. **Symmetry determines dynamics.** Noether's theorem turns every continuous symmetry
>    into a conservation law, and **gauge symmetry doesn't just constrain the Standard
>    Model — it generates it.** Demanding local invariance forces the existence and the
>    couplings of the force carriers (§3.1 → `physics-quantum-mechanics-and-field-theory`).
> 2. **⚠️ Relativity is geometry, not force.** Gravity is not a field on spacetime; it *is*
>    the curvature of spacetime, and free-fall is unaccelerated motion. Nearly every
>    confusion about GR dissolves once that's internalized (§4 → `physics-relativity-black-holes-and-gravitational-waves`).
> 3. **⚠️ The two frameworks are both spectacularly confirmed and mutually inconsistent.**
>    QFT treats spacetime as a fixed stage; GR makes it dynamical. **This is not a
>    technicality awaiting cleanup — it is the central unsolved problem in physics** (§12).

---

## §11. The Measurement Problem

**[DURABLE] State it precisely, because vagueness here generates most of the bad
philosophy.**

Unitary evolution (postulate 5) is linear. Apply it to a measurement: if
`|↑⟩|ready⟩ → |↑⟩|up⟩` and `|↓⟩|ready⟩ → |↓⟩|down⟩`, then linearity **forces**
```
(α|↑⟩ + β|↓⟩)|ready⟩ → α|↑⟩|up⟩ + β|↓⟩|down⟩
```
**⚠️ The apparatus ends up in a superposition of pointer readings.** We never observe that.
**Postulate 4 says we get one outcome with probability `|α|²` — but nothing in the
formalism says when postulate 5 stops and postulate 4 starts.** That's the problem, and it
is a real one, not a confusion.

**Decoherence** — the environment entangles with the system, rapidly (⚠️ **timescales of
10⁻²⁰ s for macroscopic objects**) suppressing interference between pointer states.

> **⚠️ GOTCHA — decoherence does not solve the measurement problem, and saying it does is
> the most common error among physicists who haven't thought about it carefully.**
> Decoherence explains **why we don't see interference** between macroscopic alternatives,
> and it explains **which basis** is selected (einselection). **It does not explain why
> there is one outcome rather than a branching superposition** — the reduced density
> matrix is *improper*, and turning it into a probability distribution over actual
> outcomes still requires an interpretive move. **Decoherence converts the problem from
> "why no interference" to "why one outcome," which is progress, not resolution.**

---

## §12. Why QM and GR Don't Fit

**[DURABLE] The central unsolved problem, and worth being precise about the failure mode.**

**The technical statement**: quantizing GR perturbatively gives a **non-renormalizable**
theory. Newton's constant has dimensions `[G] = mass⁻²`, so each loop order requires new
counterterms — ⚠️ **infinitely many free parameters, and therefore no predictive power at
high energy.** Pure gravity happens to be finite at one loop; **two loops diverges, and
gravity plus matter diverges at one.**

**The conceptual statement is worse than the technical one:**
- **⚠️ QFT presumes a fixed background spacetime** on which fields live and against which
  "time evolution" is defined. **GR makes spacetime dynamical.** There is no background.
- **The problem of time**: canonical quantization gives the **Wheeler–DeWitt equation
  `Ĥ|Ψ⟩ = 0`** — ⚠️ **the total Hamiltonian vanishes, so the wavefunction of the universe
  does not evolve.** Time has to be recovered relationally, and how is unresolved.
- **Locality and observables**: in GR, diffeomorphism invariance means **local observables
  are not gauge-invariant.** What are the observables of quantum gravity?

**⚠️ As an effective field theory, quantum gravity works fine** — you can compute quantum
corrections to Newtonian potential reliably below the Planck scale. **The breakdown is at
`E ~ M_P ≈ 1.22×10¹⁹ GeV`**, which is ~10¹⁵ times beyond LHC energies. **This is why
there is no experimental guidance**, and why the field has been stuck.

**Approaches, honestly characterized:**
- **String theory** — ⚠️ **mathematically deep, produced enormous spin-off physics
  (AdS/CFT, holography), and makes no confirmed distinctive prediction.** The landscape
  problem (~10⁵⁰⁰ vacua) undermines predictivity.
- **Loop quantum gravity** — background-independent by construction, ⚠️ **and has
  difficulty recovering smooth classical spacetime and the Standard Model.**
- **Asymptotic safety, causal set theory, causal dynamical triangulations, group field
  theory** — active, none decisive.
- **⚠️ AdS/CFT (Maldacena, 1997) is the most concrete result in the area**: a gravitational
  theory in `(d+1)`-dimensional anti-de Sitter space is exactly dual to a conformal field
  theory on its `d`-dimensional boundary. **It is a working example of holography and of
  emergent spacetime** — but **our universe is de Sitter, not anti-de Sitter**, and the
  dictionary for realistic cosmology is missing.
