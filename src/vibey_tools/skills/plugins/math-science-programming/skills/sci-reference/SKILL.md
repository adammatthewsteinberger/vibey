---
name: sci-reference
description: "Use when checking a numerical anti-pattern, weighing a contested question, confirming whether a tooling or ecosystem claim is still current (snapshot verified August 2026), finding the books, documentation and people, or needing the numbers to hold, the what-to-check list for when the numbers are wrong, and a method picker. Companion to the other math-science-programming skills."
---

# Math and Science Programming: Anti-Patterns, Contested Questions, Currency, and Canon

> **Part 5 of 5** of the *Math and Science Programming* reference (plugin `math-science-programming`), covering §15–§20. Sibling skills: `sci-floating-point-and-numerical-foundations` (§0–§3), `sci-tooling-and-symbolic-computation` (§4–§5), `sci-linear-algebra-differential-equations-and-optimization` (§6–§9), `sci-statistics-performance-and-reproducibility` (§10–§14). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 below for the currency snapshot and what goes stale first.

> **How to read this.** Reference for engineers doing numerical work, and for scientists
> who ended up writing production software by accident. Three markers:
> - **[DURABLE]** — numerical analysis, and the engineering practice around it. Most of
>   this document; **floating point hasn't changed since 1985.**
> - **[VERSIONED]** — tools, libraries, ecosystem.
> - **[CONTESTED]** — genuine disagreement.
>
> **⚠️ GOTCHA** boxes mark the places where code runs, produces numbers, and the numbers
> are wrong.
>
> **The three framings that organize everything below:**
> 1. **⚠️ Your code will produce plausible wrong answers, and nothing will crash.** This is
>    the defining hazard of the whole domain. A web service that breaks returns a 500;
>    numerical code that breaks returns a `float`. **Every practice in §13 → `sci-statistics-performance-and-reproducibility` and §14 → `sci-statistics-performance-and-reproducibility` exists
>    because of this one asymmetry.**
> 2. **You are not computing with real numbers.** You're computing with a finite subset of
>    the rationals that doesn't obey associativity or distributivity (§1 → `sci-floating-point-and-numerical-foundations`). **Most numerical
>    bugs are a failure to internalize that**, and the rest are conditioning problems (§2 → `sci-floating-point-and-numerical-foundations`).
> 3. **⚠️ Do not write the algorithm.** LAPACK, SUNDIALS, and the rest represent
>    person-centuries of numerical expertise that you will not replicate. **Your job is to
>    choose the right routine, feed it a well-conditioned problem, and check the
>    answer** — see §3 → `sci-floating-point-and-numerical-foundations` and the anti-pattern table.

---

## §15. Anti-Patterns

