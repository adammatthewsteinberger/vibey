---
name: ml-framing-data-and-classical
description: "Use when starting or scoping an ML project: when not to use ML, framing the problem properly (target, metric, baseline, cost of errors), data splitting and the leakage that follows from getting it wrong, the data problems you'll actually hit (labels, drift, imbalance, duplicates), and the classical toolkit — gradient boosting as the tabular default (XGBoost, LightGBM, CatBoost), linear models, clustering, and the rest of scikit-learn. Includes the router for the whole machine-learning reference."
---

# Machine Learning: Framing, Data, and the Classical Toolkit

> **Part 1 of 4** of the *Machine Learning* reference (plugin `machine-learning`), covering §0–§3. Sibling skills: `ml-deep-learning-and-training` (§4–§8), `ml-evaluation-serving-mlops-and-safety` (§9–§14), `ml-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 → `ml-reference` for the currency snapshot and what goes stale first.

> **How to read this.** Reference, not tutorial. Sections are independent. Three markers:
> - **[DURABLE]** — statistics, optimization theory, or a lesson the field has relearned
>   every few years. Does not expire.
> - **[VERSIONED]** — framework versions, hardware, library APIs. Moving fast; verify.
> - **[CONTESTED]** — practitioners genuinely disagree.
>
> **⚠️ GOTCHA** boxes mark the mistakes that produce a model that looks great offline and
> fails in production — which is the characteristic failure of this field.
>
> **The three framings that organize everything below:**
> 1. **Your data is the model.** Architecture choices matter far less than data quality,
>    quantity, and whether your evaluation measures the thing you care about. Most time on
>    a real project goes to data, and most catastrophic failures originate there (§2).
> 2. **The default failure mode is a number that lies.** Leakage, distribution shift, a
>    metric that doesn't match the objective, a test set you tuned against. **A model that
>    looks too good almost always is** — and finding out why is the core skill.
> 3. **Almost everything you'll build should not be a neural network.** For tabular data —
>    which is most business data — gradient-boosted trees remain the strongest default
>    (§3.1). Reach for deep learning when you have perceptual data, sequences, very large
>    datasets, or a pretrained model to adapt.

---

## §0. Routing

### 0.1 The question router

| Asked about... | Go to |
|---|---|
| Should I use ML at all; framing the problem | §1 |
| Data: splits, leakage, imbalance, labels | §2 |
| Classical ML: boosting, linear models, clustering | §3 |
| Deep learning fundamentals | §4 → `ml-deep-learning-and-training` |
| Architectures: transformers, CNNs, diffusion | §5 → `ml-deep-learning-and-training` |
| PyTorch, JAX, the ecosystem, torch.compile | §6 → `ml-deep-learning-and-training` |
| Training at scale: DDP, FSDP, parallelism, precision | §7 → `ml-deep-learning-and-training` |
| Fine-tuning, PEFT/LoRA, post-training | §8 → `ml-deep-learning-and-training` |
| Evaluation and metrics | §9 → `ml-evaluation-serving-mlops-and-safety` |
| Debugging training | §10 → `ml-evaluation-serving-mlops-and-safety` |
| Inference, serving, quantization | §11 → `ml-evaluation-serving-mlops-and-safety` |
| MLOps, reproducibility, monitoring | §12 → `ml-evaluation-serving-mlops-and-safety` |
| Hardware and cost | §13 → `ml-evaluation-serving-mlops-and-safety` |
| Interpretability, fairness, safety | §14 → `ml-evaluation-serving-mlops-and-safety` |
| "Don't do this" | §15 → `ml-reference` |
| "Which approach is better?" | §16 → `ml-reference` (contested) |
| "Is this still current?" | §17 → `ml-reference` |
| Books, courses, people | §18 → `ml-reference` |

---

## §1. Framing

### 1.1 When not to use ML

**[DURABLE] The most valuable ML judgment is recognizing the problems that don't need it.**
Don't use ML when:
- **Rules work.** If the logic is expressible in a hundred lines of `if` statements, write
  them. They're debuggable, auditable, and don't drift.
- **You don't have data**, or you can't get labels at reasonable cost.
- **You can't tolerate being wrong** and there's no fallback path.
- **The relationship you're modeling doesn't exist.** ML finds patterns; it also
  hallucinates them from noise.
- **You need a causal answer** and only have observational data. **⚠️ Prediction ≠ causation
  is the most expensive confusion in applied ML** — a model that predicts churn well tells
  you nothing about what intervention reduces churn.
- **Requirements change faster than you can retrain.**

### 1.2 Framing the problem properly

```
business objective  →  ML task  →  metric  →  data  →  baseline  →  model
       ↑                                                              |
       └──────────────── does the metric actually move it? ───────────┘
