---
name: physics-reference
description: "Use when checking a physical constant or scale, correcting a common misconception, weighing a contested question of interpretation or of physics, or asking what is genuinely open: the experimental frontier and the anomalies currently live, the textbook canon, the equations worth holding, the scale ladder, and how to tell which framework applies to a given problem. Companion to the other fundamental-physics skills."
---

# Fundamental Physics: Numbers, Misconceptions, Contested Questions, and the Open Frontier

> **Part 5 of 5** of the *Fundamental Physics* reference (plugin `fundamental-physics`), covering §13–§20. Sibling skills: `physics-quantum-mechanics-and-field-theory` (§0–§3), `physics-relativity-black-holes-and-gravitational-waves` (§4–§6), `physics-cosmology-and-astrophysics` (§7–§10), `physics-measurement-problem-and-quantum-gravity` (§11–§12). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The formalism is settled — QM 1925, GR 1915, the Standard Model complete by the 1970s and confirmed in 2012. See §17 below for the experimental frontier, which is the only part that moves.

> **How to read this.** The physics and its mathematics, organized so the connections are
> visible — because the interesting content of this subject is where the frameworks meet
> and where they fail to.
>
> Two markers:
> - **[DURABLE]** — established formalism and confirmed results. Almost everything.
> - **[CONTESTED]** — genuine disagreement among competent physicists (§15, §16, §17).
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
>    technicality awaiting cleanup — it is the central unsolved problem in physics** (§12 → `physics-measurement-problem-and-quantum-gravity`).

---

## §13. Numbers

```
c = 299,792,458 m/s (exact)            ħ = 1.0546×10⁻³⁴ J·s
G = 6.674×10⁻¹¹ m³/(kg·s²)             k_B = 1.381×10⁻²³ J/K
α = 1/137.036 (at low energy)          m_e = 0.511 MeV/c²
m_p = 938.272 MeV/c²                   m_n = 939.565 MeV/c²

Planck scale:  ℓ_P = 1.616×10⁻³⁵ m,  t_P = 5.39×10⁻⁴⁴ s,  M_P = 1.22×10¹⁹ GeV

Higgs 125.25 GeV · W 80.377 GeV · Z 91.188 GeV · top 172.7 GeV
Higgs vev v = 246 GeV
Σm_ν < 0.12 eV (cosmological, model-dependent)

H₀ ≈ 67.4 (CMB) / 73.0 (distance ladder) km/s/Mpc   ⚠️ §17
Ω_m ≈ 0.315 · Ω_Λ ≈ 0.685 · Ω_b ≈ 0.049
Age 13.787 Gyr · T_CMB = 2.7255 K
Critical density ρ_c ≈ 8.5×10⁻²⁷ kg/m³   (~5 H atoms/m³)

Chandrasekhar 1.4 M_⊙ · Solar r_s = 2.95 km · Earth r_s = 8.87 mm
Eddington L ≈ 1.26×10³¹ (M/M_⊙) W
```

---

## §14. Misconceptions

