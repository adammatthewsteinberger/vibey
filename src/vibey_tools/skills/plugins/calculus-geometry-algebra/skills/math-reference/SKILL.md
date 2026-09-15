---
name: math-reference
description: "Use when correcting a mathematical misconception, looking up a formula or identity, finding the textbook canon, or needing a method picker and the sanity checks worth running on a derivation or a numerical result. Companion to the other calculus-geometry-algebra skills."
---

# Calculus, Geometry and Algebra: Misconceptions, Formulas, and Canon

> **Part 6 of 6** of the *Calculus, Geometry and Algebra* reference (plugin `calculus-geometry-algebra`), covering §22–§26. Sibling skills: `math-linear-algebra-foundations` (§0–§4), `math-inner-products-svd-and-numerical-reality` (§5–§8), `math-calculus-and-vector-calculus` (§9–§13), `math-forms-optimization-and-differential-equations` (§14–§16), `math-geometry-manifolds-tensors-and-lie-groups` (§17–§21). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Permanently settled — Newton and Leibniz in the 1670s, Gauss and Cauchy in the 1820s, Grassmann 1844, Riemann 1854, Ricci-Curbastro in the 1890s, Cartan 1899, Eckart-Young 1936.

> **How to read this.** Three connected parts: **linear algebra (§1–§8 → `math-linear-algebra-foundations`, `math-inner-products-svd-and-numerical-reality`)**, **calculus
> (§9–§16 → `math-calculus-and-vector-calculus`, `math-forms-optimization-and-differential-equations`)**, **geometry and tensors (§17–§21 → `math-geometry-manifolds-tensors-and-lie-groups`)**. ⚠️ **They are far more connected than
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
>    sequence** (§14 → `math-forms-optimization-and-differential-equations`).

---

## §22. Misconceptions

| Misconception | Correction |
|---|---|
| A matrix *is* a linear map | ⚠️ **It represents one in a chosen basis** (§1 → `math-linear-algebra-foundations`) |
| Eigendecomposition is the fundamental factorization | ⚠️ **SVD is — it always exists** (§6.1 → `math-inner-products-svd-and-numerical-reality`) |
| Every matrix is diagonalizable | ⚠️ **Defective matrices exist; use Schur, not Jordan** (§4 → `math-linear-algebra-foundations`, §7 → `math-inner-products-svd-and-numerical-reality`) |
| Determinant is a computational tool | ⚠️ **Conceptually central, computationally marginal** (§3 → `math-linear-algebra-foundations`) |
| Test `det = 0` for singularity | ⚠️ **Use σ_min or κ** (§3 → `math-linear-algebra-foundations`, §8 → `math-inner-products-svd-and-numerical-reality`) |
| Solve least squares via normal equations | ⚠️ **`AᵀA` squares the condition number. Use QR/SVD** (§5 → `math-inner-products-svd-and-numerical-reality`, §8 → `math-inner-products-svd-and-numerical-reality`) |
| Invert the matrix to solve `Ax = b` | ⚠️ **Solve the system — faster and more accurate** (§8 → `math-inner-products-svd-and-numerical-reality`) |
| Compute eigenvalues from the characteristic polynomial | ⚠️ **Polynomial roots are wildly ill-conditioned** (§8 → `math-inner-products-svd-and-numerical-reality`) |
| A better algorithm fixes an ill-conditioned problem | ⚠️ **Conditioning is the problem's property, not the algorithm's** (§8 → `math-inner-products-svd-and-numerical-reality`) |
| The derivative is the slope of the tangent | ⚠️ **It's the best linear approximation — that's what generalizes** (§9.2 → `math-calculus-and-vector-calculus`) |
| Smooth implies analytic | ⚠️ **`e^{−1/x²}` — false in real analysis, true in complex** (§11 → `math-calculus-and-vector-calculus`) |
| Green's, Stokes' and divergence are three theorems | ⚠️ **One theorem: `∫_∂M ω = ∫_M dω`** (§13 → `math-calculus-and-vector-calculus`, §14 → `math-forms-optimization-and-differential-equations`) |
| Curl-free implies conservative | ⚠️ **Only on a simply connected domain** (§13 → `math-calculus-and-vector-calculus`) |
| Fubini always lets you swap integration order | ⚠️ **Needs absolute integrability** (§12 → `math-calculus-and-vector-calculus`) |
| A conditionally convergent series has a sum | ⚠️ **Rearrangement gives any value you like** (§11 → `math-calculus-and-vector-calculus`) |
| Vectors and covectors are the same thing | ⚠️ **They coincide only in Euclidean space with an orthonormal basis** (§19 → `math-geometry-manifolds-tensors-and-lie-groups`) |
| A PyTorch tensor is a tensor | ⚠️ **It's an n-d array. A tensor is basis-independent** (§19 → `math-geometry-manifolds-tensors-and-lie-groups`) |
| Christoffel symbols are tensors | ⚠️ **They aren't — which is why they can vanish at a point** (§20 → `math-geometry-manifolds-tensors-and-lie-groups`) |
| You can compare vectors at different points on a manifold | ⚠️ **Not without a connection; the failure to do so IS curvature** (§18 → `math-geometry-manifolds-tensors-and-lie-groups`, §20 → `math-geometry-manifolds-tensors-and-lie-groups`) |
| Tensor decompositions inherit SVD's guarantees | ⚠️ **Order ≥3: best rank-k may not exist; rank is NP-hard** (§19 → `math-geometry-manifolds-tensors-and-lie-groups`) |
| High-dimensional critical points are usually minima | ⚠️ **Overwhelmingly saddles** (§12 → `math-calculus-and-vector-calculus`) |
| Optimize rotations by parameterizing the matrix | ⚠️ **Work in the Lie algebra** (§21 → `math-geometry-manifolds-tensors-and-lie-groups`) |