```

**[DURABLE] Always build the dumb baseline first**: predict the majority class, predict the
mean, use last week's value, use a linear model, use the existing heuristic. **If your
neural network doesn't beat the baseline by a margin that matters, you've learned
something important and cheap.** A shocking number of published and deployed models don't.

**Frame the task honestly**: supervised (classification, regression, ranking), unsupervised
(clustering, dimensionality reduction, density estimation), self-supervised (the pretraining
paradigm), reinforcement learning (⚠️ expensive, sample-hungry, hard to debug — often the
wrong tool for a problem that could be supervised), or **not-ML** (§1.1).

**Define the deployment constraint before you model**: latency budget, throughput,
memory, cost per prediction, retraining cadence, explainability requirement, and what
happens when the model is wrong. **⚠️ A model that can't meet the latency budget is a
research artifact**, and finding that out at the end is a common and avoidable waste.

---

## §2. Data

**[DURABLE] This is where the time goes and where the failures come from.**

### 2.1 Splitting — and the leakage that follows from getting it wrong

```
train  →  fit parameters
val    →  select hyperparameters, early stopping, model selection
test   →  ONE final estimate. Touch it once.
```

> **⚠️ GOTCHA — data leakage is the #1 cause of models that look great and fail.** The
> forms, roughly in order of how often they bite:
> 1. **Preprocessing before splitting.** Fitting a scaler, imputer, encoder, or feature
>    selector on the full dataset leaks test statistics into training. **Fit on train,
>    transform everything.** Use a `Pipeline` so this is structurally impossible.
> 2. **Temporal leakage.** Random-splitting time-series data lets the model see the future.
>    **Split by time, always, for anything with a time dimension.**
> 3. **Group leakage.** The same patient / user / document in both train and test.
>    **Use grouped splits.**
> 4. **Target leakage in features.** A feature computed from or after the outcome —
>    "number_of_support_tickets" predicting churn when the tickets came after the cancel
>    decision. **The classic tell: a feature with suspiciously high importance.**
> 5. **Duplicate or near-duplicate rows** spanning the split.
> 6. **Tuning against the test set** across many experiments. This is slow-motion leakage
>    and it's endemic.
>
> **The diagnostic: if your model is much better than you expected, look for leakage
> before you celebrate.** That instinct is worth more than any technique in this document.

**Cross-validation** when data is scarce: k-fold, stratified k-fold (preserve class
balance), **grouped** k-fold, and **time-series split** (expanding or rolling window,
never shuffled). **Nested CV** when you're both tuning and estimating performance — most
people skip it and consequently report optimistic numbers.

### 2.2 The data problems you'll actually hit

- **Class imbalance** — resampling (SMOTE and friends: ⚠️ often overrated, and it must
  happen *inside* the CV fold), class weights, threshold tuning (usually the best answer),
  and **metrics that aren't accuracy** (§9.1 → `ml-evaluation-serving-mlops-and-safety`).
- **Missing data** — is it MCAR, MAR, or MNAR? **Missingness is often itself a signal**;
  add an indicator column. Note that gradient-boosting libraries handle missing values
  natively and well, which is one of several practical reasons they win on tabular data.
- **Label noise** — usually a bigger accuracy ceiling than your model choice. Audit labels;
  measure inter-annotator agreement; **the noise floor is your real ceiling**.
- **Distribution shift** — covariate shift (inputs change), label shift, concept drift
  (the relationship itself changes). **[DURABLE] This is the main reason deployed models
  degrade**, and it's why §12.3 → `ml-evaluation-serving-mlops-and-safety` exists.
- **Feature engineering** still matters enormously outside deep learning. For tabular
  problems, good features beat model choice **almost every time**.

---

## §3. The Classical Toolkit

### 3.1 Gradient boosting — still the tabular default

**[DURABLE, and it's the most useful practical fact in this document.]** For structured /
tabular data, **gradient-boosted decision trees remain the strongest default**, and this
has survived a decade of attempts to unseat them. The evidence is consistent across
independent benchmarks: Shwartz-Ziv & Armon ("Tabular Data: Deep Learning Is Not All You
Need") found deep models weaker than XGBoost, and that deep models only beat XGBoost when
*ensembled with* it; Grinsztajn et al. ("Why do tree-based models still outperform deep
learning on tabular data?") found the same across many datasets.

**Why trees win here [DURABLE]**: tabular features have no spatial or sequential structure
to exploit, they're heterogeneous in scale and type, trees handle missing values and
categoricals natively, they're robust to uninformative features, they need far less tuning,
and they train fast on CPU. The honest counterweight from the same literature: **trees
generalize less well to diverse unseen data and are less robust to distribution shift than
deep models**, and well-regularized MLPs beat GBDTs in some studies (Kadra et al.) — so
the literature genuinely conflicts at the margins.

**[VERSIONED] The three libraries**: **XGBoost** (mature categorical support,
terabyte-scale external-memory training), **LightGBM** (leaf-wise growth, histogram-based
splits — fastest and most memory-efficient on large data), and **CatBoost** (best
out-of-the-box performance, especially with categorical-heavy data, via ordered target
encoding). Scikit-learn's **HistGradientBoosting** has been identified in comparative work
as **the most stable across datasets** with good performance and computational efficiency.

**⚠️ The performance gap between the three has narrowed to the point of near-irrelevance.
Feature engineering and proper tuning matter far more than which one you pick.** Start with
whichever you know; switch only for a specific reason (huge data → LightGBM; heavy
categoricals → CatBoost).

### 3.2 The rest of the classical toolkit

**Linear/logistic regression** — still the right answer surprisingly often. Interpretable,
fast, well-calibrated, and an honest baseline. **Regularization**: L2 (ridge — shrinks),
L1 (lasso — sparsifies and selects), elastic net.
**Random forests** — lower ceiling than boosting but nearly tuning-free and hard to
overfit; a good sanity check.
**SVMs** — largely superseded, still fine on small high-dimensional data.
**k-NN** — a genuinely useful baseline, and the conceptual core of retrieval and embeddings.
**Clustering** — k-means (⚠️ assumes spherical, equal-variance clusters; choosing k is not
a solved problem), DBSCAN/HDBSCAN (density-based, finds arbitrary shapes, handles noise),
hierarchical, Gaussian mixtures.
**Dimensionality reduction** — PCA (linear, fast, interpretable variance), UMAP and t-SNE
for **visualization only**. **⚠️ Never interpret distances or cluster sizes in a t-SNE or
UMAP plot as meaningful** — this is one of the most common misreadings in applied ML.
**Calibration** — Platt scaling, isotonic regression. **[DURABLE] If your downstream
decision uses the probability rather than the argmax, you must calibrate**, and most people
don't. Boosted trees and neural nets are both typically miscalibrated out of the box.