| Anti-pattern | Why |
|---|---|
| Comparing floats with `==` | Decimal fractions aren't representable (§1.1 → `sci-floating-point-and-numerical-foundations`) |
| Hand-rolled naive summation over a big array | ⚠️ **Error grows with n; use pairwise/Kahan** (§1.1 → `sci-floating-point-and-numerical-foundations`) |
| Treating a parallel result difference as a bug | ⚠️ **FP addition isn't associative** (§1.1 → `sci-floating-point-and-numerical-foundations`, §11 → `sci-statistics-performance-and-reproducibility`) |
| `sqrt(x*x + y*y)` instead of `hypot` | Intermediate overflow (§1.2 → `sci-floating-point-and-numerical-foundations`) |
| The naive quadratic formula | Catastrophic cancellation on one root (§1.1 → `sci-floating-point-and-numerical-foundations`) |
| `-ffast-math` on code you haven't analyzed | ⚠️ **Permits reassociation, assumes no NaN/inf** (§1.1 → `sci-floating-point-and-numerical-foundations`) |
| Never checking the condition number | ⚠️ **κ=10¹⁶ means zero significant digits, silently** (§2 → `sci-floating-point-and-numerical-foundations`) |
| Refining the mesh/step indefinitely | ⚠️ **Total error has a minimum; past it you get worse** (§2 → `sci-floating-point-and-numerical-foundations`) |
| High-degree polynomial fit on raw equispaced data | Vandermonde conditioning + Runge (§2 → `sci-floating-point-and-numerical-foundations`, §9 → `sci-linear-algebra-differential-equations-and-optimization`) |
| **`inv(A) @ b`** | ⚠️ **Slower, less accurate, less stable than `solve`** (§6 → `sci-linear-algebra-differential-equations-and-optimization`) |
| `det(A)` as a singularity test | Overflows; tells you less than κ (§6 → `sci-linear-algebra-differential-equations-and-optimization`) |
| Normal equations for least squares | ⚠️ **Squares the condition number. Use QR** (§6 → `sci-linear-algebra-differential-equations-and-optimization`) |
| Not using Cholesky on an SPD matrix | 2× the speed, free (§6 → `sci-linear-algebra-differential-equations-and-optimization`) |
| Unpreconditioned Krylov on an ill-conditioned system | Won't converge, and that's the default (§6 → `sci-linear-algebra-differential-equations-and-optimization`) |
| Python/MATLAB loop over array elements | ⚠️ **Two to three orders of magnitude** (§3 → `sci-floating-point-and-numerical-foundations`) |
| Vectorizing into an n×n intermediate for an O(n) result | Memory explosion (§3 → `sci-floating-point-and-numerical-foundations`) |
| Explicit ODE solver on a stiff system | ⚠️ **It will crawl. That's the diagnosis** (§7.1 → `sci-linear-algebra-differential-equations-and-optimization`) |
| RK45 for long Hamiltonian integrations | ⚠️ **Energy drift. Use a symplectic integrator** (§7.1 → `sci-linear-algebra-differential-equations-and-optimization`) |
| Default `rtol`/`atol` without thinking | Rarely right for your scaling (§7.1 → `sci-linear-algebra-differential-equations-and-optimization`) |
| Unscaled optimization variables | ⚠️ **The most common non-convergence cause** (§8 → `sci-linear-algebra-differential-equations-and-optimization`) |
| Finite-difference gradients when AD exists | Slower, less accurate, ill-conditioned (§5 → `sci-tooling-and-symbolic-computation`, §8 → `sci-linear-algebra-differential-equations-and-optimization`) |
| Reading only `x` and ignoring the solver exit flag | ⚠️ **"Max iterations" is not convergence** (§8 → `sci-linear-algebra-differential-equations-and-optimization`) |
| Assuming a local optimum is global | Only convex problems promise that (§8 → `sci-linear-algebra-differential-equations-and-optimization`) |
| Unregularized inverse problem | Fits noise beautifully (§8.4 → `sci-linear-algebra-differential-equations-and-optimization`) |
| Deterministic quadrature above ~4 dimensions | Curse of dimensionality; use QMC (§9 → `sci-linear-algebra-differential-equations-and-optimization`) |
| Comparing FFT results across libraries without checking normalization | The 1/N convention differs (§9 → `sci-linear-algebra-differential-equations-and-optimization`) |
| Point estimates with no uncertainty | Half an answer (§10 → `sci-statistics-performance-and-reproducibility`) |
| Per-thread seeding from the clock | ⚠️ **Correlated streams; use counter-based RNG** (§10 → `sci-statistics-performance-and-reproducibility`) |
| MCMC without checking R̂ and ESS | Confident nonsense (§10 → `sci-statistics-performance-and-reproducibility`) |
| Optimizing before profiling | You will guess wrong (§11 → `sci-statistics-performance-and-reproducibility`) |
| Micro-optimizing arithmetic in bandwidth-bound code | Roofline says it can't help (§11 → `sci-statistics-performance-and-reproducibility`) |
| Large numerical data in CSV | Slow, untyped, ⚠️ **lossy on floats** (§12 → `sci-statistics-performance-and-reproducibility`) |
| Writing floats to text at 6 digits | Silent data loss (§12 → `sci-statistics-performance-and-reproducibility`) |
| No units discipline | ⚠️ **Mars Climate Orbiter** (§12 → `sci-statistics-performance-and-reproducibility`) |
| "The plot looks reasonable" as verification | ⚠️ **Code produces numbers whether or not it's right** (§13 → `sci-statistics-performance-and-reproducibility`) |
| No convergence-order test | ⚠️ **The cheapest bug-finder you're not using** (§13 → `sci-statistics-performance-and-reproducibility`) |
| Never heard of manufactured solutions | The most powerful verification tool available (§13 → `sci-statistics-performance-and-reproducibility`) |
| Conflating verification and validation | Different questions; both needed (§13 → `sci-statistics-performance-and-reproducibility`) |
| `requirements.txt` with no pinned versions | ⚠️ **Not an environment** (§14 → `sci-statistics-performance-and-reproducibility`) |
| Seeds not recorded in the output | Untraceable results (§14 → `sci-statistics-performance-and-reproducibility`) |
| Claiming bitwise reproducibility across hardware | ⚠️ **Often impossible; state a tolerance** (§14 → `sci-statistics-performance-and-reproducibility`) |
| "Code available on request" | Empirically equivalent to unavailable (§14 → `sci-statistics-performance-and-reproducibility`) |
| Writing the algorithm instead of calling LAPACK | ⚠️ **Person-centuries of expertise you won't replicate** (§3 → `sci-floating-point-and-numerical-foundations`) |