---

## §23. Formulas

```
LINEAR ALGEBRA
⚠️ Rank-nullity: dim ker + dim im = dim domain
Four subspaces: row ⊥ null (ℝⁿ), col ⊥ left-null (ℝᵐ)  ⚠️ dims r, n−r, r, m−r
det(AB) = det A det B · trace = Σλ · det = Πλ
Projection: P = A(AᵀA)⁻¹Aᵀ · Normal equations AᵀAx̂ = Aᵀb  ⚠️ (don't solve directly)
Spectral: A = QΛQᵀ (symmetric) · ⚠️ SVD: A = UΣVᵀ (ANY matrix)
κ(A) = σ_max/σ_min   ⚠️ lose ~k digits when κ ≈ 10ᵏ
⚠️ Eckart-Young: truncated SVD is the optimal rank-k approximation
Pseudoinverse A⁺ = VΣ⁺Uᵀ

CALCULUS
⚠️ f(a+h) = f(a) + f'(a)h + o(h)   — the definition that generalizes
FTC: d/dx ∫ₐˣf = f(x) · ∫ₐᵇf' = f(b) − f(a)
Taylor: f(x) = Σf⁽ⁿ⁾(a)(x−a)ⁿ/n!  ⚠️ + remainder
Chain rule (multivariable) = Jacobian product ⚠️ = backpropagation
∇×(∇f) = 0 · ∇·(∇×F) = 0   ⚠️ both are d² = 0
⚠️ GENERALIZED STOKES: ∫_∂M ω = ∫_M dω
Lagrange: ∇f = λ∇g · ⚠️ KKT adds μ ≥ 0 and μᵢgᵢ = 0

HESSIAN TEST
PD → min · ND → max · indefinite → ⚠️ saddle · singular → inconclusive

GEOMETRY & TENSORS
⚠️ Einstein summation: repeated upper-lower pairs sum
vⁱ contravariant (upper) · ωᵢ covariant (lower) · g_{ij} lowers, g^{ij} raises
Geodesic: ∇_γ̇ γ̇ = 0
⚠️ Theorema Egregium: Gaussian curvature is intrinsic
Riemann tensor ⚠️ = failure of parallel transport around a loop
Lie: exp: 𝔤 → G  ⚠️ optimize in the algebra, map back

NUMERICAL COSTS
LU O(n³/3) · Cholesky O(n³/6) · QR O(2mn²) · SVD O(mn²)
Trapezoid O(h²) · Simpson O(h⁴) · ⚠️ Monte Carlo O(N^{-1/2}), dimension-independent
```

---

## §24. Books

**Linear algebra**
| Author | Work | Why |
|---|---|---|
| **Strang** | ***Introduction to Linear Algebra*** + MIT 18.06 lectures | ⚠️ **The four subspaces framing (§2 → `math-linear-algebra-foundations`). The best first exposure, and the lectures are free** |
| **Axler** | ***Linear Algebra Done Right*** | ⚠️ **Determinant-free, map-first. The right second book — it fixes the §1 → `math-linear-algebra-foundations` misconception structurally** |
| **Trefethen & Bau** | ***Numerical Linear Algebra*** | ⚠️ **§7 → `math-inner-products-svd-and-numerical-reality` and §8 → `math-inner-products-svd-and-numerical-reality`. Beautifully written and genuinely enjoyable** |
| **Golub & Van Loan** | *Matrix Computations* | The reference |
| **Horn & Johnson** | *Matrix Analysis* | Theory reference |