| Claim | Reality |
|---|---|
| "Uncertainty is a measurement disturbance" | ⚠️ **A theorem about non-commuting operators; no sharp joint values exist** (§1.2 → `physics-quantum-mechanics-and-field-theory`) |
| "Entanglement transmits information" | ⚠️ **No-communication theorem. Local statistics are unchanged** (§1.3 → `physics-quantum-mechanics-and-field-theory`) |
| "Bell proved the universe is non-local" | ⚠️ **It rules out *local + realist*. You may drop either** (§1.3 → `physics-quantum-mechanics-and-field-theory`) |
| "Observation requires consciousness" | Decoherence is caused by environmental interaction; a photon suffices (§11 → `physics-measurement-problem-and-quantum-gravity`) |
| "Decoherence solves measurement" | ⚠️ **It explains no-interference and basis selection, not single outcomes** (§11 → `physics-measurement-problem-and-quantum-gravity`) |
| "The Higgs gives everything mass" | ⚠️ **>98% of ordinary matter's mass is QCD binding energy** (§3.4 → `physics-quantum-mechanics-and-field-theory`) |
| "Quarks have never been seen so they may not exist" | Confinement is *predicted* by asymptotic freedom (§3.2 → `physics-quantum-mechanics-and-field-theory`) |
| "Gravity is a force" | ⚠️ **It's spacetime curvature; free-fall is unaccelerated** (§4.2 → `physics-relativity-black-holes-and-gravitational-waves`) |
| "Nothing escapes a black hole's gravity because it's so strong" | ⚠️ **The horizon is a causal boundary — all future light cones point inward** (§5.1 → `physics-relativity-black-holes-and-gravitational-waves`) |
| "You'd be crushed at the event horizon" | Tidal force `∝ M/r³` — ⚠️ **for a supermassive BH, the horizon is unremarkable** (§5.1 → `physics-relativity-black-holes-and-gravitational-waves`) |
| "The universe expands into something" | No exterior. The metric's scale factor grows (§7.1 → `physics-cosmology-and-astrophysics`) |
| "Redshift is Doppler shift" | ⚠️ **Wavelengths stretch with the metric** (§7.1 → `physics-cosmology-and-astrophysics`) |
| "Galaxies receding faster than c breaks relativity" | ⚠️ **Nothing moves through space superluminally** (§7.1 → `physics-cosmology-and-astrophysics`) |
| "The Big Bang was an explosion at a point" | It happened everywhere; it's an expansion of the metric |
| "Dark matter is just a fudge factor" | ⚠️ **Five independent lines; the Bullet Cluster is decisive against pure modified gravity** (§10 → `physics-cosmology-and-astrophysics`) |
| "Dark energy is a mysterious substance" | ⚠️ **Observationally it's just `w ≈ −1`. Λ in the field equations is the simplest description** (§7 → `physics-cosmology-and-astrophysics`) |
| "String theory is proven / is pseudoscience" | ⚠️ **Neither. Mathematically productive, empirically unconfirmed** (§12 → `physics-measurement-problem-and-quantum-gravity`) |
| "Relativistic mass increases with speed" | Deprecated. Mass is the invariant (§4.1 → `physics-relativity-black-holes-and-gravitational-waves`) |
| "Hawking radiation comes from a particle pair splitting at the horizon" | ⚠️ **A heuristic Hawking himself deprecated; the real derivation is Bogoliubov mixing of field modes** (§5.4 → `physics-relativity-black-holes-and-gravitational-waves`) |
| "Quantum gravity is needed everywhere GR breaks down" | ⚠️ **EFT works fine below the Planck scale** (§12 → `physics-measurement-problem-and-quantum-gravity`) |

---

## §15. Contested: Interpretation

**[CONTESTED — and note that these are empirically equivalent for all current
experiments. Choosing between them is not (yet) a physics question, and pretending
otherwise is a category error in both directions.]**

**Copenhagen / "shut up and calculate"** — the working default. Collapse is a primitive.
⚠️ **Criticized for leaving "measurement" undefined; defended as appropriate epistemic
restraint.**

**Many-Worlds (Everett)** — only unitary evolution; branching is real. ⚠️ **Elegantly
removes postulate 4 but must then derive the Born rule from within, and whether that has
been done non-circularly is genuinely disputed.**

**de Broglie–Bohm (pilot wave)** — deterministic, particles have definite positions guided
by the wavefunction. ⚠️ **Explicitly non-local (which Bell permits), and awkward to make
relativistic.**

**Objective collapse (GRW, CSL)** — modifies the dynamics. ⚠️ **The one class that is
genuinely falsifiable, and experiments are progressively constraining the parameter space.**

**QBism / relational / consistent histories** — the wavefunction is epistemic or
observer-relative. ⚠️ **PBR constrains naive epistemic readings** (§1.3 → `physics-quantum-mechanics-and-field-theory`).

