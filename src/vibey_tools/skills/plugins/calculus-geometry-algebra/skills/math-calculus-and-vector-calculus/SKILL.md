---
name: math-calculus-and-vector-calculus
description: "Use when doing calculus rather than reading it: limits and continuity and what the derivative actually is as a linear approximation, integration and its several distinct meanings, series and Taylor approximation with convergence and truncation error, multivariable calculus including gradients, Jacobians and Hessians, and vector calculus with divergence, curl and the integral theorems."
---

# Calculus, Geometry and Algebra: The Derivative, Integration, Series, and Vector Calculus

> **Part 3 of 6** of the *Calculus, Geometry and Algebra* reference (plugin `calculus-geometry-algebra`), covering §9–§13. Sibling skills: `math-linear-algebra-foundations` (§0–§4), `math-inner-products-svd-and-numerical-reality` (§5–§8), `math-forms-optimization-and-differential-equations` (§14–§16), `math-geometry-manifolds-tensors-and-lie-groups` (§17–§21), `math-reference` (§22–§26). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Permanently settled — Newton and Leibniz in the 1670s, Gauss and Cauchy in the 1820s, Grassmann 1844, Riemann 1854, Ricci-Curbastro in the 1890s, Cartan 1899, Eckart-Young 1936.

> **How to read this.** Three connected parts: **linear algebra (§1–§8 → `math-linear-algebra-foundations`, `math-inner-products-svd-and-numerical-reality`)**, **calculus
> (§9–§16 → `math-forms-optimization-and-differential-equations`)**, **geometry and tensors (§17–§21 → `math-geometry-manifolds-tensors-and-lie-groups`)**. ⚠️ **They are far more connected than
> standard curricula suggest, and the connections are where the understanding is.**
>
> **⚠️ GOTCHA** boxes mark places where standard teaching creates a misconception.
>
> **The three unifying ideas:**
> 1. **⚠️ The derivative is the best linear approximation.** Not a slope, not a limit of
>    quotients — those are how you compute it in one dimension. **Once you see it as a
>    linear map, the multivariable chain rule, the Jacobian, and manifolds all become
>    obvious** (§9.2).
> 2. **⚠️ Linear algebra is about maps, not arrays.** A matrix is a *representation* of a
>    linear map in a chosen basis. **Eigenvectors, determinants, and SVD are all
>    basis-independent facts about the map that the array happens to encode** (§2 → `math-linear-algebra-foundations`).
> 3. **⚠️ Green's, Stokes', and the divergence theorem are one theorem.** They're the
>    generalized Stokes theorem `∫_∂M ω = ∫_M dω` in different dimensions. **Learning them
>    as three unrelated formulas is the single biggest missed opportunity in the standard
>    sequence** (§14 → `math-forms-optimization-and-differential-equations`).

---

## §9. The Derivative

### 9.1 Limits and continuity
**`lim_{x→a} f(x) = L`** — ⚠️ **the ε-δ definition is what makes the subject rigorous, and
it exists to handle exactly the cases intuition fails on.**
**Continuity** at `a`: the limit exists and equals `f(a)`.
**⚠️ Uniform continuity** is stronger — one δ works everywhere; **and it's what you need for
theorems about integrability.**
**Key theorems on compact intervals**: **Intermediate Value**, **Extreme Value**, **Mean
Value** (⚠️ **the workhorse — most of single-variable calculus's theory is corollaries of
MVT**).

### 9.2 ⚠️ What the derivative actually is
```
f(a + h) = f(a) + f'(a)h + o(h)
```
> **⚠️ GOTCHA — the derivative is the best LINEAR APPROXIMATION at a point, and this is
> the definition worth carrying.** ⚠️ **"Slope of the tangent line" is a 1D picture;
> "limit of difference quotients" is a computation.** **Neither generalizes.**
> **The linear-approximation view generalizes immediately**: ⚠️ **in `ℝⁿ → ℝᵐ` the
> derivative is a linear map (the Jacobian); on a manifold it's a map between tangent
> spaces (§18 → `math-geometry-manifolds-tensors-and-lie-groups`); in a function space it's the Fréchet derivative.** **Same idea
> throughout.**

**Rules**: product, quotient, **chain rule** (⚠️ **which is just composition of linear
approximations — that's why it's a product**).
**⚠️ Differentiable ⟹ continuous, but not conversely** (`|x|` at 0; **and Weierstrass's
function is continuous everywhere and differentiable nowhere**).

---

## §10. Integration

**Riemann integral** — limit of tapering partitions. **Fundamental Theorem of Calculus**:
```
d/dx ∫ₐˣ f(t)dt = f(x)        ∫ₐᵇ f'(x)dx = f(b) − f(a)
```
⚠️ **Differentiation and integration are inverse operations — the central insight of the
whole subject, and it was not obvious to anyone before Newton and Leibniz.**

**⚠️ Lebesgue integration** — partition the *range* rather than the domain. **Why it
matters**: it integrates far more functions, and ⚠️ **crucially, it has good convergence
theorems (monotone and dominated convergence) that let you exchange limits and integrals.**
**Riemann's don't.** **This is why probability theory and functional analysis are built on
Lebesgue.**

