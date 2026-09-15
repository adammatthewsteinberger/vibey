---
name: math-inner-products-svd-and-numerical-reality
description: "Use when the numerical behaviour of linear algebra matters: inner products, orthogonality, projections and Gram-Schmidt, the spectral theorem for symmetric matrices and the singular value decomposition as the most important factorization, the matrix factorizations (LU, QR, Cholesky, eigendecomposition) and what each is for, and conditioning and numerical reality — why the textbook algorithm is not the one your library runs."
---

# Calculus, Geometry and Algebra: Inner Products, the Spectral Theorem and SVD, Factorizations, and Conditioning

> **Part 2 of 6** of the *Calculus, Geometry and Algebra* reference (plugin `calculus-geometry-algebra`), covering §5–§8. Sibling skills: `math-linear-algebra-foundations` (§0–§4), `math-calculus-and-vector-calculus` (§9–§13), `math-forms-optimization-and-differential-equations` (§14–§16), `math-geometry-manifolds-tensors-and-lie-groups` (§17–§21), `math-reference` (§22–§26). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Permanently settled — Newton and Leibniz in the 1670s, Gauss and Cauchy in the 1820s, Grassmann 1844, Riemann 1854, Ricci-Curbastro in the 1890s, Cartan 1899, Eckart-Young 1936.

> **How to read this.** Three connected parts: **linear algebra (§1–§8 → `math-linear-algebra-foundations`)**, **calculus
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

## §5. Inner Products and Orthogonality

**Inner product** `⟨u,v⟩` — gives length `‖v‖ = √⟨v,v⟩` and angle `cos θ = ⟨u,v⟩/(‖u‖‖v‖)`.
⚠️ **Geometry enters linear algebra here and not before. A vector space has no notion of
length or angle until you choose an inner product.**

**Orthonormal bases** are the good ones: ⚠️ **coefficients are just inner products,
`v = Σ⟨v,eᵢ⟩eᵢ`, with no linear system to solve.**
**Gram-Schmidt** constructs them — ⚠️ **and classical Gram-Schmidt is numerically unstable;
use modified Gram-Schmidt or Householder** (§7).

**Projection onto a subspace**: `P = A(AᵀA)⁻¹Aᵀ`.
**⚠️ Least squares is projection.** `Ax = b` with no solution → project `b` onto `C(A)`:
```
Normal equations: AᵀAx̂ = Aᵀb
```
⚠️ **But do not solve the normal equations numerically — forming `AᵀA` squares the
condition number** (§8). **Use QR or SVD.**
**⚠️ The residual is orthogonal to the column space, and that's the entire geometric
content of least squares.**

**Orthogonal matrices** `QᵀQ = I` — ⚠️ **preserve lengths and angles, `det = ±1`, and are
perfectly conditioned. This is why numerical algorithms are built from them.**

---

## §6. Spectral Theorem and SVD

**⚠️ Spectral theorem**: a **real symmetric** matrix has **real eigenvalues** and an
**orthonormal eigenbasis** — `A = QΛQᵀ`. **(Hermitian in the complex case.)**
⚠️ **This is why symmetric matrices are so much better behaved, and why covariance
matrices, Hessians, and Laplacians — all symmetric — are tractable.**
**Positive definite**: all eigenvalues > 0. ⚠️ **Equivalently `xᵀAx > 0` for all `x ≠ 0`,
equivalently it has a Cholesky factorization** (§7).

### 6.1 ⚠️ SVD — the most important factorization
```
A = UΣVᵀ        U (m×m) orthogonal, Σ (m×n) diagonal ≥0, V (n×n) orthogonal
```
> **⚠️ GOTCHA — SVD exists for EVERY matrix.** ⚠️ **Any shape, any rank, real or complex,
> no symmetry or invertibility required.** **Eigendecomposition needs square and often
> fails; SVD never does.** **If you learned eigendecomposition as the fundamental
> factorization, that's backwards — SVD is.**

**⚠️ What it says geometrically**: **every linear map is a rotation, then an axis-aligned
scaling, then another rotation.** That's all any linear map does.