**⚠️ My honest read**: the disagreement is real, the physicists holding each position are
serious, and **anyone telling you it's settled — in either direction — is overstating.**
The one thing that *is* settled is that local hidden variables are dead.

---

## §16. Contested: Physics

**16.1 Is dark matter particulate or is gravity modified?** ⚠️ **Overwhelmingly favoured:
particles.** The Bullet Cluster and the CMB third peak are extremely hard for modified
gravity. **But** MOND's success on galaxy rotation curves and the tightness of the baryonic
Tully–Fisher relation are **real and not well explained by ΛCDM at galactic scales.**
**The honest position: dark matter is right, and the small-scale successes of MOND are an
unexplained regularity that ΛCDM should account for and currently doesn't.**

**16.2 Is inflation established?** *For*: it predicted `n_s < 1` and the acoustic peak
structure, and nothing else does as well. *Against* (⚠️ **Steinhardt, Ijjas, Loeb make this
seriously**): eternal inflation makes anything possible, which undercuts falsifiability,
and the initial conditions problem may be relocated rather than solved. **Undetected `r`
keeps this open.**

**16.3 Is the multiverse science?** ⚠️ **Genuinely disputed on methodological grounds.**
Landscape + eternal inflation makes anthropic reasoning tempting; critics argue an
unfalsifiable framework is not physics. **This is a real disagreement about what science
is, not just about facts.**

**16.4 Is string theory worth the investment?** §12 → `physics-measurement-problem-and-quantum-gravity`. **For**: it's the only framework that
consistently quantizes gravity and it generated AdS/CFT. **Against**: decades without a
distinctive testable prediction, and opportunity cost. ⚠️ **Both positions are held by
excellent physicists.**

**16.5 Black hole interiors and firewalls.** The AMPS argument shows unitarity, locality,
and equivalence-principle smoothness at the horizon cannot all hold. ⚠️ **Something has to
give and it isn't agreed which.**

---

## §17. What's Actually Open

**[DURABLE] The formalism in §1–§10 → `physics-quantum-mechanics-and-field-theory`, `physics-relativity-black-holes-and-gravitational-waves`, `physics-cosmology-and-astrophysics` is not in dispute. These are.**

**17.1 ⚠️ The muon g−2 anomaly has substantially dissolved — and this is a genuine change.**
The experimental side got better and better: **Fermilab's Run-1 (2021) reached 0.46 ppm,
Run-2/3 (2023) reached 0.20 ppm, and the third and final result was announced on
3 June 2025**, giving a new experimental world average.

**But the discrepancy was never purely experimental — it was theory.** The Standard Model
prediction hinges on the **hadronic vacuum polarization (HVP)** contribution, and two
methods disagreed:
- **Data-driven (R-ratio)** evaluations from `e⁺e⁻ → hadrons` cross sections gave a value
  implying a ~4–5σ anomaly.
- **⚠️ Lattice QCD** (BMW 2021, then independently confirmed by multiple groups on
  short-, intermediate-, and long-distance "windows") gave a **larger HVP, which removes
  most of the discrepancy.**

**The lattice consensus consolidated**: independent groups (Mainz/CLS, Fermilab/HPQCD/MILC,
RBC/UKQCD, ETM) converged, and by 2025–26 sub-percent lattice determinations of even the
**next-to-leading-order HVP** exist. **The Muon g−2 Theory Initiative's 2025 White Paper**
now uses lattice input.

> **⚠️ GOTCHA — the anomaly moved rather than vanished.** The tension is now **between
> theory methods, not between theory and experiment.** Recent lattice work reports
> **~4.6σ tension with data-driven evaluations based on hadronic cross sections excluding
> the CMD-3 result** — ⚠️ **and CMD-3's 2023 pion form factor measurement disagrees with
> earlier `e⁺e⁻` experiments.** **So the open question is now: why do the hadronic
> cross-section measurements disagree with each other and with the lattice?** That is a
> real unresolved problem, but it is a **QCD and experimental-systematics problem, not
> evidence for new physics.**