---

## §16. Contested Questions

**16.1 Julia, Python, or MATLAB?** §4 → `sci-tooling-and-symbolic-computation`. **[CONTESTED and genuinely unsettled.]** Julia is
technically excellent and mature by download and package count, with real enterprise
backing — **and its adoption metrics remain modest, its compile latency and AOT story draw
persistent criticism, and one 2024 assessment argued its language-level limitations are
"severe enough to prevent widespread adoption."** Meanwhile **Python closed much of the
performance gap** through Numba, JAX, and the Array API. **The honest answer is
ecosystem-dependent, and §4.1 → `sci-tooling-and-symbolic-computation`'s first criterion usually decides it.**

**16.2 Is MATLAB worth the licence?** *For*: toolbox quality is genuinely unmatched in
control, DSP and Simulink-to-hardware, the documentation is excellent, and in regulated
industries the validation pedigree matters. *Against*: cost, lock-in, and
⚠️ **proprietary dependencies are a reproducibility liability** (§14 → `sci-statistics-performance-and-reproducibility`). **Strongest where a
specific toolbox has no free equivalent; weakest as general-purpose numerics.**

**16.3 Should scientists be trained as software engineers?** *For*: §13 → `sci-statistics-performance-and-reproducibility` and §14 → `sci-statistics-performance-and-reproducibility`'s failure
modes are engineering failures, and the crisis is measurable. *Against*: research code is
often exploratory and genuinely throwaway, and full engineering rigour on a script that
runs once is waste. **⚠️ The synthesis most Research Software Engineering groups land on:
tiered rigour — throwaway analysis gets version control and a pinned environment; anything
others will use gets tests, docs, and review.**

**16.4 Are notebooks good or bad for science?** *For*: exploration, narrative, teaching,
and reproducible figures. *Against*: ⚠️ **hidden execution-order state, poor diffing, and
they encourage code that can't be tested or reused.** **The workable compromise: notebooks
for exploration and presentation, importable modules for anything that matters, and
`nbstripout`/Jupytext in version control.**

**16.5 Is scientific ML overhyped?** §7.3 → `sci-linear-algebra-differential-equations-and-optimization`. *For*: real wins on surrogates, inverse
problems, and closure modelling. *Against*: ⚠️ **for well-posed forward problems, classical
solvers are usually faster, more accurate, and come with error bounds** — and the
comparisons in papers frequently omit a well-tuned conventional baseline. **Live.**

**16.6 Fortran — legacy or still right?** *For*: it remains extremely fast for dense array
work, modern Fortran is much improved, and rewriting validated legacy code is a genuine
risk. *Against*: hiring, tooling, ecosystem. **⚠️ "It's old" is not an argument; "nobody
here can maintain it" is.**

---

## §17. Currency Snapshot — verified August 2026

**[DURABLE] §1 → `sci-floating-point-and-numerical-foundations`, §2 → `sci-floating-point-and-numerical-foundations`, §3 → `sci-floating-point-and-numerical-foundations`, §6–§13 → `sci-linear-algebra-differential-equations-and-optimization`, `sci-statistics-performance-and-reproducibility` are numerical analysis and do not move. IEEE 754 is from
1985.** What follows is the tooling layer.