**Calculus and analysis**
| **Spivak** | ***Calculus*** | ⚠️ **Rigorous single-variable. Really an analysis book** |
| **Rudin** | *Principles of Mathematical Analysis* | Terse, canonical, hard |
| **Tao** | *Analysis I & II* | ⚠️ **More humane than Rudin, equally rigorous** |
| **Hubbard & Hubbard** | ***Vector Calculus, Linear Algebra, and Differential Forms*** | ⚠️ **The unified treatment. Exactly the §13 → `math-calculus-and-vector-calculus`→§14 → `math-forms-optimization-and-differential-equations` connection this document argues for** |
| **Spivak** | *Calculus on Manifolds* | ⚠️ **Tiny, dense, and the classic route to generalized Stokes** |

**Geometry, tensors, and applications**
| **do Carmo** | *Differential Geometry of Curves and Surfaces* | The standard entry |
| **Lee** | ***Introduction to Smooth Manifolds*** | ⚠️ **§18–§20 → `math-geometry-manifolds-tensors-and-lie-groups`, thorough and clear** |
| **Needham** | ***Visual Differential Geometry and Forms*** | ⚠️ **Geometric intuition first. Unusual and excellent** |
| **Misner, Thorne & Wheeler** | *Gravitation* | ⚠️ **The tensor exposition is superb regardless of your interest in GR** |
| **Boyd & Vandenberghe** | ***Convex Optimization*** | ⚠️ **§15 → `math-forms-optimization-and-differential-equations`. Free online, and the standard** |
| **Nocedal & Wright** | *Numerical Optimization* | The algorithms |
| **Strang** | *Linear Algebra and Learning from Data* | The ML-facing treatment |

**⚠️ Also**: **3Blue1Brown's *Essence of Linear Algebra* and *Essence of Calculus*** —
⚠️ **the best geometric intuition available for §1–§6 → `math-linear-algebra-foundations`, `math-inner-products-svd-and-numerical-reality` and §9 → `math-calculus-and-vector-calculus`, free, and worth watching
even if you already know the material.**

---

## §25. Quick Reference

### 25.1 Picker
| Need | Use |
|---|---|
| Solve `Ax = b`, square, general | **LU with partial pivoting** (§7 → `math-inner-products-svd-and-numerical-reality`) |
| Solve `Ax = b`, symmetric positive definite | ⚠️ **Cholesky — twice as fast** (§7 → `math-inner-products-svd-and-numerical-reality`) |
| Least squares | ⚠️ **QR (or SVD if rank-deficient). Never normal equations** (§5 → `math-inner-products-svd-and-numerical-reality`, §7 → `math-inner-products-svd-and-numerical-reality`) |
| Rank, or numerical rank | ⚠️ **SVD — count singular values above tolerance** (§6.1 → `math-inner-products-svd-and-numerical-reality`) |
| Best low-rank approximation | ⚠️ **Truncated SVD (Eckart-Young)** (§6.1 → `math-inner-products-svd-and-numerical-reality`) |
| PCA | ⚠️ **SVD of centred data** (§6.1 → `math-inner-products-svd-and-numerical-reality`) |
| Is this problem well posed? | **Condition number** (§8 → `math-inner-products-svd-and-numerical-reality`) |
| Matrix powers or `e^{At}` | **Eigendecomposition, or Schur if defective** (§4 → `math-linear-algebra-foundations`, §16 → `math-forms-optimization-and-differential-equations`) |
| Huge sparse system | **Krylov (CG/GMRES) + ⚠️ a good preconditioner** (§7 → `math-inner-products-svd-and-numerical-reality`) |
| Direction of steepest ascent | **Gradient** (§12 → `math-calculus-and-vector-calculus`) |
| Classify a critical point | **Hessian eigenvalues** (§12 → `math-calculus-and-vector-calculus`) |
| Optimize with equality constraints | **Lagrange multipliers** (§15 → `math-forms-optimization-and-differential-equations`) |
| Optimize with inequality constraints | **KKT; ⚠️ check convexity for sufficiency** (§15 → `math-forms-optimization-and-differential-equations`) |
| Convert a boundary integral to a volume one | ⚠️ **Generalized Stokes** (§14 → `math-forms-optimization-and-differential-equations`) |
| High-dimensional integral | ⚠️ **Monte Carlo — error independent of dimension** (§10 → `math-calculus-and-vector-calculus`) |
| Represent rotations for optimization | ⚠️ **Lie algebra `so(3)`/`se(3)`** (§21 → `math-geometry-manifolds-tensors-and-lie-groups`) |
| Quantity that must be basis-independent | ⚠️ **Check it's actually a tensor** (§19 → `math-geometry-manifolds-tensors-and-lie-groups`) |