**17.2 ⚠️ Dark energy may be evolving — the most consequential live result in cosmology.**
**DESI DR1 (2024)** with 6 million redshifts hinted that `w ≠ −1`; **DR2 (2025)** with
**14 million** strengthened it. Fits to the **CPL parameterization** `w(a) = w₀ + wₐ(1−a)`
favour **`w₀ > −1` and `wₐ < 0`** — dark energy that was phantom-like early and is
quintessence-like now.

**⚠️ Significance is dataset-dependent and quoted between about 2.8σ and 4.2σ.** Read that
carefully: **it depends which supernova compilation and CMB data you combine.**

**⚠️ The serious caveats, which the headlines omit:**
- **CPL is a phenomenological two-parameter fit, and the mapping from the preferred CPL
  region to an actual physical model is not one-to-one** — canonical non-phantom scalar
  fields remain viable in appropriately defined model spaces.
- **Prior sensitivity is real**: analyses with relaxed priors find the posteriors change
  shape, and **one critical review notes that neither DR1 BAO, DR2 BAO, nor DR2 BAO+CMB
  with relaxed priors confirms late-time accelerated expansion today.**
- **Individual tracers dominate the signal** — LRG1 in DR1, LRG2 and ELG1 in DR2 —
  ⚠️ **and "BAO has yet to stabilise."**
- **The signal is in tension with the Hubble tension**: evolving dark energy of this form
  tends to *lower* `H₀`, worsening rather than helping.

**17.3 The Hubble tension.** **CMB-inferred `H₀ ≈ 67.4 ± 0.5` versus distance-ladder
`73.0 ± 1.0` km/s/Mpc — about 5σ.** ⚠️ **DESI has neither alleviated nor worsened it**, and
it persists across model variations. **Either a systematic in one method or new physics
(early dark energy, extra relativistic species, modified recombination).** Unresolved.

**17.4 The `S₈` / clustering tension** — weak lensing prefers slightly less clustering than
the CMB predicts. Smaller than the Hubble tension and less robust, but persistent.

**17.5 The cosmological constant problem.** ⚠️ **QFT's naive vacuum energy estimate exceeds
the observed Λ by up to ~120 orders of magnitude** — the worst quantitative prediction in
physics. **Supersymmetry would help; it isn't observed at accessible scales.** No accepted
resolution.

**17.6 The hierarchy problem.** Why is the Higgs mass 125 GeV rather than being dragged to
`M_P` by radiative corrections? ⚠️ **Naturalness motivated TeV-scale supersymmetry — and
the LHC has not found it**, which is a genuine blow to a decades-old expectation and has
prompted real reconsideration of naturalness as a guide.

**17.7 Neutrino questions.** ⚠️ **Oscillation proves non-zero mass — the only confirmed
laboratory physics beyond the Standard Model.** Open: **absolute mass scale**, **mass
ordering** (normal vs inverted), **Dirac or Majorana** (neutrinoless double beta decay
would settle it), **CP violation in the lepton sector** (⚠️ **a possible route to
leptogenesis and the matter asymmetry**), and sterile states.

**17.8 Baryon asymmetry.** The Sakharov conditions are known; ⚠️ **the Standard Model's CP
violation is orders of magnitude too small.** Unexplained.

**17.9 Strong CP problem.** Why is `θ_QCD < 10⁻¹⁰` when nothing forbids `O(1)`? ⚠️ **The
Peccei–Quinn solution predicts the axion, which doubles as a dark matter candidate** —
searches ongoing.

**17.10 Black hole information.** §5.4 → `physics-relativity-black-holes-and-gravitational-waves`. Replica wormholes and the Page curve suggest
unitarity holds; ⚠️ **the mechanism is not settled.**

**17.11 Quantum gravity.** §12 → `physics-measurement-problem-and-quantum-gravity`. **No experimental guidance at accessible energies.**

