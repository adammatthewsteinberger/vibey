---
name: sci-linear-algebra-differential-equations-and-optimization
description: "Use when solving the actual mathematical problem: linear systems, factorizations, least squares, eigenvalues and sparse solvers; ODEs including stiffness, solver choice and adaptive stepping; PDEs by finite difference, finite element and finite volume, and scientific machine learning; optimization (convex, gradient-based, derivative-free, constrained); and interpolation, quadrature and transforms."
---

# Math and Science Programming: Linear Algebra, Differential Equations, Optimization, and Quadrature

> **Part 3 of 5** of the *Math and Science Programming* reference (plugin `math-science-programming`), covering §6–§9. Sibling skills: `sci-floating-point-and-numerical-foundations` (§0–§3), `sci-tooling-and-symbolic-computation` (§4–§5), `sci-statistics-performance-and-reproducibility` (§10–§14), `sci-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §6. Linear Algebra

**[DURABLE] The most important practical rule in this entire document:**

> **⚠️ GOTCHA — never invert a matrix to solve a linear system.**
> `x = inv(A) @ b` is slower, less accurate, and less numerically stable than
> `x = solve(A, b)`. **The explicit inverse is almost never what you want** — if you find
> yourself computing one, you are probably solving a system, and there is a factorization
> for it. **Same for `det(A)` as a singularity test: it overflows, underflows, and tells
> you less than the condition number does.**

**Pick the factorization to match the matrix**:

| Structure | Use | Cost |
|---|---|---|
| **General square** | **LU with partial pivoting** | ~⅔n³ |
| **Symmetric positive definite** | ⚠️ **Cholesky — 2× faster and more stable. Use it whenever it applies** | ~⅓n³ |
| **Least squares / overdetermined** | ⚠️ **QR, not the normal equations** — forming AᵀA **squares the condition number** | ~2mn² |
| **Rank-deficient, ill-conditioned, or you need structure** | **SVD** — ⚠️ **the most informative and most expensive** | ~O(mn²) |
| **Symmetric eigenproblem** | Symmetric QR / divide-and-conquer | |
| **Large sparse** | **Iterative: CG (SPD), GMRES/BiCGSTAB (general), LSQR** | Depends |

**⚠️ Sparse is a different discipline.** Store in CSR/CSC/COO; ⚠️ **fill-in during
factorization is the central problem**, mitigated by reordering (AMD, METIS). **Iterative
methods live or die by preconditioning** — ⚠️ **an unpreconditioned Krylov solver on a
poorly-conditioned system will converge slowly or not at all, and "not converging" is the
default state.** Jacobi, ILU, algebraic multigrid, domain decomposition.

**Libraries**: **SuiteSparse** (⚠️ **Tim Davis's work — UMFPACK, CHOLMOD; the standard**),
**PETSc** and **Trilinos** for large-scale parallel, **Eigen** (C++ header-only),
**ARPACK** for large eigenproblems, **cuSOLVER/cuSPARSE** on GPU.

---

## §7. Differential Equations and Simulation

### 7.1 ODEs

**[DURABLE] The single most important question: is your system stiff?**

**⚠️ Stiffness means widely-separated time scales** — a fast transient alongside slow
dynamics. **The tell: an explicit solver takes absurdly tiny steps and crawls**, not
because accuracy demands it but because stability does. **Chemical kinetics, circuit
simulation, and reaction-diffusion are routinely stiff.**

| | **Non-stiff** | **Stiff** |
|---|---|---|
| Methods | Explicit RK (Dormand–Prince RK45), Adams–Bashforth | ⚠️ **Implicit: BDF, Radau, Rosenbrock** |
| Cost per step | Cheap | Expensive — solves a nonlinear system, needs a Jacobian |
| **Use when** | Smooth, comparable time scales | ⚠️ **Explicit is crawling** |

**⚠️ Structure-preserving integrators matter more than accuracy order for long runs**:
**symplectic integrators for Hamiltonian systems** (⚠️ **they conserve energy over
astronomically long integrations where a "more accurate" RK method drifts**), and
**geometric integrators generally.** **If you're doing orbital mechanics or molecular
dynamics and using RK45, that's likely the bug.**

**Also**: **adaptive stepping with error control** (⚠️ **set `rtol` and `atol` deliberately
— the defaults are rarely right for your scaling**), **event detection** for
discontinuities, **DAEs** (index matters), and **sensitivity analysis / adjoints** for
gradients through a solve.

**Libraries**: **SUNDIALS** (CVODE/IDA/ARKODE — ⚠️ **the reference implementation, wrapped
by nearly everything**), **`scipy.integrate.solve_ivp`**, **DifferentialEquations.jl**
(⚠️ **the most comprehensive ODE ecosystem anywhere, and a genuine reason to consider
Julia**), MATLAB's `ode45`/`ode15s`.

### 7.2 PDEs

**The discretization families**: **finite difference** (simple, structured grids),
**finite volume** (⚠️ **conservative by construction — the right choice for fluids and
anything with conservation laws**), **finite element** (complex geometry, rigorous error
theory), **spectral** (⚠️ **exponential convergence for smooth problems on simple
domains**), and **meshless/particle** methods.

**⚠️ The CFL condition** governs explicit time-stepping stability: your time step is
bounded by the mesh spacing over the wave speed. **Refining the mesh forces smaller time
steps**, which is why explicit schemes get expensive quadratically.

**Frameworks**: **FEniCS/Firedrake** (⚠️ **write the weak form, get a solver — genuinely
remarkable**), **deal.II**, **MFEM**, **OpenFOAM** (CFD), **SU2**, **Gmsh** for meshing,
**ParaView/VisIt** for visualization.

**⚠️ And the practical truth: meshing is usually the hard part, not solving.** Budget
accordingly.

### 7.3 Scientific machine learning
**[VERSIONED]** **PINNs**, **neural ODEs**, **operator learning (DeepONet, Fourier Neural
Operator)**, and hybrid physics-ML models. ⚠️ **Promising and genuinely oversold: for
classical forward problems on well-posed domains, a good conventional solver is usually
faster and far more reliable.** The stronger cases are inverse problems, surrogate models
for repeated queries, and problems where the governing equations are partly unknown.

---

## §8. Optimization

**[DURABLE] Classify the problem before choosing a method — this is most of the work.**

```
Is it convex?          → YES: a global optimum exists and is findable. Say so, and exploit it
                         NO: you get a local optimum. Multi-start, or accept it