**Techniques**: substitution (⚠️ **the chain rule backwards**), integration by parts
(⚠️ **the product rule backwards, and the source of the adjoint relationships throughout
physics**), partial fractions, trigonometric substitution, contour integration.
**Improper integrals** and convergence tests.

**⚠️ Numerical integration**: trapezoid `O(h²)`, Simpson `O(h⁴)`, **Gaussian quadrature**
(⚠️ **exact for polynomials up to degree `2n−1` with `n` points — remarkably efficient**),
**adaptive methods**, and ⚠️ **Monte Carlo, whose `O(N^{-1/2})` error is dimension-
independent — which is why it wins in high dimensions despite being slow in low ones.**

---

## §11. Series and Taylor Approximation

**Convergence tests**: ratio, root, comparison, integral, alternating.
⚠️ **Absolute vs conditional convergence matters**: **a conditionally convergent series can
be rearranged to converge to any value whatsoever (Riemann rearrangement).**

**Taylor series**:
```
f(x) = Σ f⁽ⁿ⁾(a)(x−a)ⁿ/n!
```
**⚠️ With the remainder term — the remainder is the part that matters and the part that
gets dropped.** **Lagrange form: `R_n = f⁽ⁿ⁺¹⁾(ξ)(x−a)ⁿ⁺¹/(n+1)!`.**
> **⚠️ GOTCHA — a function can be infinitely differentiable and NOT equal its Taylor
> series.** ⚠️ **`e^{−1/x²}` (with `f(0)=0`) has every derivative zero at the origin, so
> its Taylor series is identically zero, while the function is not.** **Smooth does not
> imply analytic.** ⚠️ **In complex analysis this cannot happen — differentiable once
> implies analytic — which is a genuinely deep difference between real and complex
> analysis.**

**Radius of convergence**, **Fourier series** (⚠️ **expansion in an orthogonal basis of
functions — which is §5 → `math-inner-products-svd-and-numerical-reality` in an infinite-dimensional space, and seeing it that way makes it
much less mysterious**), and **asymptotic series** (⚠️ **divergent yet useful — truncating
at the right term gives excellent accuracy, and adding more terms makes it worse**).

---

## §12. Multivariable Calculus

**Partial derivatives**, **gradient `∇f`** (⚠️ **direction of steepest ascent, and
perpendicular to level sets — the second fact is the one people forget and it's what
makes Lagrange multipliers work**), **directional derivative `∇f · û`**.

**Jacobian** `J` — ⚠️ **the matrix of the derivative as a linear map** (§9.2). **For
`f: ℝⁿ → ℝᵐ` it's `m×n`.** **The chain rule is matrix multiplication of Jacobians** —
⚠️ **which is exactly backpropagation.**

**Hessian** `H` — second partials, ⚠️ **symmetric when the function is `C²` (Clairaut),
which is why §6 → `math-inner-products-svd-and-numerical-reality`'s spectral theorem applies to it.**
```
H positive definite    ⚠️ local minimum
H negative definite    local maximum
H indefinite           ⚠️ saddle point
H singular             ⚠️ test inconclusive
```
**⚠️ In high dimensions, critical points of random functions are overwhelmingly saddles
rather than local minima** — the eigenvalues would all need the same sign by chance.
**This reframes what optimization is fighting.**

**Multiple integrals**, **Fubini** (⚠️ **exchange order of integration — requires
absolute integrability, and there are standard counterexamples when it fails**),
**change of variables with the Jacobian determinant** (§3 → `math-linear-algebra-foundations`).

---

## §13. Vector Calculus

```
grad   ∇f          scalar → vector      ⚠️ steepest ascent
div    ∇·F         vector → scalar      ⚠️ source/sink density
curl   ∇×F         vector → vector      ⚠️ circulation density (3D only)
lap    ∇²f = ∇·∇f  ⚠️ deviation from the local average — why it governs diffusion
```
**⚠️ Identities worth memorizing**: `∇×(∇f) = 0` (**gradients are curl-free**) and
`∇·(∇×F) = 0` (**curls are divergence-free**). ⚠️ **Both are `d² = 0` in disguise** (§14 → `math-forms-optimization-and-differential-equations`).

**The integral theorems:**
```
FTC (1D)               ∫ₐᵇ f' = f(b) − f(a)
Green's (2D)           ∮ (P dx + Q dy) = ∬ (∂Q/∂x − ∂P/∂y) dA
Stokes' (surface)      ∮ F·dr = ∬ (∇×F)·dS
Divergence/Gauss (3D)  ∯ F·dS = ∭ (∇·F) dV
```
> **⚠️ GOTCHA — these are four instances of ONE theorem, and teaching them separately is
> the biggest structural failure in the standard calculus sequence.** ⚠️ **All say: the
> integral of a derivative over a region equals the integral of the original over the
> boundary.** **§14 → `math-forms-optimization-and-differential-equations` makes this literal.**

**Conservative fields**: `F = ∇φ` ⟺ path-independent ⟺ `∮F·dr = 0` ⟺ `∇×F = 0`
⚠️ **(the last equivalence requires a simply connected domain — and the standard
counterexample on a punctured plane is where topology enters analysis).**