**17.12 Also genuinely open**: the **neutron star equation of state** (§9 → `physics-cosmology-and-astrophysics`), the
**core-collapse supernova explosion mechanism**, **early massive galaxies and SMBH seeds**
(JWST finding surprisingly mature systems at high `z`), the **W boson mass** (⚠️ **CDF's
2022 high value remains in tension with other measurements and the SM; not resolved**), and
**turbulence**, which is unsolved everywhere it appears.

---

## §18. Textbooks

| Author | Work | Why |
|---|---|---|
| **Griffiths** | *Introduction to Quantum Mechanics*; *Elementary Particles* | ⚠️ **The best first books in both subjects. Readable without being loose** |
| **Sakurai & Napolitano** | *Modern Quantum Mechanics* | The graduate standard |
| **Shankar** | *Principles of Quantum Mechanics* | Excellent on the formalism |
| **Ballentine** | *Quantum Mechanics: A Modern Development* | ⚠️ **The most careful treatment of the foundations** |
| **Peskin & Schroeder** | *An Introduction to Quantum Field Theory* | The standard QFT text |
| **Schwartz** | *QFT and the Standard Model* | ⚠️ **More modern and more readable than Peskin** |
| **Weinberg** | *The Quantum Theory of Fields* (3 vols) | Deep, idiosyncratic, definitive |
| **Zee** | *QFT in a Nutshell*; *GR in a Nutshell* | ⚠️ **Physical insight over rigour. Read alongside a standard text** |
| **Misner, Thorne & Wheeler** | ***Gravitation*** ("MTW") | The 1,200-page classic. Still unmatched on intuition |
| **Wald** | *General Relativity* | ⚠️ **The mathematically rigorous choice** |
| **Carroll** | ***Spacetime and Geometry*** | ⚠️ **The best modern GR textbook; lecture notes free online** |
| **Hartle** | *Gravity* | "Physics first" — accessible entry |
| **Schutz** | *A First Course in General Relativity* | Gentler on the differential geometry |
| **Dodelson & Schmidt** | *Modern Cosmology* | The standard cosmology text |
| **Weinberg** | *Cosmology* | Rigorous and demanding |
| **Peebles** | *Principles of Physical Cosmology* | Historical depth from a founder |
| **Carroll & Ostlie** | *Modern Astrophysics* | ⚠️ **The comprehensive undergraduate astrophysics reference** |
| **Shapiro & Teukolsky** | *Black Holes, White Dwarfs and Neutron Stars* | §9 → `physics-cosmology-and-astrophysics` definitively |
| **Nielsen & Chuang** | *Quantum Computation and Quantum Information* | ⚠️ **The best treatment of entanglement and density matrices anywhere** |
| **Bell** | *Speakable and Unspeakable in QM* | ⚠️ **Read Bell on Bell. Unusually clear thinking** |

**Primary sources**: **arXiv** (hep-th, hep-ph, gr-qc, astro-ph), **Particle Data Group
Review of Particle Physics** (⚠️ **the authoritative compilation — free, and where you
should check any particle number**), **NASA ADS**, **Living Reviews in Relativity**.

---

## §19. Quick Reference

### 19.1 The equations
```
iħ ∂|ψ⟩/∂t = Ĥ|ψ⟩                     Schrödinger
σ_A σ_B ≥ ½|⟨[Â,B̂]⟩|                  uncertainty
⟨f|i⟩ = ∫𝒟φ e^(iS/ħ)                  path integral
G_μν + Λg_μν = 8πG T_μν /c⁴           Einstein field equations
ds² = −(1−r_s/r)c²dt² + …             Schwarzschild
S_BH = k_B A/(4ℓ_P²)                  Bekenstein–Hawking
T_H = ħc³/(8πGMk_B)                   Hawking temperature
(ȧ/a)² = 8πGρ/3 − kc²/a² + Λc²/3      Friedmann
1 + z = a(t₀)/a(t_e)                  cosmological redshift
dP/dr = −Gmρ/r²                       hydrostatic equilibrium
L_Edd = 4πGMm_p c/σ_T                 Eddington limit
E² = (pc)² + (mc²)²                   relativistic energy
```

