---
name: sci-floating-point-and-numerical-foundations
description: "Use when a numerical result is wrong, surprising, or not reproducible: IEEE 754 floating point and what you are actually computing with, catastrophic cancellation, NaN and signed zero, comparison and summation practices, conditioning and numerical stability and the difference between them, and the BLAS/LAPACK substrate that everything else stands on. Includes the router for the whole math-science-programming reference."
---

# Math and Science Programming: Floating Point, Conditioning and Stability, and the BLAS/LAPACK Substrate

> **Part 1 of 5** of the *Math and Science Programming* reference (plugin `math-science-programming`), covering §0–§3. Sibling skills: `sci-tooling-and-symbolic-computation` (§4–§5), `sci-linear-algebra-differential-equations-and-optimization` (§6–§9), `sci-statistics-performance-and-reproducibility` (§10–§14), `sci-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    the rationals that doesn't obey associativity or distributivity (§1). **Most numerical
>    bugs are a failure to internalize that**, and the rest are conditioning problems (§2).
> 3. **⚠️ Do not write the algorithm.** LAPACK, SUNDIALS, and the rest represent
>    person-centuries of numerical expertise that you will not replicate. **Your job is to
>    choose the right routine, feed it a well-conditioned problem, and check the
>    answer** — see §3 and the anti-pattern table.

---

## §0. Routing

| Asked about... | Go to |
|---|---|
| **Floating point and why the answer is wrong** | **§1** |
| Conditioning, stability, error analysis | §2 |
| The numerical substrate (BLAS/LAPACK) | §3 |
| **Choosing a language/tool** | **§4 → `sci-tooling-and-symbolic-computation`** |
| Symbolic computation | §5 → `sci-tooling-and-symbolic-computation` |
| Linear systems and eigenproblems | §6 → `sci-linear-algebra-differential-equations-and-optimization` |
| ODEs, PDEs, and simulation | §7 → `sci-linear-algebra-differential-equations-and-optimization` |
| Optimization | §8 → `sci-linear-algebra-differential-equations-and-optimization` |
| Interpolation, quadrature, transforms | §9 → `sci-linear-algebra-differential-equations-and-optimization` |
| Statistics, uncertainty, Monte Carlo | §10 → `sci-statistics-performance-and-reproducibility` |
| Performance, parallelism, GPU | §11 → `sci-statistics-performance-and-reproducibility` |
| Data, I/O, and units | §12 → `sci-statistics-performance-and-reproducibility` |
| **Testing and verification** | **§13 → `sci-statistics-performance-and-reproducibility`** |
| **Reproducibility** | **§14 → `sci-statistics-performance-and-reproducibility`** |
| "Don't do this" | §15 → `sci-reference` |
| "Which side is right?" | §16 → `sci-reference` |
| "Is this still current?" | §17 → `sci-reference` |
| Books and people | §18 → `sci-reference` |

---

## §1. Floating Point

**[DURABLE] IEEE 754 dates from 1985, is implemented everywhere, and has not changed.
Everything in this section is permanent.**

### 1.1 What you're actually computing with

**`float64`**: 1 sign bit, 11 exponent, 52 mantissa. **~15–17 significant decimal digits**,
range ~10^±308. **`float32`**: ~6–9 digits, ~10^±38. **`float16`/`bfloat16`** trade
precision for memory and speed — ⚠️ **`bfloat16` keeps float32's exponent range and throws
away mantissa**, which is why ML uses it and numerical analysis mostly doesn't.

**Machine epsilon (float64): ~2.22e-16.** ⚠️ **The single most useful number in this
document** — it's the gap between 1.0 and the next representable number, and it bounds
your relative error per operation.

> **⚠️ GOTCHA — the consequences, all of which produce silent wrong answers:**
> - **`0.1 + 0.2 != 0.3`.** Decimal fractions mostly aren't representable in binary.
>   ⚠️ **Never compare floats with `==`** — compare against a tolerance, and think about
>   whether it should be absolute or relative.
> - **⚠️ Addition is not associative.** `(a+b)+c != a+(b+c)`. **This is why parallel
>   reductions give different answers on different thread counts** (§11 → `sci-statistics-performance-and-reproducibility`, §14 → `sci-statistics-performance-and-reproducibility`), and it is
>   the single most common source of "why doesn't my result reproduce."
> - **Catastrophic cancellation.** Subtracting nearly-equal numbers annihilates
>   significant digits. ⚠️ **The classic: the quadratic formula loses all precision for one
>   root when `b² >> 4ac`** — use the numerically stable variant.
> - **Absorption.** Adding a tiny number to a huge one changes nothing. ⚠️ **Summing a
>   large array naively accumulates error proportional to n** — use **Kahan/Neumaier
>   compensated summation** or pairwise summation (⚠️ **NumPy's `sum` already does
>   pairwise; a hand-rolled loop does not**).
> - **Special values.** `NaN != NaN` (⚠️ **which is how `NaN` sneaks past your validity
>   checks**), `inf - inf = NaN`, and **signed zero** matters at branch cuts.
> - **Subnormals** near zero lose precision gradually, ⚠️ **and can be dramatically slow on
>   some hardware** — flush-to-zero is a real performance flag.
> - **`x87` 80-bit intermediates, FMA contraction, and `-ffast-math`** all change results.
>   ⚠️ **`-ffast-math` assumes no NaN/inf and permits reassociation — it can silently break
>   correct code.**

### 1.2 The practices
**Scale and non-dimensionalize** your problem so quantities are O(1) — ⚠️ **this single
habit prevents a large fraction of overflow, underflow, and conditioning problems.**
**Prefer `log` space** for products of probabilities (`logsumexp`). **Reformulate to avoid
cancellation** (`log1p`, `expm1`, `hypot` exist precisely for this). **Use the library
function** — ⚠️ **`np.hypot(x,y)` is not `sqrt(x*x+y*y)`; it avoids intermediate overflow.**
And **when you genuinely need exactness — money, combinatorics — use integers, decimals, or
rationals**, not floats.

---

## §2. Conditioning and Stability

**[DURABLE] The two concepts that let you reason about numerical error, and they're
distinct in a way people constantly conflate:**

- **Conditioning is a property of the *problem*.** How much does the output change when
  the input is perturbed? **An ill-conditioned problem amplifies error no matter how good
  your algorithm is.**
- **Stability is a property of the *algorithm*.** Does it introduce error beyond what the
  conditioning demands? **A backward-stable algorithm gives the exact answer to a slightly
  perturbed problem.**

**⚠️ The practical consequence: `error ≈ condition_number × machine_epsilon`.** For a
linear system with **κ(A) = 10^8** in float64, expect to lose about 8 of your ~16 digits.
**⚠️ κ(A) near 10^16 means you have no significant digits left, and the solver will not
warn you.** **Check the condition number.** `np.linalg.cond`, or `rcond` from the solver.

**Classic ill-conditioned traps**: **Hilbert matrices**, **Vandermonde matrices**
(⚠️ **which is why fitting a high-degree polynomial through `polyfit` on raw x-values is a
trap** — use orthogonal polynomials or scale the domain), **numerical differentiation**
(⚠️ **inherently ill-conditioned — halving h halves truncation error and doubles rounding
error; there's an optimal h around √ε and you cannot beat it**), **root-finding near
multiple roots**, and **deconvolution and inverse problems generally** (§8.4 → `sci-linear-algebra-differential-equations-and-optimization`).

**[DURABLE] The distinction that saves the most time**: **truncation error** comes from
your method (a finite difference, a truncated series) and shrinks as you refine;
**rounding error** comes from floating point and *grows* as you refine. ⚠️ **Total error
has a minimum. Refining past it makes your answer worse**, and watching an error curve
turn back upward is the standard diagnostic.

---

## §3. The Substrate: BLAS and LAPACK

**[DURABLE] Almost everything numerical you will ever run bottoms out here, and knowing
that changes how you write code.**

**BLAS levels**: **Level 1** vector-vector, O(n) work on O(n) data — memory-bound.
**Level 2** matrix-vector, O(n²) on O(n²) — still memory-bound. **Level 3** matrix-matrix,
**O(n³) work on O(n²) data** — ⚠️ **compute-bound, cache-blockable, and the only level that
gets near peak FLOPS.** **This is why algorithms are reformulated in terms of matrix
products wherever possible.**

**LAPACK** builds the actual decompositions on top: LU, QR, Cholesky, SVD, eigenvalue
solvers. **Implementations**: **OpenBLAS**, **Intel MKL**, **AMD AOCL/BLIS**, **Apple
Accelerate**, and the **reference BLAS** (⚠️ **correct and slow — never use it for real
work**). **NumPy, MATLAB, R, and Julia are all calling these**, which is why
"MATLAB vs NumPy speed" comparisons on linear algebra usually measure which BLAS was
linked.

> **⚠️ GOTCHA — the vectorization principle.** In any interpreted array language,
> **the loop is the problem, not the language.** A Python loop over array elements runs at
> interpreter speed; the same operation expressed as an array operation runs at BLAS
> speed. **Two-to-three orders of magnitude, routinely.**
>
> ⚠️ **And the counter-caution: vectorizing can explode memory.** A broadcast that
> materializes an n×n intermediate for an O(n) result is a common and expensive mistake.
> Chunk it, or use an expression-fusing tool (`numexpr`, Numba, JAX).