| Thing | Status as of Aug 2026 | Decay risk |
|---|---|---|
| **⚠️ Python Array API standard** | **The genuine structural change in the Python numerical stack.** A common specification across NumPy, CuPy, PyTorch, JAX, Dask. **NumPy 2.0 adopted it (NEP 47/56)** in the main namespace, `numpy.linalg` and `numpy.fft`. **Four years on from the first release (2021.12)**, adoption is broad. ⚠️ **The payoff: downstream libraries write array-agnostic code once and users get GPU execution with a minimal code change** — reported benchmarks include **up to ~52× speedups across scikit-learn and SciPy**, and a Ridge+MaxAbsScaler benchmark at **~50× (PyTorch) and ~49× (CuPy) vs NumPy** | Medium |
| **SciPy / scikit-learn** | Both adopting the standard progressively; scikit-learn uses `array_api_compat`. ⚠️ **Note a subtlety: the standard routes to `numpy.linalg` rather than `scipy.linalg`, which differ subtly** — scikit-learn dispatches conservatively for backward compatibility | Medium |
| **CuPy** | **v14 (Feb 2026)** — NumPy v2 semantics, bfloat16, CUDA pip wheels, broader NumPy/SciPy API coverage. **60M downloads, 10k GitHub stars** | Medium |
| **⚠️ Julia** | **100M+ downloads, 12,000+ registered packages.** **JuliaHub raised a $65M Series B in April 2026.** **TIOBE ~#32 at ~0.50% (April 2026)** — ⚠️ **but TIOBE measures search popularity and systematically undercounts specialized domains.** Persistent criticisms: **compile latency; weak first-class AOT compilation of small binaries** (PackageCompiler.jl/StaticCompiler.jl not considered first-class); a 2024 assessment argued limitations are **"severe enough to prevent widespread adoption"** for scientific ML | Medium |
| **MATLAB** | Retains the academic and industrial stronghold in control, DSP and Simulink workflows. ⚠️ **MathWorks has responded to Python's rise** — direct Python calling from MATLAB, and adoption of more aggressive broadcasting semantics | Low |
| **⚠️ Reproducibility** | **>70% of researchers report failing to reproduce another group's findings.** Life-sciences replication estimates: **10–25% reproducing robustly.** **Nature's 2026 reproducibility special issue: a multi-team effort found ~half of behavioural-science claims replicated.** Institutional response: artifact evaluation committees and reproducibility badges at major venues — ⚠️ **though research questions whether badges reliably reflect reproducibility quality** | Low |
| **Numerical reproducibility** | **Intel MKL offers conditional numerical reproducibility** by curtailing instruction-set extensions — ⚠️ **at a performance cost, and requiring consistent thread counts.** Underlying causes remain **out-of-order FP arithmetic in parallel reductions and non-associativity** | Low |
| **Regulatory** | ⚠️ **EU AI Act high-risk obligations phasing in through August 2026** touch scientific software in high-risk domains (medical devices, decision support): technical documentation, data governance, human oversight, traceability, post-market monitoring | Medium |

**Goes stale fastest:** the Array API adoption state and Julia's trajectory.
**Essentially never stale:** §1 → `sci-floating-point-and-numerical-foundations`, §2 → `sci-floating-point-and-numerical-foundations`, §6 → `sci-linear-algebra-differential-equations-and-optimization`, §7.1 → `sci-linear-algebra-differential-equations-and-optimization`'s stiffness framing, §13 → `sci-statistics-performance-and-reproducibility`, §15.

---

## §18. The Canon

### 18.1 Books

| Author | Work | Why |
|---|---|---|
| **Trefethen & Bau** | ***Numerical Linear Algebra*** | ⚠️ **The best-written numerical book there is.** Read it |
| **Golub & Van Loan** | *Matrix Computations* | The comprehensive reference |
| **Higham** | ***Accuracy and Stability of Numerical Algorithms*** | ⚠️ **The definitive work on §1 → `sci-floating-point-and-numerical-foundations` and §2 → `sci-floating-point-and-numerical-foundations`** |
| **Goldberg** | *"What Every Computer Scientist Should Know About Floating-Point Arithmetic"* | ⚠️ **Free paper. Read it once; it pays forever** |
| **Press et al.** | *Numerical Recipes* | ⚠️ **Excellent explanations, and the code has known quality and licensing issues — read it, don't copy it** |
| **Nocedal & Wright** | ***Numerical Optimization*** | §8 → `sci-linear-algebra-differential-equations-and-optimization`, definitively |
| **Boyd & Vandenberghe** | ***Convex Optimization*** | Free. The standard |
| **Hairer, Nørsett & Wanner** | *Solving ODEs I & II* | ⚠️ **Vol. II on stiff problems is the reference** |
| **LeVeque** | *Finite Difference/Finite Volume Methods* | Clear and practical |
| **Strang** | *Linear Algebra*; *Computational Science and Engineering* | The best intuition-builder |
| **Gelman et al.** | *Bayesian Data Analysis* | §10 → `sci-statistics-performance-and-reproducibility` |
| **Roache** | *Verification and Validation in Computational Science* | ⚠️ **§13 → `sci-statistics-performance-and-reproducibility`'s source, including MMS** |
| **Wilson et al.** | *"Good Enough Practices in Scientific Computing"* | ⚠️ **Free paper, and the most actionable thing in this list** |
| **The Turing Way** | (community handbook) | ⚠️ **Free, excellent, the practical reference for §14 → `sci-statistics-performance-and-reproducibility`** |

