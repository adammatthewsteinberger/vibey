---
name: math-geometry-manifolds-tensors-and-lie-groups
description: "Use when working in curved or structured spaces: geometry including projective and affine settings, manifolds and charts, tensors done properly rather than as multidimensional arrays, Riemannian geometry with metrics, connections, geodesics and curvature, and Lie groups and Lie algebras including the rotation groups that show up in robotics, graphics and physics."
---

# Calculus, Geometry and Algebra: Geometry, Manifolds, Tensors, Riemannian Geometry, and Lie Groups

> **Part 5 of 6** of the *Calculus, Geometry and Algebra* reference (plugin `calculus-geometry-algebra`), covering §17–§21. Sibling skills: `math-linear-algebra-foundations` (§0–§4), `math-inner-products-svd-and-numerical-reality` (§5–§8), `math-calculus-and-vector-calculus` (§9–§13), `math-forms-optimization-and-differential-equations` (§14–§16), `math-reference` (§22–§26). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Permanently settled — Newton and Leibniz in the 1670s, Gauss and Cauchy in the 1820s, Grassmann 1844, Riemann 1854, Ricci-Curbastro in the 1890s, Cartan 1899, Eckart-Young 1936.

> **How to read this.** Three connected parts: **linear algebra (§1–§8 → `math-linear-algebra-foundations`, `math-inner-products-svd-and-numerical-reality`)**, **calculus
> (§9–§16 → `math-calculus-and-vector-calculus`, `math-forms-optimization-and-differential-equations`)**, **geometry and tensors (§17–§21)**. ⚠️ **They are far more connected than
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

## §17. Geometry

**Euclidean** — distances and angles; **isometries** are rotations, reflections,
translations.
**Affine** — ⚠️ **no origin, no distances; parallelism and ratios along lines survive.**
**Convexity** lives here.
**Projective** — ⚠️ **add points at infinity; parallel lines meet.** **Homogeneous
coordinates make projection linear**, which is why they run all of computer graphics and
computer vision. **The cross-ratio is the projective invariant.**
**Non-Euclidean** — spherical (positive curvature, no parallels) and hyperbolic (negative,
infinitely many). ⚠️ **Their consistency showed the parallel postulate is independent, not
derivable — a foundational moment in mathematics.**

**⚠️ Klein's Erlangen program is the organizing idea**: **a geometry is the study of what
is invariant under a group of transformations.** ⚠️ **Which geometry you're doing is
determined by which group you allow**, and that reframing connects §17 to §21.

---

## §18. Manifolds

**⚠️ A space that looks locally like `ℝⁿ`** — charts, atlases, transition maps.
**Smooth manifold**: transition maps are smooth.
**Tangent space `T_pM`** — ⚠️ **the vector space of directions at a point.** **Formally
defined via derivations or equivalence classes of curves, precisely because you cannot
subtract points on a curved space.**
> **⚠️ GOTCHA — you cannot compare vectors at different points on a manifold.** ⚠️ **There
> is no canonical way to say a vector here "equals" a vector there.** **Fixing this
> requires a connection**, and **the failure of parallel transport around a closed loop
> to return the original vector is exactly curvature** (§20). **This is the conceptual
> core of differential geometry.**

**Vector fields**, **cotangent space** `T*_pM` (⚠️ **the dual — where 1-forms live, and
where gradients actually live**), **tensor and exterior bundles**, **flows and Lie
brackets**.

---

## §19. Tensors — Done Properly

**⚠️ Three definitions circulate, they are not equivalent, and the confusion is the single
most common problem in this area.**

```
1. ⚠️ "A multidimensional array"          — ML/programming usage
2. ⚠️ "An object transforming by a law"    — physics/engineering usage
3. ⚠️ "A multilinear map"                  — mathematics usage
```
> **⚠️ GOTCHA — a PyTorch tensor is generally NOT a tensor in the mathematical sense.**
> ⚠️ **It's an n-dimensional array — a data structure.** **A tensor in senses 2 and 3 is a
> basis-independent geometric object that *has* components in a basis, and those
> components must transform correctly under change of basis.**
> **The array is the shadow; the tensor is the object.** ⚠️ **This is exactly §1 → `math-linear-algebra-foundations`'s
> matrix-vs-linear-map distinction, one level up.** **Neither usage is wrong — but
> conflating them produces real errors when you start changing coordinates.**

