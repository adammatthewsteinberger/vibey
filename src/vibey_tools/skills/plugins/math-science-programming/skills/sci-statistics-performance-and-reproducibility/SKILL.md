---
name: sci-statistics-performance-and-reproducibility
description: "Use when quantifying uncertainty, making numerical code fast, or making it trustworthy: statistics and uncertainty quantification, performance and parallelism (vectorization, threading, MPI, GPU computing), data, I/O and units, testing and verification (the method of manufactured solutions, convergence tests, property-based testing), and reproducibility — environments, seeds, and provenance."
---

# Math and Science Programming: Statistics, Performance, Testing, and Reproducibility

> **Part 4 of 5** of the *Math and Science Programming* reference (plugin `math-science-programming`), covering §10–§14. Sibling skills: `sci-floating-point-and-numerical-foundations` (§0–§3), `sci-tooling-and-symbolic-computation` (§4–§5), `sci-linear-algebra-differential-equations-and-optimization` (§6–§9), `sci-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    numerical code that breaks returns a `float`. **Every practice in §13 and §14 exists
>    because of this one asymmetry.**
> 2. **You are not computing with real numbers.** You're computing with a finite subset of
>    the rationals that doesn't obey associativity or distributivity (§1 → `sci-floating-point-and-numerical-foundations`). **Most numerical
>    bugs are a failure to internalize that**, and the rest are conditioning problems (§2 → `sci-floating-point-and-numerical-foundations`).
> 3. **⚠️ Do not write the algorithm.** LAPACK, SUNDIALS, and the rest represent
>    person-centuries of numerical expertise that you will not replicate. **Your job is to
>    choose the right routine, feed it a well-conditioned problem, and check the
>    answer** — see §3 → `sci-floating-point-and-numerical-foundations` and the anti-pattern table.

---

## §10. Statistics and Uncertainty

**[DURABLE] The section engineers most often skip and most often need.**

**Fitting**: ⚠️ **least squares assumes Gaussian errors** — if yours aren't, use the right
likelihood. **Weighted least squares** when uncertainties differ. **Robust regression**
(Huber, RANSAC) when outliers exist. ⚠️ **Report parameter uncertainties, not just point
estimates** — the covariance matrix from the fit is the minimum.

**Uncertainty quantification**: **propagation of uncertainty** (linear, via the Jacobian),
**Monte Carlo propagation** (⚠️ **more honest for nonlinear models**), **bootstrap** for
distribution-free confidence intervals, and **sensitivity analysis** (Sobol indices) to
find which input actually drives your output.

**Bayesian inference**: **MCMC** (⚠️ **NUTS/HMC in Stan, PyMC, NumPyro, Turing.jl — and
check R̂ and effective sample size, because an unconverged chain produces confident
nonsense**), **variational inference** for speed, **nested sampling** for evidence.

**Random numbers**: ⚠️ **Use a modern generator (PCG64, Philox) via a proper API — never
`rand()` from C's standard library for anything scientific.** **Seed explicitly and record
the seed** (§14). ⚠️ **For parallel work, use counter-based generators or explicitly split
streams — naively seeding per-thread from the clock produces correlated streams**, which is
a genuinely nasty and hard-to-detect bug.

---

## §11. Performance and Parallelism

**[DURABLE] The order of operations, and doing it in a different order wastes weeks:**
```
1. Make it correct                        (§13)
2. Profile — find where the time is       ⚠️ never guess
3. Better algorithm / better library      ← the biggest wins live here
4. Vectorize; use Level-3 BLAS shapes     (§3)
5. Memory layout and cache behaviour
6. Parallelize on one node (threads)
7. GPU, if the problem suits it
8. Distributed (MPI), if it must
```

**⚠️ Most numerical code is memory-bandwidth-bound, not compute-bound.** The **roofline
model** is the right mental tool: plot arithmetic intensity (FLOPs per byte moved) against
achievable performance and you can see immediately whether you're near the bandwidth
ceiling or the compute ceiling. **BLAS Level 1 and 2 operations, and most stencil codes,
are bandwidth-bound** — which means micro-optimizing the arithmetic achieves nothing.

**The parallel toolkit**: **OpenMP** (shared memory, incremental), **MPI** (⚠️ **still the
backbone of HPC, and not going anywhere**), **CUDA/HIP/SYCL** for GPUs, **Kokkos** and
**RAJA** for performance portability, **Dask**/**Ray** for Python-level distribution, and
**Numba**/**JAX**/**Cython** for compiling Python hot paths.

> **⚠️ GOTCHA — parallel numerics has its own failure modes:**
> - **⚠️ Non-associativity means results change with thread count** (§1.1 → `sci-floating-point-and-numerical-foundations`). **This is not a
>   bug, and it will look like one.** If you need bit-reproducibility, you need
>   deterministic reduction orders — Intel MKL offers "conditional numerical
>   reproducibility" by fixing instruction sets and requiring consistent thread counts,
>   ⚠️ **at a performance cost**.
> - **False sharing** — threads writing adjacent memory ping-pong cache lines.
> - **Load imbalance** — the slowest rank sets your runtime.
> - **Communication cost** — ⚠️ **an all-reduce at every timestep will dominate**; overlap
>   communication with computation.
> - **Amdahl's law** — the serial fraction bounds everything.
> - **⚠️ Silent data corruption** at scale is real in large HPC runs, and it's why
>   checkpointing and consistency checks matter.

---

## §12. Data, I/O, and Units

**Formats**: **HDF5** (⚠️ **the scientific standard — hierarchical, chunked, compressed,
parallel-capable**), **NetCDF** (climate and geoscience, built on HDF5), **Zarr**
(⚠️ **cloud-native chunked arrays — increasingly the default for large distributed data**),
**Parquet** for tabular, **FITS** in astronomy. ⚠️ **CSV for anything large is a mistake**
— slow, untyped, and lossy on floats unless you're careful with precision.

⚠️ **Float round-tripping**: use `repr`/`%.17g` or a binary format. **Writing floats to
text at 6 digits and reading them back is silent data loss**, and it happens constantly.

**[DURABLE] Units and dimensional analysis.** ⚠️ **The Mars Climate Orbiter was lost to a
pound-force-seconds versus newton-seconds mismatch.** Use a units library — **Pint**
(Python), **Unitful.jl**, **boost::units** — or at absolute minimum **encode units in
variable names and check dimensional consistency in your tests** (§13). **Non-
dimensionalize your equations** where you can; it improves conditioning too (§1.2 → `sci-floating-point-and-numerical-foundations`).

---

## §13. Testing and Verification

**[DURABLE] The most under-practised discipline in scientific software, and the direct
answer to this document's opening framing.**

**⚠️ The vocabulary matters and is worth getting right:**
- **Verification: are we solving the equations right?** (A software question.)
- **Validation: are we solving the right equations?** (A science question — compare against
  experiment.)
- **⚠️ Both are needed, and passing one tells you nothing about the other.**

**The techniques that actually work:**
- **Analytical solutions.** Test against problems with known closed-form answers.
- **⚠️ The Method of Manufactured Solutions (MMS)** — **the most powerful verification tool
  in scientific computing and the least used.** Pick an arbitrary solution, substitute it
  into your PDE to derive the source term that makes it true, then check your solver
  recovers it. **It works for problems with no natural analytical solution.**
- **⚠️ Convergence-order testing.** A second-order method must show error dropping 4× when
  you halve h. **If your observed order doesn't match the theoretical order, you have a
  bug** — and this catches an enormous class of subtle errors that eyeballing a plot will
  not.
- **Conservation checks** — mass, energy, momentum, probability summing to 1. **Cheap,
  and they catch real bugs.**
- **Symmetry and invariance tests** — translate, rotate, or rescale the problem and the
  answer should transform correspondingly.
- **Property-based testing** — Hypothesis, and metamorphic relations generally.
- **Comparison against an independent implementation.**
- **Regression tests with tolerances** — ⚠️ **and pin the tolerance thoughtfully, because
  `assert_allclose` with default tolerances either passes everything or fails on noise.**
- **Test the edge cases**: zero, negative, NaN, inf, empty arrays, singular matrices,
  and the degenerate geometry.

**⚠️ And the mindset**: your code produces numbers whether or not it is correct.
**"It ran and the plot looks reasonable" is not evidence.**

---

## §14. Reproducibility

**[VERSIONED in the specifics, DURABLE in the practice.]**

**⚠️ The context is a genuine, measured crisis.** Surveys indicate **over 70% of
researchers have failed to reproduce another group's findings**; large-scale replication
efforts in life sciences report **only 10–25% of studies or effects reproducing robustly**;
and Nature's 2026 reproducibility special issue reported a multi-team meta-research effort
finding **only about half of published behavioural-science claims could be replicated.**
⚠️ **Computational reproducibility — same data, same code, same answer — is the easiest
kind, and it still frequently fails.**

**[DURABLE] What actually to do, roughly in order of payoff:**
1. **Version control everything**, code and analysis scripts alike. Non-negotiable.
2. **⚠️ Pin your environment exactly** — `conda-lock`, `uv.lock`, `renv`, Julia's
   `Manifest.toml`, or a container. **"requirements.txt with no versions" is not an
   environment.** Version drift is the single most common reproduction failure.
3. **Containerize** for anything you want reproducible in five years — Docker, Apptainer/
   Singularity (⚠️ **the HPC-friendly one**).
4. **⚠️ Record random seeds**, and record them *in the output*, not only in the script.
5. **Record the full provenance**: code version, data version, parameters, environment,
   hardware. ⚠️ **Ideally emit it into the result file itself**, so an orphaned output can
   still be traced.
6. **Separate code from data from results**; make the pipeline re-runnable end to end
   (Snakemake, Nextflow, Make).
7. **Archive with a DOI** — Zenodo, Software Heritage. **A GitHub URL is not an archive.**
8. **Publish the code.** ⚠️ **"Available on request" is empirically equivalent to
   unavailable.**

**⚠️ The numerical caveat specific to this domain**: **bitwise reproducibility across
different hardware, thread counts, BLAS implementations, or compiler flags is often
impossible** (§1.1 → `sci-floating-point-and-numerical-foundations`, §11). **The honest target is reproducibility to a stated tolerance,
with the tolerance justified** — not bit-identity. ⚠️ **Say which you're claiming.**