**What it gives you:**
```
Rank             ⚠️ number of nonzero singular values — the RELIABLE rank test
Four subspaces   ⚠️ orthonormal bases for all of §2, directly
Condition number κ = σ_max/σ_min          (§8)
Pseudoinverse    A⁺ = VΣ⁺Uᵀ  ⚠️ solves least squares even for rank-deficient A
‖A‖₂ = σ_max     ‖A‖_F = √(Σσᵢ²)
Best rank-k approximation  ⚠️ Eckart-Young: truncate to the top k singular values.
                 OPTIMAL in both the 2-norm and Frobenius norm
```
**⚠️ Eckart-Young is the theorem behind an enormous amount of practice**: PCA (⚠️ **SVD of
centred data**), low-rank approximation, image compression, latent semantic analysis,
recommender systems, and model compression. **"Take the top k components" is always this
theorem.**

**⚠️ Relation to eigendecomposition**: singular values of `A` are square roots of
eigenvalues of `AᵀA`; **`V` holds its eigenvectors.** ⚠️ **But computing SVD that way
squares the condition number — real algorithms (Golub-Kahan) never form `AᵀA`.**

---

## §7. Matrix Factorizations

| Factorization | Form | ⚠️ Use |
|---|---|---|
| **LU (with pivoting)** | `PA = LU` | ⚠️ **Solving `Ax=b`; the workhorse. `O(n³/3)`** |
| **Cholesky** | `A = LLᵀ` | ⚠️ **Symmetric positive definite; twice as fast as LU** |
| **QR** | `A = QR` | ⚠️ **Least squares, stably. Householder or Givens** |
| **Eigendecomposition** | `A = PDP⁻¹` | Dynamics, powers; ⚠️ may not exist |
| **Schur** | `A = QTQ*` | ⚠️ **Always exists, numerically stable — the practical alternative to Jordan** |
| **SVD** | `A = UΣVᵀ` | ⚠️ **Always exists; everything in §6.1** |
| **Jordan** | `A = PJP⁻¹` | ⚠️ **Theory only — numerically unstable** |

**Iterative methods for large sparse systems**: **Conjugate Gradient** (⚠️ **SPD only, and
Krylov-subspace based**), **GMRES**, **BiCGSTAB**; **Lanczos** and **Arnoldi** for
eigenvalues; ⚠️ **preconditioning is usually what determines whether these converge in
practice, and it matters more than the choice of solver.**
**Randomized SVD** — ⚠️ **for very large low-rank problems, and it works remarkably well.**

---

## §8. Conditioning and Numerical Reality

**Condition number** `κ(A) = σ_max/σ_min` — ⚠️ **how much relative input error is
amplified.**
```
κ ≈ 1        well conditioned
κ ≈ 10ᵏ      ⚠️ expect to lose about k digits of accuracy
κ = ∞        singular
```
**⚠️ Double precision gives ~16 digits, so `κ > 10¹⁶` means no correct digits remain.**

> **⚠️ GOTCHA — conditioning is a property of the PROBLEM; stability is a property of the
> ALGORITHM.** ⚠️ **A backward-stable algorithm on an ill-conditioned problem still gives
> a bad answer, and that is not the algorithm's fault.** **You cannot fix ill-conditioning
> with better code — you must reformulate the problem.**

**⚠️ The specific things not to do**, all of which follow from the above:
- **Don't form `AᵀA`** (§5) — ⚠️ **it squares `κ`.** Use QR or SVD.
- **Don't compute eigenvalues from the characteristic polynomial** — ⚠️ **polynomial roots
  are wildly ill-conditioned (Wilkinson's polynomial).**
- **Don't invert a matrix to solve `Ax = b`** — ⚠️ **solve the system. Inversion is slower
  and less accurate.**
- **Don't test `det = 0`** for singularity (§3 → `math-linear-algebra-foundations`) — use `σ_min` or `κ`.
- **Don't use classical Gram-Schmidt** (§5).
- ⚠️ **Don't subtract nearly equal numbers** — catastrophic cancellation destroys
  significant digits. **This is why the quadratic formula needs a rearranged branch.**

---

# PART II — CALCULUS