### 25.2 Sanity checks
- [ ] Dimensional/shape analysis — do the dimensions compose? (§1 → `math-linear-algebra-foundations`)
- [ ] Is my "tensor" basis-independent, or just an array? (§19 → `math-geometry-manifolds-tensors-and-lie-groups`)
- [ ] Am I forming `AᵀA` anywhere? ⚠️ **Don't** (§8 → `math-inner-products-svd-and-numerical-reality`)
- [ ] What's the condition number? (§8 → `math-inner-products-svd-and-numerical-reality`)
- [ ] Does this theorem's hypothesis actually hold — simply connected, absolutely integrable, convex, Lipschitz? (§11 → `math-calculus-and-vector-calculus`, §12 → `math-calculus-and-vector-calculus`, §13 → `math-calculus-and-vector-calculus`, §15 → `math-forms-optimization-and-differential-equations`, §16 → `math-forms-optimization-and-differential-equations`)
- [ ] Limiting cases: does the formula behave sensibly as parameters → 0 or ∞?
- [ ] Is the Taylor remainder small enough for the use I'm making of it? (§11 → `math-calculus-and-vector-calculus`)
- [ ] Am I comparing vectors at different points on a curved space? (§18 → `math-geometry-manifolds-tensors-and-lie-groups`)

---

## §26. Method

**No searches were run; none could be relevant.** ⚠️ **This is the most settled material
in the series.** **Newton and Leibniz (1670s)**, **Gauss**, **Cauchy's rigorous limits
(1820s)**, **Grassmann (1844)**, **Riemann (1854)**, **Ricci-Curbastro and Levi-Civita
(1890s)**, **Cartan's exterior calculus (1899)**, **Eckart-Young (1936)**. ⚠️ **None of
it will change.**

**Sources** are the texts in §24 — chiefly **Strang** and **Axler** for §1–§6 → `math-linear-algebra-foundations`, `math-inner-products-svd-and-numerical-reality`,
**Trefethen & Bau** for §7–§8 → `math-inner-products-svd-and-numerical-reality`, **Spivak** and **Hubbard & Hubbard** for §9–§15 → `math-calculus-and-vector-calculus`, `math-forms-optimization-and-differential-equations`, **Lee**
and **do Carmo** for §17–§21 → `math-geometry-manifolds-tensors-and-lie-groups`, and **Boyd & Vandenberghe** for §15 → `math-forms-optimization-and-differential-equations`.

**Confidence: high throughout**, ⚠️ **and I have stated theorems with their hypotheses,
because in mathematics the hypotheses are the theorem.** **§22 is largely a list of
results applied outside their conditions.**

⚠️ **Four editorial choices worth naming, since they shape what's emphasized.**

**§6.1 → `math-inner-products-svd-and-numerical-reality` gives SVD priority over eigendecomposition, deliberately.** ⚠️ **Standard curricula
teach eigendecomposition first and often never reach SVD properly, which leaves people
with the fundamental factorization backwards.** **SVD exists for every matrix, gives all
four subspaces, the condition number, the pseudoinverse, and the optimal low-rank
approximation.** **Eigendecomposition needs a square matrix and can fail.** ⚠️ **If you
retain one thing from Part I, retain SVD.**

**§13 → `math-calculus-and-vector-calculus` and §14 → `math-forms-optimization-and-differential-equations` present the integral theorems as one theorem.** ⚠️ **Teaching Green's,
Stokes' and the divergence theorem as three separate formulas is, I'd argue, the largest
structural failure in the standard calculus sequence** — **students memorize three things
that are one thing, and the unifying statement `∫_∂M ω = ∫_M dω` is both simpler and more
powerful.** **Hubbard & Hubbard and Spivak's *Calculus on Manifolds* both take this route
and it's worth the detour.**

**§19 → `math-geometry-manifolds-tensors-and-lie-groups` is the section I'd most want read by anyone working in machine learning.** ⚠️ **The
word "tensor" carries three inequivalent meanings, and the ML usage is the one that is
*not* the mathematical object.** **A PyTorch tensor is a data structure; a tensor proper
is basis-independent and defined by how its components transform.** ⚠️ **The distinction is
harmless until you change coordinates, and then it isn't.** **It is precisely §1 → `math-linear-algebra-foundations`'s
matrix-versus-linear-map problem one level up, which is why I've placed them as bookends.**

**§8 → `math-inner-products-svd-and-numerical-reality`'s numerical warnings are included because they're the gap between knowing the
mathematics and getting a correct answer.** ⚠️ **Every item in that section is something
that is mathematically valid and numerically wrong** — the normal equations, the
characteristic polynomial, matrix inversion, `det = 0`. **Trefethen & Bau is the book that
fixes this, and it's genuinely a pleasure to read, which is rare in numerical analysis.**
