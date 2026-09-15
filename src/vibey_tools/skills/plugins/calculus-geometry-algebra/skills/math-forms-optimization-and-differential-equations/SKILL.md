---
name: math-forms-optimization-and-differential-equations
description: "Use when the problem needs the more structural tools: differential forms and the exterior derivative as the framework that unifies the vector calculus integral theorems, constrained optimization with Lagrange multipliers and the KKT conditions, and differential equations — the solution methods, classification, and what makes a system stiff or stable."
---

# Calculus, Geometry and Algebra: Differential Forms, Constrained Optimization, and Differential Equations

> **Part 4 of 6** of the *Calculus, Geometry and Algebra* reference (plugin `calculus-geometry-algebra`), covering §14–§16. Sibling skills: `math-linear-algebra-foundations` (§0–§4), `math-inner-products-svd-and-numerical-reality` (§5–§8), `math-calculus-and-vector-calculus` (§9–§13), `math-geometry-manifolds-tensors-and-lie-groups` (§17–§21), `math-reference` (§22–§26). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Permanently settled — Newton and Leibniz in the 1670s, Gauss and Cauchy in the 1820s, Grassmann 1844, Riemann 1854, Ricci-Curbastro in the 1890s, Cartan 1899, Eckart-Young 1936.

> **How to read this.** Three connected parts: **linear algebra (§1–§8 → `math-linear-algebra-foundations`, `math-inner-products-svd-and-numerical-reality`)**, **calculus
> (§9–§16 → `math-calculus-and-vector-calculus`)**, **geometry and tensors (§17–§21 → `math-geometry-manifolds-tensors-and-lie-groups`)**. ⚠️ **They are far more connected than
> standard curricula suggest, and the connections are where the understanding is.**
>
> **⚠️ GOTCHA** boxes mark places where standard teaching creates a misconception.
>
> **The three unifying ideas:**
> 1. **⚠️ The derivative is the best linear approximation.** Not a slope, not a limit of
>    quotients — those are how you compute it in one dimension. **Once you see it as a
>    linear map, the multivariable chain rule, the Jacobian, and manifolds all become
>    obvious** (§9.2 → `math-calculus-and-vector-calculus`).
> 2. **⚠️ Linear algebra is about maps, not arrays.** A matrix is a *representation* of a
>    linear map in a chosen basis. **Eigenvectors, determinants, and SVD are all
>    basis-independent facts about the map that the array happens to encode** (§2 → `math-linear-algebra-foundations`).
> 3. **⚠️ Green's, Stokes', and the divergence theorem are one theorem.** They're the
>    generalized Stokes theorem `∫_∂M ω = ∫_M dω` in different dimensions. **Learning them
>    as three unrelated formulas is the single biggest missed opportunity in the standard
>    sequence** (§14).

---

## §14. Differential Forms

**⚠️ The unification, and it repays the effort.**
```
0-form   function f
1-form   ω = f dx + g dy + h dz         ⚠️ integrate over curves
2-form   ω = f dx∧dy + ...              integrate over surfaces
3-form   f dx∧dy∧dz                     integrate over volumes
```
**Wedge product `∧`** — ⚠️ **antisymmetric: `dx∧dy = −dy∧dx`, so `dx∧dx = 0`.** **The
antisymmetry is what encodes orientation and signed volume — the same fact as §3 → `math-linear-algebra-foundations`'s
determinant.**
**Exterior derivative `d`** — ⚠️ **`d² = 0` always**, which reproduces both identities in
§13 → `math-calculus-and-vector-calculus` at once.

**⚠️ Generalized Stokes theorem:**
```
∫_∂M ω = ∫_M dω
```
⚠️ **That single line contains the FTC, Green's, Stokes' and the divergence theorem.**
**"The integral of `dω` over a region equals the integral of `ω` over its boundary."**
**⚠️ And the notational suggestiveness is real: `d` and `∂` are adjoint, which is the
germ of de Rham cohomology — closed forms (`dω = 0`) modulo exact forms (`ω = dη`) measure
the topology of the space.** **That's how the punctured-plane counterexample in §13 → `math-calculus-and-vector-calculus`
becomes a theorem rather than a curiosity.**

---

## §15. Constrained Optimization

**Lagrange multipliers** — to optimize `f` subject to `g = 0`:
```
∇f = λ∇g
```
**⚠️ The geometric reason, which makes it memorable**: at a constrained optimum, **the level
set of `f` is tangent to the constraint surface**, so their gradients are parallel (§12 → `math-calculus-and-vector-calculus`).
**If they weren't, you could move along the constraint and improve.**
**⚠️ `λ` is the shadow price — the rate of change of the optimum with respect to relaxing
the constraint. That interpretation is often the most useful output.**

**KKT conditions** extend this to inequality constraints:
```
Stationarity · Primal feasibility · Dual feasibility (μ ≥ 0)
⚠️ Complementary slackness: μᵢgᵢ = 0 — either the constraint is active or its
   multiplier is zero
```
**⚠️ KKT is necessary under constraint qualification, and sufficient for convex problems**
— **which is why convexity matters so much: it converts a necessary condition into a
certificate of global optimality.**
**Duality** — the dual gives a bound; ⚠️ **strong duality (zero gap) holds for convex
problems under Slater's condition.**

---

## §16. Differential Equations

**ODEs**: separable, linear (integrating factor), exact, **constant-coefficient linear**
(⚠️ **solved by the characteristic equation, which is §4 → `math-linear-algebra-foundations`'s eigenvalue problem**).
**Systems `ẋ = Ax`** have solution `x(t) = e^{At}x₀` — ⚠️ **and the matrix exponential is
computed via eigendecomposition, so stability is read off the eigenvalues: `Re(λ) < 0` for
all λ means stable.** **Existence and uniqueness (Picard-Lindelöf) requires Lipschitz
continuity.**

**PDEs** by type, and ⚠️ **the classification determines everything about behaviour and
numerics:**
```
Elliptic    (Laplace, Poisson)   ⚠️ equilibrium; boundary-value; smooth solutions
Parabolic   (heat)               ⚠️ diffusion; smooths data; irreversible
Hyperbolic  (wave)               ⚠️ finite propagation speed; preserves discontinuities
```
**Methods**: separation of variables, **Fourier and Laplace transforms** (⚠️ **which turn
differentiation into multiplication — the reason transform methods work at all**), Green's
functions, characteristics.

---

# PART III — GEOMETRY AND TENSORS