### 18.2 Documentation and tooling
**NumPy/SciPy docs** (⚠️ **SciPy's are unusually good on *which* algorithm and why**),
**LAPACK Users' Guide**, **the Array API standard** (data-apis.org), **SUNDIALS**,
**PETSc**, **SuiteSparse**, **FEniCS/Firedrake tutorials**, **JuliaHub and SciML docs**,
**Stan** and **PyMC**, **Software Carpentry** (⚠️ **the best entry point for scientists
becoming programmers**), **Zenodo** and **Software Heritage** for archiving.

### 18.3 People
**Nick Higham** (⚠️ **accuracy and stability; his blog and *What Is...* series are
outstanding**), **Nick Trefethen** (numerical analysis, Chebfun), **Gil Strang**,
**Tim Davis** (SuiteSparse), **Jack Dongarra** (BLAS/LAPACK, Turing Award),
**Cleve Moler** (⚠️ **created MATLAB; his writing on numerical computing is superb**),
**Chris Rackauckas** (SciML, DifferentialEquations.jl), **Steven Johnson** and
**Alan Edelman** (Julia, FFTW), **Andrew Gelman** (statistics, and unusually good on
what goes wrong), **Ralf Gommers** and **Aaron Meurer** (Array API, SciPy, SymPy),
**Greg Wilson** (Software Carpentry, and the practice literature).

---

## §19. Quick Reference

### 19.1 Numbers to hold
- **float64 eps ≈ 2.22e-16**; ~15–17 significant digits
- **float32 eps ≈ 1.19e-7**; ~6–9 digits
- **error ≈ κ(A) × eps** — ⚠️ **κ=10⁸ costs you half your digits**
- **Optimal finite-difference step ≈ √eps ≈ 1.5e-8** (for a well-scaled problem)
- **Cholesky ≈ ⅓n³; LU ≈ ⅔n³; QR ≈ 2mn²**
- **BLAS-3 is the only level that reaches peak FLOPS**
- ⚠️ **Above ~4 dimensions, quadrature loses to Monte Carlo**

### 19.2 When the numbers are wrong
1. **Check for NaN/inf** and where they first appear (⚠️ `np.seterr`, or a debugger trap)
2. **Check the condition number** (§2 → `sci-floating-point-and-numerical-foundations`)
3. **Check scaling** — are quantities O(1)? (§1.2 → `sci-floating-point-and-numerical-foundations`, §8 → `sci-linear-algebra-differential-equations-and-optimization`)
4. **Check the solver's exit status**, not just its output (§8 → `sci-linear-algebra-differential-equations-and-optimization`)
5. **Check units** (§12 → `sci-statistics-performance-and-reproducibility`)
6. **Run a convergence study** — does the error behave as theory says? (§13 → `sci-statistics-performance-and-reproducibility`)
7. **Check conservation** — is energy/mass conserved? (§13 → `sci-statistics-performance-and-reproducibility`)
8. **Compare against an analytical case or a manufactured solution** (§13 → `sci-statistics-performance-and-reproducibility`)
9. **Check tolerances** — are `rtol`/`atol` appropriate for your scale? (§7.1 → `sci-linear-algebra-differential-equations-and-optimization`)

### 19.3 Method picker
| Problem | Use |
|---|---|
| Solve Ax=b, general | LU (`solve`) — ⚠️ **never `inv`** |
| Solve Ax=b, symmetric positive definite | **Cholesky** |
| Least squares | **QR** — not normal equations |
| Rank / structure / ill-conditioned | **SVD** |
| Large sparse SPD | **CG + preconditioner** |
| Large sparse general | **GMRES/BiCGSTAB + preconditioner** |
| ODE, non-stiff | RK45 (`solve_ivp`, `ode45`) |
| ODE, stiff | **BDF / Radau** (`ode15s`, CVODE) |
| Hamiltonian, long integration | **Symplectic integrator** |
| PDE, conservation laws | **Finite volume** |
| PDE, complex geometry | **Finite element** (FEniCS/deal.II) |
| Smooth 1-D integral | Gauss–Legendre / `quad` |
| High-dimensional integral | **Monte Carlo / Sobol QMC** |
| Gradients of a program | ⚠️ **Automatic differentiation** (§5 → `sci-tooling-and-symbolic-computation`) |
| Convex optimization | **CVXPY / JuMP** + a conic solver |
| Constrained nonlinear | **IPOPT / SQP** |
| Parameter uncertainty | Bootstrap, or MCMC (§10 → `sci-statistics-performance-and-reproducibility`) |
| Deriving equations | ⚠️ **Symbolic, then generate code** (§5 → `sci-tooling-and-symbolic-computation`) |

---

## §20. Sources and Method

**Method.** Narrative review, written as practice guidance for engineers doing numerical
work. **The overwhelming majority of this document — §1 → `sci-floating-point-and-numerical-foundations`, §2 → `sci-floating-point-and-numerical-foundations`, §3 → `sci-floating-point-and-numerical-foundations`, §5–§13 → `sci-tooling-and-symbolic-computation`, `sci-linear-algebra-differential-equations-and-optimization`, `sci-statistics-performance-and-reproducibility`, §15 — is
numerical analysis and long-settled engineering practice**, resting on the standard
literature (Higham, Trefethen & Bau, Golub & Van Loan, Nocedal & Wright, Hairer et al.,
Roache) rather than on anything searched. **IEEE 754 is from 1985 and the algorithms are
mostly older than that**; §17 says so explicitly rather than manufacturing currency.
Three targeted searches were run in **August 2026** on the parts that genuinely move:
the language landscape, the Python array ecosystem, and the state of reproducibility
practice.

**Search log** (August 2026): Julia adoption, the two-language problem, and the MATLAB
comparison · NumPy 2 / SciPy / Array API standard and GPU interoperability · scientific
software reproducibility, verification and validation.

**Primary and near-primary sources consulted (selected):**
- **NumPy Enhancement Proposals** (NEP 47, NEP 56, and the roadmap) and the **Array API
  standard** documentation for the interoperability story; **Quansight Labs' and
  Quansight's engineering blogs** for the adoption state and benchmark figures;
  **CuPy's v14 release announcement**; scikit-learn's Array API documentation for the
  `numpy.linalg`/`scipy.linalg` dispatch subtlety
- **arXiv 2410.10908**, *"The State of Julia for Scientific Machine Learning"*, for the
  critical assessment — ⚠️ **I've quoted its conclusion because the enthusiastic case is
  much easier to find than the sceptical one**; TIOBE/JuliaHub figures via 2026 ecosystem
  write-ups; Hacker News practitioner discussion for the AOT-compilation critique
- **Reproducibility**: arXiv 2512.00651 for the >70% figure and the artifact-badge
  research; a 2026 review post citing **Nature's 2026 reproducibility special issue** and
  the Begley & Ellis / Ioannidis replication estimates; a **Frontiers (2025)** paper on
  scientific software in the AI era for the EU AI Act timing; ScienceDirect's
  reproducibility overview for the MKL conditional-reproducibility mechanism

**Confidence statement.** **Very high confidence** in §1 → `sci-floating-point-and-numerical-foundations`, §2 → `sci-floating-point-and-numerical-foundations`, §3 → `sci-floating-point-and-numerical-foundations`, §5–§13 → `sci-tooling-and-symbolic-computation`, `sci-linear-algebra-differential-equations-and-optimization`, `sci-statistics-performance-and-reproducibility` and §15 — this is
settled numerical analysis, consistently presented across the standard texts for decades,
and my confidence rests on that literature rather than on web sources. **High confidence in
the Array API material** (§17), which comes from NumPy's own NEPs and the implementing
teams' engineering blogs — ⚠️ **though the specific speedup multipliers (52×, 50×, 49×) are
benchmark-and-hardware-specific figures published by parties invested in the standard's
success, and should be read as "GPU dispatch can be transformative for the right workload"
rather than as a general expectation.**

⚠️ **Moderate confidence, and deliberately hedged, on §4.2 → `sci-tooling-and-symbolic-computation` and §16.1's Julia assessment.**
This is a domain with strong partisans on both sides; I have quoted a peer-reviewed
critical assessment alongside the adoption figures **specifically because the promotional
case is far easier to find**, and the download/package/TIOBE numbers come from ecosystem
write-ups rather than audited sources. **The reproducibility figures in §14 → `sci-statistics-performance-and-reproducibility` and §17 vary
substantially between studies and disciplines** — the 10–25% and ~50% estimates measure
different things in different fields and should not be combined or treated as a single
number; I have attributed each rather than averaging them. §16 is opinion labelled as such.