### 19.2 Scale ladder
```
Planck length        10⁻³⁵ m       ⚠️ where §12 bites
Proton               10⁻¹⁵ m
Atom                 10⁻¹⁰ m
Human                10⁰ m
Earth                10⁷ m
Sun                  10⁹ m
Solar system         10¹³ m
Light year           10¹⁶ m
Galaxy               10²¹ m
Observable universe  10²⁶ m        ⚠️ ~93 Gly across, larger than 13.8 Gly × 2 — expansion
```

### 19.3 Which framework applies
| Regime | Use |
|---|---|
| Small, slow | Quantum mechanics (§1 → `physics-quantum-mechanics-and-field-theory`) |
| Small, fast, particle number varying | QFT (§3 → `physics-quantum-mechanics-and-field-theory`) |
| Large, weak gravity | Newton |
| Large, strong gravity or precision timing | GR (§4.2 → `physics-relativity-black-holes-and-gravitational-waves`) |
| Large mass **and** small scale | ⚠️ **Nobody knows (§12 → `physics-measurement-problem-and-quantum-gravity`)** |
| Whole universe, large scale | FLRW + ΛCDM (§7 → `physics-cosmology-and-astrophysics`) |

---

## §20. Method

**This document is physics.** §1–§14 → `physics-quantum-mechanics-and-field-theory`, `physics-relativity-black-holes-and-gravitational-waves`, `physics-cosmology-and-astrophysics`, `physics-measurement-problem-and-quantum-gravity` rest on the standard graduate literature — Sakurai,
Peskin & Schroeder, Schwartz, MTW, Wald, Carroll, Dodelson, Shapiro & Teukolsky — and on
primary results that are decades old and repeatedly confirmed: **Schrödinger (1926), Dirac
(1928), Einstein (1915), Bell (1964), Hawking (1974), Weinberg–Salam–Glashow (1967–8),
Gross–Politzer–Wilczek (1973)**. None of that has a currency dependency and none of it was
web-verified, because the textbooks are the authority and they are stable.

**Two searches were run in August 2026, confined to §17's experimental frontier**, where
the situation has genuinely changed: the muon g−2 theory picture and the DESI dark energy
result.

**Confidence.** **Very high** in §1–§10 → `physics-quantum-mechanics-and-field-theory`, `physics-relativity-black-holes-and-gravitational-waves`, `physics-cosmology-and-astrophysics`, §13, §14 — settled physics, cross-checked against
standard references. **High** in §11 → `physics-measurement-problem-and-quantum-gravity` and §12 → `physics-measurement-problem-and-quantum-gravity`'s characterization of the problems, which is
the mainstream framing. **High** on §17.1's muon g−2 account: the Fermilab measurement
dates and precisions and the lattice/data-driven split come from the collaboration's own
2025 result document and multiple independent lattice papers.

⚠️ **Moderate and deliberately hedged on §17.2.** The DESI significance genuinely varies —
**I have quoted the 2.8σ–4.2σ range rather than a single figure because the number depends
on dataset combination**, and I have foregrounded the critical literature (prior
sensitivity, individual-tracer dominance, the CPL-to-physical-model mapping) **because the
enthusiastic reading is far easier to find than the sceptical one.** ⚠️ **Several of those
critiques come from a small number of authors who have made this argument repeatedly**;
they are serious and published, but they are not the collaboration's view. **Treat evolving
dark energy as a live and interesting result, not an established one.**

**§15 and §16 are contested by construction** and I have tried to state each position in
its strongest form rather than adjudicate — except where a theorem settles it (local hidden
variables are excluded; that is not a matter of taste). **§17's list is my assessment of
where the field's open problems sit**; a specialist in any one area would add detail and
might reorder the priorities.
