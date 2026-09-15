---
name: math-linear-algebra-foundations
description: "Use when working with linear structure: vector spaces, bases, dimension and linear maps, matrices and the four fundamental subspaces (column space, null space, row space, left null space) and what rank actually means, determinants and their geometric interpretation as signed volume, and eigenvalues, eigenvectors and diagonalization including when a matrix is not diagonalizable. Includes the router for the whole calculus-geometry-algebra reference."
---

# Calculus, Geometry and Algebra: Vector Spaces, Matrices, Determinants, and Eigenvalues

> **Part 1 of 6** of the *Calculus, Geometry and Algebra* reference (plugin `calculus-geometry-algebra`), covering §0–§4. Sibling skills: `math-inner-products-svd-and-numerical-reality` (§5–§8), `math-calculus-and-vector-calculus` (§9–§13), `math-forms-optimization-and-differential-equations` (§14–§16), `math-geometry-manifolds-tensors-and-lie-groups` (§17–§21), `math-reference` (§22–§26). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Permanently settled — Newton and Leibniz in the 1670s, Gauss and Cauchy in the 1820s, Grassmann 1844, Riemann 1854, Ricci-Curbastro in the 1890s, Cartan 1899, Eckart-Young 1936.

> **How to read this.** Three connected parts: **linear algebra (§1–§8 → `math-inner-products-svd-and-numerical-reality`)**, **calculus
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
>    basis-independent facts about the map that the array happens to encode** (§2).
> 3. **⚠️ Green's, Stokes', and the divergence theorem are one theorem.** They're the
>    generalized Stokes theorem `∫_∂M ω = ∫_M dω` in different dimensions. **Learning them
>    as three unrelated formulas is the single biggest missed opportunity in the standard
>    sequence** (§14 → `math-forms-optimization-and-differential-equations`).

---

## §0. Routing

| You want... | Go to |
|---|---|
| **Vector spaces and linear maps** | **§1** |
| **The four fundamental subspaces** | **§2** |
| Determinants | §3 |
| **Eigenvalues and diagonalization** | **§4** |
| Inner products, orthogonality, least squares | §5 → `math-inner-products-svd-and-numerical-reality` |
| **Spectral theorem and SVD** | **§6 → `math-inner-products-svd-and-numerical-reality`** |
| Matrix factorizations | §7 → `math-inner-products-svd-and-numerical-reality` |
| **Conditioning and numerical reality** | **§8 → `math-inner-products-svd-and-numerical-reality`** |
| **The derivative, properly** | **§9 → `math-calculus-and-vector-calculus`** |
| Integration | §10 → `math-calculus-and-vector-calculus` |
| Series and Taylor | §11 → `math-calculus-and-vector-calculus` |
| Multivariable derivatives | §12 → `math-calculus-and-vector-calculus` |
| **Vector calculus** | **§13 → `math-calculus-and-vector-calculus`** |
| **Differential forms** | **§14 → `math-forms-optimization-and-differential-equations`** |
| Constrained optimization | §15 → `math-forms-optimization-and-differential-equations` |
| Differential equations | §16 → `math-forms-optimization-and-differential-equations` |
| Geometry | §17 → `math-geometry-manifolds-tensors-and-lie-groups` |
| Manifolds | §18 → `math-geometry-manifolds-tensors-and-lie-groups` |
| **Tensors** | **§19 → `math-geometry-manifolds-tensors-and-lie-groups`** |
| Riemannian geometry | §20 → `math-geometry-manifolds-tensors-and-lie-groups` |
| Lie groups and algebras | §21 → `math-geometry-manifolds-tensors-and-lie-groups` |
| **Misconceptions** | **§22 → `math-reference`** |
| Formulas | §23 → `math-reference` |
| Books | §24 → `math-reference` |
| Quick reference | §25 → `math-reference` |

---

# PART I — LINEAR ALGEBRA

---

## §1. Vector Spaces and Linear Maps

**A vector space over a field**: closed under addition and scalar multiplication, with the
usual axioms. ⚠️ **"Vector" means "element of a vector space" — functions, polynomials,
matrices and random variables are all vectors, and treating them that way is the point of
the abstraction.**

**Span, linear independence, basis, dimension.** ⚠️ **Every vector space has a basis, and
all bases have the same cardinality — that's what makes dimension well defined.**

