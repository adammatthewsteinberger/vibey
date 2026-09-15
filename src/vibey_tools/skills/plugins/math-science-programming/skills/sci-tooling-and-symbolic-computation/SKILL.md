---
name: sci-tooling-and-symbolic-computation
description: "Use when choosing a language or tool for numerical work, or reaching for a computer algebra system: MATLAB, Python's scientific stack (NumPy, SciPy, JAX), Julia, R, Fortran and Mathematica, the criteria that actually decide it, the two-language problem assessed honestly, and symbolic computation with SymPy, Mathematica and Maxima — including when symbolic beats numeric and when it does not."
---

# Math and Science Programming: Choosing a Tool, and Symbolic Computation

> **Part 2 of 5** of the *Math and Science Programming* reference (plugin `math-science-programming`), covering §4–§5. Sibling skills: `sci-floating-point-and-numerical-foundations` (§0–§3), `sci-linear-algebra-differential-equations-and-optimization` (§6–§9), `sci-statistics-performance-and-reproducibility` (§10–§14), `sci-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 → `sci-reference` for the currency snapshot and what goes stale first.

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

## §4. Choosing a Tool

**[VERSIONED for the ecosystem details, DURABLE for the criteria.]**

| Tool | Genuine strengths | ⚠️ Genuine weaknesses |
|---|---|---|
| **MATLAB** | ⚠️ **Superb toolboxes** (Simulink, control, signal processing), excellent docs, industry-standard in control/aero/DSP, Simulink code generation to embedded targets is a real moat | **Cost and licence management**; proprietary; awkward at general programming; deployment is painful |
| **Python (NumPy/SciPy)** | ⚠️ **The default, and the widest ecosystem by far.** Free, general-purpose, and the glue between science and everything else | Loops are slow (§3 → `sci-floating-point-and-numerical-foundations`); packaging has historically been painful; **two-language problem for hot paths** |
| **Julia** | ⚠️ **Genuinely fast without leaving the language**; multiple dispatch is a superb fit for numerical code; excellent for ODEs/SciML | **Smaller ecosystem**; ⚠️ **compile latency ("time to first plot")** and weak AOT/binary story (§4.2) |
| **R** | ⚠️ **Statistics, unmatched.** CRAN, tidyverse, and the best statistical modelling libraries in existence | Awkward outside statistics; performance |
| **Fortran** | ⚠️ **Still the fastest thing for dense array numerics**, and it's what much of LAPACK and legacy HPC actually is. Modern Fortran (2008/2018) is far better than its reputation | Ecosystem, tooling, hiring |
| **C/C++** | Control, performance, Eigen/Armadillo/Blaze, and where libraries get written | Development speed; you own every mistake |
| **Mathematica / Maple** | ⚠️ **Symbolic computation, unmatched** (§5). Excellent for derivation | Cost; proprietary; less good as general numerics |
| **Octave / Scilab** | Free, largely MATLAB-compatible | Slower; toolbox gaps |
| **Rust** | Memory safety, growing numerical ecosystem | Ecosystem immaturity for science |

### 4.1 [DURABLE] The criteria that actually decide it
1. **⚠️ What does your field use?** Being the only Julia user in a MATLAB lab is a real
   cost — code review, collaboration, and inheriting others' work all get harder.
   **This is usually decisive and rarely stated.**
2. **Does the library you need exist?** ⚠️ **A specialist toolbox can outweigh every
   language-level consideration.** MATLAB's Simulink-to-hardware path, R's statistical
   models, and Julia's DifferentialEquations.jl are each near-unique.
3. **Who maintains it in five years?**
4. **Deployment**: does this ship, or run once for a paper?
5. **Licensing**, especially for reproducibility (⚠️ **a proprietary dependency is a
   reproducibility liability** — §14 → `sci-statistics-performance-and-reproducibility`).

### 4.2 ⚠️ The two-language problem, honestly

**[CONTESTED]** Julia was explicitly designed to solve it: **you prototype in a high-level
language, then rewrite the hot path in C or Fortran, and now you maintain two
implementations that can diverge.**

**Julia's case in 2026**: mature by any reasonable measure — **100M+ downloads, 12,000+
registered packages**, and **JuliaHub raised a $65M Series B in April 2026**, which is
meaningful enterprise signal. ⚠️ **But it sits around #32 on TIOBE at ~0.5%**, and the
honest reading of that is contested: TIOBE measures search-result popularity and
**systematically undercounts specialized domains**, but the number is still not large.

**⚠️ The critique deserves airing too.** A 2024 assessment of Julia for scientific machine
learning argued that while the ecosystem provides genuinely useful abstractions,
**"the limitations are severe enough to prevent it from widespread adoption,"** and called
on the community to address language-level issues. **The recurring practical complaints**:
compile latency, and **weak first-class support for ahead-of-time compilation of small
binaries and libraries** — which some practitioners characterize as Julia having traded
the two-language problem for a **"1.5 language problem."**

**⚠️ And note the counter-move**: Python has substantially eroded the premise. **Numba,
Cython, JAX, PyTorch, and now the Array API standard (§17 → `sci-reference`)** mean much high-level Python
numerical code reaches compiled speed without a rewrite. **MathWorks responded too** —
MATLAB can call Python directly and has adopted Python-like broadcasting semantics.

**[DURABLE] The defensible position: pick for ecosystem and colleagues first, performance
second — because the performance gap is now closable in every one of these languages, and
the ecosystem gap is not.**

---

## §5. Symbolic Computation

**[DURABLE] A genuinely different mode: exact manipulation of expressions, not
approximation of numbers.**

**Tools**: **Mathematica** (⚠️ **the most capable, and it's not close for hard integration
and simplification**), **Maple**, **SymPy** (Python, free, ⚠️ **capable but notably slower
and weaker at hard simplification**), **SymEngine** (fast C++ core), **Maxima**, **SageMath**
(an integrating layer over many systems), and **Symbolics.jl**.

**What it's genuinely good for**: **deriving equations of motion, Jacobians, and gradients**
(⚠️ **and then generating code from them — the single most valuable pattern here**),
symbolic integration and differentiation, exact linear algebra over small matrices, series
expansions, and **checking your hand derivation.**

> **⚠️ GOTCHA — the failure modes.** **Expression swell**: intermediate expressions grow
> exponentially and a "simple" symbolic solve consumes all memory. **Simplification is
> undecidable in general**, so `simplify()` is heuristic and may not find the form you
> want. **Most equations have no closed-form solution** — symbolic tools will tell you so,
> eventually, after a long time. **And branch cuts and assumptions** (is `x` real?
> positive?) silently change answers. **⚠️ Declare your assumptions explicitly.**

**[DURABLE] The three-way distinction worth holding**: **symbolic** (exact, slow, may not
terminate), **automatic differentiation** (⚠️ **exact derivatives of a *program*, at
numerical speed — this is what changed scientific computing, and it is neither symbolic
nor finite-difference**), and **numerical differentiation** (approximate,
ill-conditioned — §2 → `sci-floating-point-and-numerical-foundations`). **For gradients of code, AD is almost always the right answer**:
JAX, PyTorch, Enzyme, ForwardDiff.jl, or Zygote.jl.