Do you have gradients? → AD (§5) is almost always available and almost always worth it
Constraints?           → Linear (LP/QP), nonlinear (SQP, interior point), or none
Smooth?                → Non-smooth needs subgradient/proximal methods
Expensive to evaluate? → Bayesian optimization / surrogate methods
Discrete?              → MILP, or see a theory-of-computation reference on NP-hardness
```

| Class | Methods | Tools |
|---|---|---|
| **LP / QP / conic** | Simplex, interior point | ⚠️ **Gurobi, CPLEX, Mosek (commercial, much faster); HiGHS, OSQP, SCS, Clarabel (open)** |
| **Smooth unconstrained** | BFGS, L-BFGS, Newton, trust region | scipy.optimize, NLopt, Optim.jl |
| **Constrained nonlinear** | SQP, interior point | **IPOPT**, SNOPT, `scipy` SLSQP |
| **Least squares** | Levenberg–Marquardt, Gauss–Newton | Ceres, `least_squares` |
| **Global / derivative-free** | Nelder–Mead, CMA-ES, DIRECT, differential evolution | NLopt, pymoo |
| **Modelling layers** | — | **CVXPY**, JuMP.jl, Pyomo, AMPL |

> **⚠️ GOTCHA — the optimization failure modes that waste the most time:**
> - **Not scaling variables.** ⚠️ **If one variable is ~10⁻⁶ and another ~10⁶, the solver
>   sees a pathological problem. Non-dimensionalize.** This is the most common cause of
>   "the optimizer won't converge."
> - **Finite-difference gradients when AD was available.** Slower, less accurate, and it
>   inherits §2 → `sci-floating-point-and-numerical-foundations`'s differentiation ill-conditioning.
> - **⚠️ Believing a local optimum is global** in a non-convex problem.
> - **Ignoring the exit flag.** ⚠️ **Solvers return status codes and people read only `x`.**
>   "Max iterations reached" is not convergence.
> - **Reformulating a convex problem into a non-convex one** by accident — CVXPY's
>   disciplined convex programming rules exist to prevent exactly this.

**⚠️ §8.4 Inverse and ill-posed problems** deserve their own note: fitting parameters to
data is often **ill-posed**, and the fix is **regularization** — Tikhonov/ridge, L1/lasso,
total variation — with the regularization parameter chosen by **L-curve or cross-
validation**, not by eye. **An unregularized inverse problem fits noise beautifully.**

---

## §9. Interpolation, Quadrature, Transforms

**Interpolation**: ⚠️ **Do not fit high-degree polynomials to equispaced points** —
**Runge's phenomenon** makes the error explode at the endpoints. **Use splines (cubic, or
monotone PCHIP if overshoot matters), or Chebyshev nodes** if you control the sampling.
**Interpolation ≠ regression**: interpolation passes through every point (⚠️ **including
the noise**); fit a smoother if the data is noisy.

**Quadrature**: **Gauss–Legendre** (exceptional for smooth integrands), **adaptive
Clenshaw–Curtis**, **QUADPACK** under `scipy.integrate.quad`. ⚠️ **For dimensions above
~4, deterministic quadrature dies to the curse of dimensionality — use Monte Carlo or
quasi-Monte Carlo (Sobol), whose error is dimension-independent.** Handle **singularities
and infinite domains with a variable transformation**, not brute force.

**Transforms**: **FFT** — ⚠️ **O(n log n), and the workhorse of signal processing and
spectral methods.** **FFTW** is the reference implementation. Know the pitfalls:
**aliasing** (sample above Nyquist), **spectral leakage** (window your data), **and the
normalization convention differs between libraries** — ⚠️ **check whether the 1/N is on the
forward or inverse transform before comparing results across tools.**