**Linear map**: `T(αu + βv) = αT(u) + βT(v)`.
> **⚠️ GOTCHA — a matrix is not a linear map; it's a *representation* of one in a chosen
> basis.** ⚠️ **Change the basis and the matrix changes while the map does not.**
> **Similar matrices `B = P⁻¹AP` represent the same map in different bases** — which is
> why they share eigenvalues, determinant, trace and rank. **Those are properties of the
> map; the entries are not.**

**Kernel** (null space) and **image** (range).
**⚠️ Rank-nullity**: `dim(ker T) + dim(im T) = dim(domain)`. **The single most used
theorem in the subject** — it's conservation of dimension.

---

## §2. Matrices and the Four Fundamental Subspaces

**⚠️ Strang's framing, and it organizes everything:** for `A: ℝⁿ → ℝᵐ`,
```
Column space  C(A)   ⊆ ℝᵐ   dim = r          ⚠️ where Ax can land
Null space    N(A)   ⊆ ℝⁿ   dim = n − r      ⚠️ what A destroys
Row space     C(Aᵀ)  ⊆ ℝⁿ   dim = r
Left null     N(Aᵀ)  ⊆ ℝᵐ   dim = m − r
```
**⚠️ The orthogonality relations are the content**: **row space ⊥ null space in ℝⁿ**, and
**column space ⊥ left null space in ℝᵐ.** ⚠️ **Each pair decomposes its whole space.**
**`Ax = b` is solvable exactly when `b ∈ C(A)`, and the solution set is a particular
solution plus `N(A)`.**

**Rank** — ⚠️ **row rank equals column rank, which is not obvious and is the reason the
picture above is symmetric.**
**Matrix multiplication is composition of maps** — ⚠️ **which is why it's associative and
not commutative, and both facts stop being surprising once you see it.**

---

## §3. Determinants

**⚠️ The definition to hold in your head: `det A` is the signed volume scaling factor of
the linear map.** A unit cube maps to a parallelepiped of volume `|det A|`; the sign
records orientation.
```
det A = 0        ⚠️ the map collapses dimension — not invertible
det(AB) = det(A)det(B)      ⚠️ scalings compose
det(Aᵀ) = det(A)      det(A⁻¹) = 1/det(A)
```
**⚠️ Practical warning**: **determinants are almost never the right computational tool.**
**Cramer's rule is `O(n!)` naively and numerically terrible; use LU. Testing `det = 0` for
singularity is unreliable — use the condition number or the smallest singular value**
(§8 → `math-inner-products-svd-and-numerical-reality`). **The determinant is conceptually central and computationally marginal.**

**⚠️ Where it genuinely matters**: the **Jacobian determinant** in change of variables
(§10 → `math-calculus-and-vector-calculus`, §12 → `math-calculus-and-vector-calculus`) — because that's exactly the local volume scaling.

---

## §4. Eigenvalues and Diagonalization

`Av = λv` — ⚠️ **directions the map only stretches, without rotating.**
**Characteristic polynomial** `det(A − λI) = 0` — ⚠️ **fine for `2×2` by hand, and a
numerically catastrophic way to compute eigenvalues** (§8 → `math-inner-products-svd-and-numerical-reality`).

**Diagonalization** `A = PDP⁻¹` when there are `n` independent eigenvectors.
⚠️ **Then `Aᵏ = PDᵏP⁻¹`, which is why eigendecomposition makes iteration and matrix
exponentials tractable.**
> **⚠️ GOTCHA — not every matrix is diagonalizable.** ⚠️ **`[[1,1],[0,1]]` has one
> eigenvalue (1) with algebraic multiplicity 2 and geometric multiplicity 1.** **When
> geometric multiplicity is less than algebraic, the matrix is *defective* and you need
> the Jordan form.** ⚠️ **But Jordan form is numerically unstable — an arbitrarily small
> perturbation makes a defective matrix diagonalizable — so it's a theoretical tool, not
> a computational one. Use the Schur decomposition in practice** (§7 → `math-inner-products-svd-and-numerical-reality`).

**Trace = sum of eigenvalues; determinant = product.** ⚠️ **Both are basis-independent,
which is the §1 gotcha showing up again.**
**Cayley-Hamilton**: every matrix satisfies its own characteristic polynomial.