**Definition 3 is the cleanest**: a **`(p,q)`-tensor** is a multilinear map taking `p`
covectors and `q` vectors to a scalar. `T: (V*)^p × V^q → ℝ`.

**Transformation law (definition 2)** — under a change of basis, ⚠️ **contravariant
(upper) indices transform with the Jacobian, covariant (lower) indices with its
inverse.** **That opposition is what makes contractions basis-independent.**
```
Vector (contravariant)      vⁱ       ⚠️ upper index
Covector/1-form (covariant) ωᵢ       ⚠️ lower index
Metric                      g_{ij}   ⚠️ (0,2) — lowers indices
Inverse metric              g^{ij}   raises them
```
**⚠️ Einstein summation**: repeated upper-lower index pairs are summed. **`vⁱωᵢ` is a
scalar.**
**Operations**: **outer product** (raises rank), **contraction** (⚠️ **lowers rank by 2;
trace is a contraction**), **raising and lowering with the metric** (⚠️ **which is why the
vector/covector distinction is invisible in Euclidean space with an orthonormal basis —
`g = I`, so components coincide, and that's precisely why the distinction is never taught
in introductory courses and then causes trouble later**).

**Examples**: **stress tensor** (rank 2), **metric tensor** (rank 2), **Riemann curvature**
(rank 4), **moment of inertia** (rank 2 — ⚠️ **and the reason `L` and `ω` need not be
parallel; see a Newtonian-mechanics reference §7**), **electromagnetic field tensor**.

**⚠️ Tensor decompositions** (a genuinely different topic that shares the name): **CP/PARAFAC**,
**Tucker**, **tensor trains**. ⚠️ **Here "tensor" means definition 1, and the SVD analogy is
imperfect — for order ≥ 3, best rank-k approximation may not exist, and computing tensor
rank is NP-hard.** **Do not assume §6.1 → `math-inner-products-svd-and-numerical-reality`'s guarantees carry over.**

---

## §20. Riemannian Geometry

**Metric tensor `g`** — ⚠️ **an inner product on each tangent space, varying smoothly.**
**It gives lengths, angles, volumes, and geodesics.**
**Connection / covariant derivative `∇`** — ⚠️ **how to differentiate vector fields, i.e.
how to compare tangent spaces (§18).** **The Levi-Civita connection is the unique
torsion-free, metric-compatible one, with Christoffel symbols `Γᵏᵢⱼ` built from
derivatives of `g`.**
⚠️ **Christoffel symbols are NOT tensors** — they don't transform correctly, which is
exactly why they can be made to vanish at a point (normal coordinates).

**Geodesics** — ⚠️ **straightest possible paths, `∇_γ̇ γ̇ = 0`; locally length-minimizing.**
**Curvature**: **Riemann tensor `R^ρ_{σμν}`** (⚠️ **measures failure of parallel transport
around an infinitesimal loop to return the original vector — the §18 gotcha made
quantitative**), **Ricci `R_{μν}`** (a contraction), **scalar `R`**, **sectional**, and
**Gaussian** curvature.
**⚠️ Gauss's Theorema Egregium**: **Gaussian curvature is intrinsic** — ⚠️ **measurable
from inside the surface without reference to any embedding.** **This is why a flat map of
the sphere must distort, and why the result is called "remarkable."**
**⚠️ Gauss-Bonnet** links total curvature to the Euler characteristic — **geometry
constrained by topology.**

---

## §21. Lie Groups and Algebras

**⚠️ A group that is also a smooth manifold — continuous symmetry made differentiable.**
```
SO(3)  rotations in 3D           SU(2)  ⚠️ double covers SO(3) — the quaternion connection
SE(3)  rigid motions             ⚠️ the configuration space of robotics and pose estimation
GL(n)  invertible matrices       SL(n)  determinant 1
```
**Lie algebra `𝔤`** — ⚠️ **the tangent space at the identity, with the Lie bracket.**
**`exp: 𝔤 → G`** maps it back to the group.
**⚠️ Why this matters practically**: **the group is curved and constrained; the algebra is
a vector space.** ⚠️ **Optimization, interpolation and uncertainty are done in the algebra
and mapped back** — **which is exactly why SLAM, robotics and pose estimation use
`se(3)`/`so(3)` rather than optimizing over rotation matrices directly** (see robotics and
computer-vision references).
**⚠️ And Noether's theorem lives here**: continuous symmetries yield conservation laws
(see a Newtonian-mechanics reference §4.5).
